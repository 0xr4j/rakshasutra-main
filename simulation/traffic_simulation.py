#!/usr/bin/env python3
"""Illustrative one-cell traffic simulation. Assumptions are in configs/traffic_scenario.json."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
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
    mean_events_per_pole = tags / passage * interval / poles
    packets: list[tuple[float, float, int]] = []
    for bucket_start in range(0, duration, interval):
        for _pole in range(poles):
            event_count = poisson(rng, mean_events_per_pole)
            while event_count > 0:
                records = min(event_count, cfg["max_tag_records_per_batch"])
                phy_bytes = cfg["lora_mac_phy_overhead_bytes"] + records * cfg["bytes_per_arrival_record"]
                start = bucket_start + rng.uniform(0.2, 1.5)
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


def write_figure(path: Path, rows: list[list[object]]) -> None:
    labels = ["Single-event + raw IDs", "15 s batches + Bloom"]
    colors = ["#91a0b9", "#58d6c5"]
    width, height = 1000, 570
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">',
             '<rect width="100%" height="100%" fill="#0b1120"/>',
             '<style>text{font-family:Inter,Segoe UI,Arial,sans-serif}.title{fill:#f4f7fb;font-size:25px;font-weight:700}.sub{fill:#9eacc3;font-size:14px}.label{fill:#d7e2f2;font-size:13px}.grid{stroke:#26344b}</style>',
             '<text x="70" y="48" class="title">Batching reduces packets, but timing can dominate collisions</text>',
             '<text x="70" y="75" class="sub">One fixed-seed, one-hour synthetic workload; 3,000 tags, 60 poles, 8 channels</text>']
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
        parts.append(f'<line x1="{plot_x}" y1="{plot_y}" x2="{plot_x}" y2="{plot_y+plot_h}" stroke="#61718b"/>')
        parts.append(f'<line x1="{plot_x}" y1="{plot_y+plot_h}" x2="{plot_x+plot_w}" y2="{plot_y+plot_h}" stroke="#61718b"/>')
    parts.append('<text x="70" y="520" fill="#9eacc3" font-size="12">Gold dashed marks on the right show 1−exp(−2G). The periodic batched case violates its Poisson-arrival premise; its large gap is a schedule-burst warning, not a deployment prediction.</text>')
    parts.append('</svg>')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    cfg = json.loads((ROOT / "configs" / "traffic_scenario.json").read_text(encoding="utf-8"))
    rng = random.Random(cfg["seed"])
    baseline = packets_baseline(cfg, rng)
    batched = packets_batched(cfg, rng)
    out = args.output_dir.resolve() / "results"
    out.mkdir(parents=True, exist_ok=True)
    rows = [summarize("Single arrival + raw per-pole ID heartbeat", baseline, cfg["channels"], cfg["duration_seconds"]),
            summarize("15 s chunks + 64 B per-pole Bloom heartbeat", batched, cfg["channels"], cfg["duration_seconds"])]
    with (out / "illustrative_traffic_simulation.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["scenario", "packets", "simulated_offered_load_per_channel", "packets_involved_in_collision", "simulated_packet_loss", "poisson_loss_from_mean_load", "simulated_pdr", "duration_seconds", "status"])
        writer.writerows(rows)
    write_figure(args.output_dir.resolve() / "figures" / "traffic_simulation.svg", rows)
    for row in rows:
        print(f"{row[0]}: n={row[1]}, G/channel={row[2]}, simulated loss={float(row[4]):.2%}, Poisson-from-G={float(row[5]):.2%}, PDR={float(row[6]):.2%}")
    print("Illustrative workload only; assumptions are in configs/traffic_scenario.json and are not shrine traffic measurements.")


if __name__ == "__main__":
    main()
