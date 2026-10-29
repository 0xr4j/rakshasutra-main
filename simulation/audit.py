#!/usr/bin/env python3
"""Reproduce selected manuscript arithmetic; this is not a field simulator."""

from __future__ import annotations

import csv
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "claims.json"


def read_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)


def airtime_ms(payload_bytes: int, sf: int, bandwidth: int, cr_index: int, preamble: int) -> float:
    """LoRa airtime with explicit header, CRC enabled, and no low-rate optimization."""
    symbol_s = (2**sf) / bandwidth
    numerator = 8 * payload_bytes - 4 * sf + 28 + 16
    denominator = 4 * sf
    payload_symbols = 8 + max(math.ceil(numerator / denominator) * (cr_index + 4), 0)
    return (preamble + 4.25 + payload_symbols) * symbol_s * 1000


def svg_line_chart(path: Path, title: str, subtitle: str, x_label: str, y_label: str,
                   series: list[tuple[str, list[tuple[float, float]], str]],
                   x_min: float, x_max: float, y_min: float, y_max: float,
                   x_ticks: list[float], y_ticks: list[float], y_percent: bool = False) -> None:
    width, height = 1000, 610
    left, right, top, bottom = 90, 40, 105, 95
    plot_w, plot_h = width - left - right, height - top - bottom
    X = lambda x: left + (x - x_min) / (x_max - x_min) * plot_w
    Y = lambda y: top + (y_max - y) / (y_max - y_min) * plot_h
    esc = lambda s: (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">',
             '<rect width="100%" height="100%" fill="#0b1120"/>',
             '<style>text{font-family:Inter,Segoe UI,Arial,sans-serif}.muted{fill:#9eacc3}.title{fill:#f4f7fb;font-size:25px;font-weight:700}.small{font-size:13px}.label{fill:#d7e2f2;font-size:14px}.grid{stroke:#26344b;stroke-width:1}</style>',
             f'<text x="{left}" y="42" class="title">{esc(title)}</text>',
             f'<text x="{left}" y="68" class="muted small">{esc(subtitle)}</text>']
    for tick in y_ticks:
        y = Y(tick)
        label = f"{tick*100:.0f}%" if y_percent else f"{tick:g}"
        parts += [f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" class="grid"/>',
                  f'<text x="{left-12}" y="{y+5:.1f}" text-anchor="end" class="muted small">{label}</text>']
    for tick in x_ticks:
        x = X(tick)
        parts += [f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height-bottom}" class="grid" opacity=".55"/>',
                  f'<text x="{x:.1f}" y="{height-bottom+24}" text-anchor="middle" class="muted small">{tick:g}</text>']
    parts += [f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#61718b"/>',
              f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#61718b"/>',
              f'<text x="{left+plot_w/2}" y="{height-27}" text-anchor="middle" class="label">{esc(x_label)}</text>',
              f'<text x="25" y="{top+plot_h/2}" transform="rotate(-90 25 {top+plot_h/2})" text-anchor="middle" class="label">{esc(y_label)}</text>']
    for index, (name, points, color) in enumerate(series):
        coords = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in points)
        parts.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')
        legend_x = left + index * 220
        parts += [f'<line x1="{legend_x}" y1="{height-62}" x2="{legend_x+27}" y2="{height-62}" stroke="{color}" stroke-width="3"/>',
                  f'<text x="{legend_x+36}" y="{height-57}" class="muted small">{esc(name)}</text>']
    parts.append(f'<text x="{left}" y="{height-7}" class="muted" font-size="11">Calculated from stated inputs; no field measurements.</text>')
    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def paper_reconciliation_rows(cfg: dict) -> list[list[str]]:
    """Compare paper headlines with calculations from the paper's stated inputs."""
    rows: list[list[str]] = []
    lora = cfg["lora"]
    for payload, manuscript_value in ((28, "66.82 ms"), (77, "138.50 ms"), (213, "338.18 ms")):
        calculated = airtime_ms(payload, lora["spreading_factor"], lora["bandwidth_hz"],
                                lora["coding_rate_index"], lora["preamble_symbols"])
        rows.append([f"airtime_{payload}_bytes", manuscript_value, f"{calculated:.3f} ms",
                     "Calculated from stated SF7/BW/CR/preamble assumptions",
                     "Arithmetic reproduced; not a radio measurement"])
    n_tags = cfg["active_tags_per_cell"][-1]
    g_base = cfg["aloha_table"][1]["offered_load_fraction"][-1]
    g_new = cfg["aloha_table"][3]["offered_load_fraction"][-1]
    loss_base = 1 - math.exp(-2 * g_base)
    loss_new = 1 - math.exp(-2 * g_new)
    reduction = 1 - g_new / g_base
    rows.extend([
        ["aloha_baseline_loss_3000", "54.2%", f"{loss_base:.4%}",
         f"Calculated from manuscript G={g_base:.3f} at N={n_tags}",
         "Formula reproduced; offered-load derivation not established"],
        ["aloha_proposed_loss_3000", "15.8%", f"{loss_new:.4%}",
         f"Calculated from manuscript G={g_new:.3f} at N={n_tags}",
         "Formula reproduced; offered-load derivation not established"],
        ["offered_load_reduction_3000", "82.4% (abstract)", f"{reduction:.4%}",
         f"Calculated from Table IV G values {g_base:.3f} -> {g_new:.3f}",
         "Mismatch: Table IV implies 77.9%; reconcile manuscript"],
    ])
    bat = cfg["battery"]
    daily_avg = (bat["active_current_ua"] * bat["active_hours_per_day"]
                 + bat["sleep_current_ua"] * bat["sleep_hours_per_day"]) / (
                     bat["active_hours_per_day"] + bat["sleep_hours_per_day"])
    for claim_id, capacity, claim in (
        ("battery_life_25c", bat["nominal_capacity_mah"], bat.get("claimed_nominal_life_months")),
        ("battery_life_cold", bat["cold_capacity_mah"], bat["claimed_cold_life_months"]),
    ):
        months = capacity * 1000 / daily_avg / 24 / 30.4375
        rows.append([claim_id, f"{claim:g} months" if claim is not None else "not stated",
                     f"{months:.2f} months",
                     f"Calculated from {capacity} mAh and {daily_avg:.4f} uA weighted active/sleep current",
                     "Arithmetic mismatch; not a validated battery-life model"])
    ble = cfg["ble_capture"]
    dwell = ble["detection_zone_m"] / (ble["vehicle_speed_kmh"] / 3.6)
    opportunities = math.floor(dwell / ble["advertising_interval_s"])
    p_needed = 1 - (1 - ble["claimed_capture_probability"]) ** (1 / max(opportunities, 1))
    rows.append(["ev_capture_20kmh", f"{ble['claimed_capture_probability']:.1%} paper claim",
                 f"{opportunities} minimum opportunities; {p_needed:.2%} independent per-ad success required",
                 f"Calculated from {dwell:.2f} s dwell and {ble['advertising_interval_s']:.2f} s interval",
                 "Unverified: per-ad reception probability and independence are not measured"])
    rows.append(["field_results", "Paper labels some results empirical",
                 "No raw field dataset, device logs, or experimental protocol supplied",
                 "Repository input inventory",
                 "Not independently verifiable; no field data available"])
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT,
                        help="output root (defaults to this repository)")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    cfg = read_config()
    (output / "results").mkdir(parents=True, exist_ok=True)
    (output / "figures").mkdir(parents=True, exist_ok=True)
    lora = cfg["lora"]
    airtime_rows = []
    for payload in lora["phy_payload_bytes"]:
        airtime_rows.append([payload, lora["spreading_factor"], lora["bandwidth_hz"],
                             f"{airtime_ms(payload, lora['spreading_factor'], lora['bandwidth_hz'], lora['coding_rate_index'], lora['preamble_symbols']):.3f}",
                             "recomputed from stated PHY assumptions; not a regulatory validation"])
    write_csv(output / "results" / "lora_airtime.csv",
              ["phy_payload_bytes", "sf", "bandwidth_hz", "airtime_ms", "status"], airtime_rows)

    n_cells = cfg["active_tags_per_cell"]
    aloha_rows, lines = [], []
    colors = ["#7585a1", "#ff7f73", "#ffbf69", "#58d6c5"]
    for i, item in enumerate(cfg["aloha_table"]):
        values = []
        for n, g in zip(n_cells, item["offered_load_fraction"]):
            loss = 1 - math.exp(-2 * g)
            aloha_rows.append([item["name"], n, f"{g:.3f}", f"{loss:.6f}",
                               "G copied from manuscript; loss recomputed with pure-ALOHA formula"])
            values.append((n, loss))
        lines.append((item["name"], values, colors[i]))
    write_csv(output / "results" / "aloha_claim_check.csv",
              ["architecture", "active_tags_in_cell", "offered_load_fraction_from_paper", "recomputed_loss_fraction", "status"], aloha_rows)
    svg_line_chart(output / "figures" / "aloha_claim_check.svg",
                   "Pure-ALOHA loss from the paper’s offered-load values",
                   "Recomputes only the formula using the manuscript's G values",
                   "Active tags stated for cell", "Packet loss", lines, 500, 3000, 0, 1,
                   n_cells, [0, .2, .4, .6, .8, 1], True)

    bloom = cfg["bloom"]
    bloom_rows = []
    bloom_points = []
    for n in bloom["population"]:
        fp = (1 - math.exp(-bloom["hashes"] * n / bloom["bits"])) ** bloom["hashes"]
        bloom_rows.append([n, bloom["bits"], bloom["hashes"], f"{fp:.8f}",
                           "approximation; assumes independent uniform hashes"])
        bloom_points.append((n, fp))
    write_csv(output / "results" / "bloom_false_positive.csv",
              ["inserted_ids", "filter_bits", "hashes", "approx_false_positive_fraction", "status"], bloom_rows)
    svg_line_chart(output / "figures" / "bloom_false_positive.svg",
                   "Bloom-filter false-positive rate by population size",
                   "512-bit filter, three hashes; standard approximation",
                   "Inserted IDs", "False-positive probability", [("512 bits / 3 hashes", bloom_points, "#58d6c5")],
                   0, 1024, 0, 1, [0, 200, 400, 600, 800, 1000], [0, .2, .4, .6, .8, 1], True)

    ble = cfg["ble_capture"]
    distance_m = ble["detection_zone_m"]
    speed = ble["vehicle_speed_kmh"] / 3.6
    dwell = distance_m / speed
    opportunities = math.floor(dwell / ble["advertising_interval_s"])
    p_claim = ble["claimed_capture_probability"]
    p_needed = 1 - (1 - p_claim) ** (1 / max(opportunities, 1))
    ble_rows = [[f"{dwell:.4f}", opportunities, f"{p_claim:.4f}", f"{p_needed:.6f}",
                 "requires independent per-ad reception; the required reception probability is not measured"]]
    write_csv(output / "results" / "ble_capture_assumption.csv",
              ["dwell_seconds", "minimum_opportunities_by_floor", "paper_capture_claim", "required_per_ad_success_probability", "status"], ble_rows)

    pseudo = cfg["pseudonym"]
    collision = 1 - math.exp(-pseudo["tag_population"] * (pseudo["tag_population"] - 1) / (2 * 2**pseudo["bits"]))
    write_csv(output / "results" / "pseudonym_collision_estimate.csv",
              ["population", "identifier_bits", "birthday_collision_probability", "status"],
              [[pseudo["tag_population"], pseudo["bits"], f"{collision:.8f}", "uniform random-space approximation, not observed pseudonym data"]])

    bat = cfg["battery"]
    active, sleep = bat["active_hours_per_day"], bat["sleep_hours_per_day"]
    daily_avg = (bat["active_current_ua"] * active + bat["sleep_current_ua"] * sleep) / (active + sleep)
    batt_rows = []
    for label, capacity in [("nominal", bat["nominal_capacity_mah"]), ("cold derated assumption", bat["cold_capacity_mah"])]:
        continuous_months = capacity * 1000 / bat["active_current_ua"] / 24 / 30.4375
        scheduled_months = capacity * 1000 / daily_avg / 24 / 30.4375
        batt_rows.append([label, capacity, f"{continuous_months:.2f}", f"{scheduled_months:.2f}",
                          "ideal capacity/current arithmetic only; excludes cell curves, pulses, cutoff and self-discharge"])
    write_csv(output / "results" / "battery_arithmetic.csv",
              ["capacity_case", "capacity_mah", "ideal_months_continuous_active", "ideal_months_with_stated_daily_sleep", "status"], batt_rows)
    pulse_c = bat["emergency_peak_current_ma"] / 1000 * bat["peak_duration_ms"] / 1000 / (bat["hold_up_capacitance_uf"] / 1_000_000)
    write_csv(output / "results" / "capacitor_pulse_estimate.csv",
              ["current_ma", "pulse_duration_ms", "capacitance_uf", "ideal_capacitor_only_voltage_change_v", "status"],
              [[bat["emergency_peak_current_ma"], bat["peak_duration_ms"], bat["hold_up_capacitance_uf"], f"{pulse_c:.2f}",
                "ideal ΔV=I·t/C sanity check; not a model of the battery-plus-capacitor circuit"]])
    batt_plot = []
    for label, capacity in [("Nominal cell", bat["nominal_capacity_mah"]), ("Cold capacity assumption", bat["cold_capacity_mah"])]:
        pts = []
        for hours in range(8, 25):
            avg = (bat["active_current_ua"] * hours + bat["sleep_current_ua"] * (24 - hours)) / 24
            months = capacity * 1000 / avg / 24 / 30.4375
            pts.append((hours, months))
        batt_plot.append((label, pts, "#58d6c5" if capacity == bat["cold_capacity_mah"] else "#ffbf69"))
    svg_line_chart(output / "figures" / "battery_idealized_runtime.svg",
                   "Ideal battery-life estimate from capacity and current",
                   "Ignores pulse loads, cutoff, cold discharge curves, losses and aging",
                   "Active hours per day", "Idealized months", batt_plot, 8, 24, 0, 90,
                   [8, 10, 12, 14, 16, 18, 20, 22, 24], [0, 15, 30, 45, 60, 75, 90])

    write_csv(output / "results" / "paper_reconciliation.csv",
              ["claim_id", "manuscript_reported_value", "recomputed_value_or_evidence",
               "basis_and_provenance", "assessment"],
              paper_reconciliation_rows(cfg))

    print("Generated audit CSVs in results/ and analytical figures in figures/.")
    print(f"EV capture arithmetic: {dwell:.2f} s zone dwell, {opportunities} minimum opportunities, {p_needed:.1%} per-ad success required for the stated aggregate capture claim.")
    print(f"32-bit pseudonym birthday collision estimate for {pseudo['tag_population']} tags: {collision:.3%}.")
    print("These are arithmetic checks and assumption-based illustrations, not field measurements.")


if __name__ == "__main__":
    main()
