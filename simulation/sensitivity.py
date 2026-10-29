#!/usr/bin/env python3
"""Synthetic schedule-jitter sensitivity; results are not field performance."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from pathlib import Path

from traffic_simulation import (
    collision_rate, packets_baseline, packets_batched, percentile, summarize
)

ROOT = Path(__file__).resolve().parents[1]
JITTER_MAX_SECONDS = [1.5, 3.75, 7.5, 15.0]


def run_loss(cfg: dict, batched: bool, replications: int) -> tuple[list[float], list[float], list[float]]:
    losses, loads, poisson_losses = [], [], []
    for replication in range(replications):
        seed = int(cfg["seed"]) + replication * 2 + (1 if batched else 0)
        packets = (packets_batched(cfg, random.Random(seed)) if batched
                   else packets_baseline(cfg, random.Random(seed)))
        summary = summarize("scenario", packets, cfg["channels"], cfg["duration_seconds"])
        _, load = collision_rate(packets, cfg["channels"], cfg["duration_seconds"])
        losses.append(float(summary[4]))
        loads.append(load)
        poisson_losses.append(1 - math.exp(-2 * load))
    return losses, loads, poisson_losses


def write_figure(path: Path, points: list[tuple[float, float]]) -> None:
    width, height = 920, 480
    left, right, top, bottom = 90, 55, 65, 95
    plot_w, plot_h = width - left - right, height - top - bottom
    x = lambda value: left + value / 15 * plot_w
    y = lambda value: top + (1 - value) * plot_h
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Packet loss at four batch delays</title>',
        '<desc id="desc">In this synthetic model, packet loss falls as the send-delay range widens. No field data are included.</desc>',
        '<rect width="100%" height="100%" fill="#0b1120"/>',
        '<style>text{font-family:Inter,Segoe UI,Arial,sans-serif}.title{fill:#f4f7fb;font-size:23px;font-weight:700}.sub{fill:#9eacc3;font-size:13px}.grid{stroke:#26344b}.line{fill:none;stroke:#58d6c5;stroke-width:4}.point{fill:#ffbf69;stroke:#0b1120;stroke-width:2}</style>',
        '<text x="70" y="38" class="title">Wider batch timing lowers simulated loss</text>',
        '<text x="70" y="60" class="sub">Synthetic one-cell model · 40 runs per setting · no field data</text>',
    ]
    for tick in [0, .2, .4, .6, .8, 1]:
        yy = y(tick)
        parts += [f'<line x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}" class="grid"/>',
                  f'<text x="{left-12}" y="{yy+4:.1f}" text-anchor="end" class="sub">{tick:.0%}</text>']
    for tick in [0, 1.5, 3.75, 7.5, 10, 15]:
        xx = x(tick)
        parts += [f'<line x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" y2="{height-bottom}" class="grid" opacity=".5"/>',
                  f'<text x="{xx:.1f}" y="{height-bottom+24}" text-anchor="middle" class="sub">{tick:g}</text>']
    coords = " ".join(f"{x(a):.1f},{y(b):.1f}" for a, b in points)
    parts.append(f'<polyline points="{coords}" class="line"/>')
    for a, b in points:
        parts += [f'<circle cx="{x(a):.1f}" cy="{y(b):.1f}" r="7" class="point"/>',
                  f'<text x="{x(a):.1f}" y="{y(b)-13:.1f}" text-anchor="middle" class="sub">{b:.1%}</text>']
    parts += [
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#61718b"/>',
        f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#61718b"/>',
        f'<text x="{left+plot_w/2}" y="{height-26}" text-anchor="middle" class="sub">Maximum random send delay within each 15 s flush window (seconds)</text>',
        '<text x="24" y="245" transform="rotate(-90 24 245)" text-anchor="middle" class="sub">Mean simulated packet loss</text>',
        '<text x="70" y="455" class="sub">Assumed inputs; no RF capture or retries; no field observations.</text>',
        '</svg>',
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    parser.add_argument("--replications", type=int, default=None)
    args = parser.parse_args()
    cfg = json.loads((ROOT / "configs" / "traffic_scenario.json").read_text(encoding="utf-8"))
    count = int(args.replications or cfg.get("replications", 40))
    if count < 2:
        raise ValueError("at least two replications are required")
    base_losses, _, _ = run_loss(cfg, False, count)
    rows = [["single arrival + raw ID heartbeat", "", count,
             f"{statistics.mean(base_losses):.8f}", f"{statistics.stdev(base_losses):.8f}",
             f"{percentile(base_losses, .025):.8f}", f"{percentile(base_losses, .975):.8f}",
             "Synthetic baseline; not field data"]]
    points = []
    for max_jitter in JITTER_MAX_SECONDS:
        case = dict(cfg)
        case["batch_jitter_max_seconds"] = max_jitter
        losses, loads, poisson = run_loss(case, True, count)
        mean_loss = statistics.mean(losses)
        rows.append(["15 s batches + 64 B Bloom heartbeat", f"{max_jitter:.2f}", count,
                     f"{mean_loss:.8f}", f"{statistics.stdev(losses):.8f}",
                     f"{percentile(losses, .025):.8f}", f"{percentile(losses, .975):.8f}",
                     f"Synthetic; mean G={statistics.mean(loads):.6f}; "
                     f"mean pure-ALOHA estimate={statistics.mean(poisson):.6f}; not field data"])
        points.append((max_jitter, mean_loss))
    out = args.output_dir.resolve()
    (out / "results").mkdir(parents=True, exist_ok=True)
    with (out / "results" / "jitter_sensitivity.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["scenario", "batch_jitter_max_seconds", "replications", "mean_packet_loss",
                         "run_loss_standard_deviation", "run_loss_p2_5", "run_loss_p97_5", "status"])
        writer.writerows(rows)
    write_figure(out / "figures" / "jitter_sensitivity.svg", points)
    print(f"Wrote jitter sensitivity for {count} fixed-seed replications per case.")
    print("Percentiles show run-to-run spread under the chosen inputs, not assumption uncertainty.")


if __name__ == "__main__":
    main()
