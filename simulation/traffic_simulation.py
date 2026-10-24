#!/usr/bin/env python3
"""Illustrative one-cell traffic simulation. Assumptions are in configs/traffic_scenario.json."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

from audit import airtime_ms

ROOT = Path(__file__).resolve().parents[1]


def poisson(rng: random.Random, mean: float) -> int:
    """Knuth Poisson sampler; per-pole, per-window means are modest in this scenario."""
    limit = math.exp(-mean)
    product = 1.0
    count = 0
    while product > limit:
        count += 1
        product *= rng.random()
    return count - 1


def collision_rate(packets: list[tuple[float, float, int]], channels: int,
                   duration_seconds: int) -> tuple[int, float]:
    """Count packets involved in any same-channel overlap and compute G per channel."""
    per_channel: dict[int, list[tuple[float, float, int]]] = defaultdict(list)
    total_airtime = 0.0
    for packet_id, (start, duration, channel) in enumerate(packets):
        end = start + duration
        per_channel[channel].append((start, end, packet_id))
        total_airtime += duration
    collided: set[int] = set()
    for channel_rows in per_channel.values():
        channel_rows.sort(key=lambda row: row[0])
        active: list[tuple[float, int]] = []
        for start, end, packet_id in channel_rows:
            active = [(active_end, active_id) for active_end, active_id in active if active_end > start]
            for _, active_id in active:
                collided.add(packet_id)
                collided.add(active_id)
            active.append((end, packet_id))
    offered_load = total_airtime / (channels * duration_seconds)
    return len(collided), offered_load


def packet_airtime(cfg: dict, phy_payload_bytes: int) -> float:
    return airtime_ms(phy_payload_bytes, cfg["spreading_factor"], cfg["bandwidth_hz"],
                      cfg["coding_rate_index"], cfg["preamble_symbols"]) / 1000


def packets_baseline(cfg: dict, rng: random.Random) -> list[tuple[float, float, int]]:
    duration = cfg["duration_seconds"]
    tags, poles, passage = cfg["active_tags"], cfg["poles_in_cell"], cfg["mean_tag_passage_seconds"]
    event_rate = tags / passage
    arrival_airtime = packet_airtime(cfg, cfg["lora_mac_phy_overhead_bytes"] + cfg["bytes_per_arrival_record"])
    heartbeat_payload = cfg["lora_mac_phy_overhead_bytes"] + cfg["baseline_heartbeat_ids_per_pole"] * 4
    heartbeat_airtime = packet_airtime(cfg, heartbeat_payload)
    packets: list[tuple[float, float, int]] = []
    t = 0.0
    while True:
        t += rng.expovariate(event_rate)
        if t >= duration:
            break
        packets.append((t, arrival_airtime, rng.randrange(cfg["channels"])))
    for _pole in range(poles):
        t = rng.random() * cfg["heartbeat_interval_seconds"]
        while t < duration:
            packets.append((t, heartbeat_airtime, rng.randrange(cfg["channels"])))
            t += cfg["heartbeat_interval_seconds"]
    return packets


def packets_batched(cfg: dict, rng: random.Random) -> list[tuple[float, float, int]]:
    duration = cfg["duration_seconds"]
    tags, poles, passage = cfg["active_tags"], cfg["poles_in_cell"], cfg["mean_tag_passage_seconds"]
    interval = cfg["arrival_batch_interval_seconds"]
    jitter_min = float(cfg.get("batch_jitter_min_seconds", 0.2))
    jitter_max = float(cfg.get("batch_jitter_max_seconds", 1.5))
    if not 0 <= jitter_min <= jitter_max <= interval:
        raise ValueError("batch jitter must satisfy 0 <= min <= max <= batch interval")
    mean_events_per_pole = tags / passage * interval / poles
    packets: list[tuple[float, float, int]] = []
    for bucket_start in range(0, duration, interval):
        for _pole in range(poles):
            event_count = poisson(rng, mean_events_per_pole)
            while event_count > 0:
                records = min(event_count, cfg["max_tag_records_per_batch"])
                phy_bytes = cfg["lora_mac_phy_overhead_bytes"] + records * cfg["bytes_per_arrival_record"]
                start = bucket_start + rng.uniform(jitter_min, jitter_max)
                packets.append((start, packet_airtime(cfg, phy_bytes), rng.randrange(cfg["channels"])))
                event_count -= records
    heartbeat_bytes = cfg["lora_mac_phy_overhead_bytes"] + cfg["bloom_heartbeat_application_bytes"]
    heartbeat_airtime = packet_airtime(cfg, heartbeat_bytes)
    for _pole in range(poles):
        t = rng.random() * cfg["heartbeat_interval_seconds"]
        while t < duration:
            packets.append((t, heartbeat_airtime, rng.randrange(cfg["channels"])))
            t += cfg["heartbeat_interval_seconds"]
    return packets


def summarize(name: str, packets: list[tuple[float, float, int]], channels: int,
              duration: int) -> list[object]:
    collided, load = collision_rate(packets, channels, duration)
    loss = collided / len(packets) if packets else 0.0
    poisson_loss = 1 - math.exp(-2 * load)
    return [name, len(packets), f"{load:.6f}", collided, f"{loss:.6f}",
            f"{poisson_loss:.6f}", f"{1-loss:.6f}", duration,
            "fixed-seed synthetic events; not measured traffic"]


def percentile(values: list[float], fraction: float) -> float:
    """Linearly interpolated empirical percentile, with no third-party dependency."""
    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0.0 <= fraction <= 1.0:
        raise ValueError("fraction must be between 0 and 1")
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def summarize_replications(name: str, runs: list[list[object]],
                           duration: int) -> list[object]:
    """Summarize run-to-run variability; percentiles are not parameter CIs."""
    losses = [float(row[4]) for row in runs]
    metrics = [[int(row[1]), float(row[2]), int(row[3]), float(row[5]), float(row[6])]
               for row in runs]
    n = len(runs)
    return [name,
            f"{statistics.mean(row[0] for row in metrics):.2f}",
            f"{statistics.mean(row[1] for row in metrics):.8f}",
            f"{statistics.mean(row[2] for row in metrics):.2f}",
            f"{statistics.mean(losses):.8f}",
            f"{statistics.mean(row[3] for row in metrics):.8f}",
            f"{statistics.mean(row[4] for row in metrics):.8f}",
            duration,
            "synthetic workload; no field measurements",
            n,
            f"{statistics.stdev(losses) if n > 1 else 0.0:.8f}",
            f"{percentile(losses, 0.025):.8f}",
            f"{percentile(losses, 0.975):.8f}"]


def write_figure(path: Path, rows: list[list[object]]) -> None:
    labels = ["Single-event + raw IDs", "15 s batches + Bloom"]
    colors = ["#91a0b9", "#58d6c5"]
    width, height = 1000, 570
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">',
             '<rect width="100%" height="100%" fill="#0b1120"/>',
             '<style>text{font-family:Inter,Segoe UI,Arial,sans-serif}.title{fill:#f4f7fb;font-size:25px;font-weight:700}.sub{fill:#9eacc3;font-size:14px}.label{fill:#d7e2f2;font-size:13px}.grid{stroke:#26344b}</style>',
             '<text x="70" y="48" class="title">Batching reduces packets, but timing can dominate collisions</text>',
             f'<text x="70" y="75" class="sub">{int(rows[0][9])} deterministic seeds; one-hour synthetic workload; 3,000 tags, 60 poles, 8 channels</text>']
    panels = [(70, "Offered load per channel (G)", [float(row[2]) for row in rows], 0.5, [0, .1, .2, .3, .4, .5], False),
              (550, "Packet loss in event simulation", [float(row[4]) for row in rows], 1.0, [0, .2, .4, .6, .8, 1.0], True)]
    for x0, title, vals, ymax, ticks, compare_poisson in panels:
        plot_x, plot_y, plot_w, plot_h = x0 + 45, 145, 350, 300
        parts.append(f'<text x="{x0+10}" y="118" fill="#c4d2e5" font-size="16" font-weight="700">{title}</text>')
        for tick in ticks:
            y = plot_y + (1 - tick / ymax) * plot_h
            parts += [f'<line x1="{plot_x}" y1="{y:.1f}" x2="{plot_x+plot_w}" y2="{y:.1f}" class="grid"/>',
                      f'<text x="{plot_x-10}" y="{y+4:.1f}" text-anchor="end" class="sub">{tick*100:.0f}%</text>']
        for i, value in enumerate(vals):
            bar_x = plot_x + 50 + i * 155
            bar_h = min(value / ymax, 1) * plot_h
            bar_y = plot_y + plot_h - bar_h
            parts += [f'<rect x="{bar_x}" y="{bar_y:.1f}" width="78" height="{bar_h:.1f}" rx="8" fill="{colors[i]}"/>',
                      f'<text x="{bar_x+39}" y="{bar_y-9:.1f}" text-anchor="middle" fill="#f4f7fb" font-size="14">{value*100:.1f}%</text>',
                      f'<text x="{bar_x+39}" y="{plot_y+plot_h+24}" text-anchor="middle" class="label">{labels[i]}</text>']
            if compare_poisson:
                estimate = float(rows[i][5])
                estimate_y = plot_y + (1 - estimate / ymax) * plot_h
                parts.append(f'<line x1="{bar_x-7}" y1="{estimate_y:.1f}" x2="{bar_x+85}" y2="{estimate_y:.1f}" stroke="#ffbf69" stroke-width="3" stroke-dasharray="6 4"/>')
                parts.append(f'<text x="{bar_x+39}" y="{estimate_y+17:.1f}" text-anchor="middle" fill="#ffcf8b" font-size="11">Poisson from G: {estimate*100:.1f}%</text>')
                low_y = plot_y + (1 - float(rows[i][11]) / ymax) * plot_h
                high_y = plot_y + (1 - float(rows[i][12]) / ymax) * plot_h
                mid_x = bar_x + 39
                parts += [f'<line x1="{mid_x}" y1="{high_y:.1f}" x2="{mid_x}" y2="{low_y:.1f}" stroke="#f4f7fb" stroke-width="2"/>',
                          f'<line x1="{mid_x-6}" y1="{high_y:.1f}" x2="{mid_x+6}" y2="{high_y:.1f}" stroke="#f4f7fb" stroke-width="2"/>',
                          f'<line x1="{mid_x-6}" y1="{low_y:.1f}" x2="{mid_x+6}" y2="{low_y:.1f}" stroke="#f4f7fb" stroke-width="2"/>']
        parts.append(f'<line x1="{plot_x}" y1="{plot_y}" x2="{plot_x}" y2="{plot_y+plot_h}" stroke="#61718b"/>')
        parts.append(f'<line x1="{plot_x}" y1="{plot_y+plot_h}" x2="{plot_x+plot_w}" y2="{plot_y+plot_h}" stroke="#61718b"/>')
    parts.append('<text x="70" y="505" fill="#9eacc3" font-size="12">Bars show the mean; whiskers span the 2.5th–97.5th percentiles across seeded runs. This is run variability under assumed inputs, not parameter uncertainty.</text>')
    parts.append('<text x="70" y="525" fill="#9eacc3" font-size="12">Gold dashed marks show 1−exp(−2G). Periodic batches violate the Poisson premise; the gap is a schedule-sensitivity warning, not a deployment prediction.</text>')
    parts.append('</svg>')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    cfg = json.loads((ROOT / "configs" / "traffic_scenario.json").read_text(encoding="utf-8"))
    replications = int(cfg.get("replications", 1))
    if replications < 1:
        raise ValueError("replications must be at least 1")
    run_records: dict[str, list[list[object]]] = {
        "Single arrival + raw per-pole ID heartbeat": [],
        "15 s chunks + 64 B per-pole Bloom heartbeat": [],
    }
    replication_rows: list[list[object]] = []
    for replication in range(replications):
        # Separate deterministic streams keep the two workload generators from
        # depending on how many random values the other scenario consumes.
        for scenario_index, (name, generator) in enumerate((
            ("Single arrival + raw per-pole ID heartbeat", packets_baseline),
            ("15 s chunks + 64 B per-pole Bloom heartbeat", packets_batched),
        )):
            run_seed = cfg["seed"] + replication * 2 + scenario_index
            packets = generator(cfg, random.Random(run_seed))
            row = summarize(name, packets, cfg["channels"], cfg["duration_seconds"])
            run_records[name].append(row)
            replication_rows.append([name, replication + 1, run_seed, *row[1:]])
    out = args.output_dir.resolve() / "results"
    out.mkdir(parents=True, exist_ok=True)
    rows = [summarize_replications(name, runs, cfg["duration_seconds"])
            for name, runs in run_records.items()]
    with (out / "illustrative_traffic_simulation.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["scenario", "mean_packets_per_run", "mean_offered_load_per_channel", "mean_packets_involved_in_collision", "mean_simulated_packet_loss", "mean_poisson_loss_from_mean_load", "mean_simulated_pdr", "duration_seconds", "status", "replications", "run_loss_standard_deviation", "run_loss_p2_5", "run_loss_p97_5"])
        writer.writerows(rows)
    with (out / "illustrative_traffic_replications.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["scenario", "replication", "seed", "packets", "offered_load_per_channel", "packets_involved_in_collision", "simulated_packet_loss", "poisson_loss_from_mean_load", "simulated_pdr", "duration_seconds", "status"])
        writer.writerows(replication_rows)
    write_figure(args.output_dir.resolve() / "figures" / "traffic_simulation.svg", rows)
    for row in rows:
        print(f"{row[0]}: n={row[1]}, G/channel={row[2]}, simulated loss={float(row[4]):.2%}, Poisson-from-G={float(row[5]):.2%}, PDR={float(row[6]):.2%}")
    print(f"Illustrative workload only; {replications} deterministic seeds. Percentiles describe run-to-run spread under the configured assumptions, not input-parameter uncertainty or shrine traffic measurements.")


if __name__ == "__main__":
    main()
