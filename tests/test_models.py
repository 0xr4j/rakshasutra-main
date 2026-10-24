import json
import math
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulation"))

import audit
import traffic_simulation


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.claims = json.loads((ROOT / "configs" / "claims.json").read_text(encoding="utf-8"))
        cls.scenario = json.loads((ROOT / "configs" / "traffic_scenario.json").read_text(encoding="utf-8"))
        cls.fixtures = json.loads((ROOT / "tests" / "fixtures" / "overlap_cases.json").read_text(encoding="utf-8"))

    def test_lora_airtime_examples(self):
        expected = [66.816, 138.496, 338.176]
        actual = [audit.airtime_ms(p, 7, 125000, 1, 8) for p in (28, 77, 213)]
        for got, want in zip(actual, expected):
            self.assertAlmostEqual(got, want, places=3)

    def test_aloha_claim_arithmetic(self):
        base = self.claims["aloha_table"][1]["offered_load_fraction"][-1]
        proposed = self.claims["aloha_table"][3]["offered_load_fraction"][-1]
        self.assertAlmostEqual(1 - math.exp(-2 * base), 0.541594, places=6)
        self.assertAlmostEqual(1 - math.exp(-2 * proposed), 0.158021, places=6)
        self.assertAlmostEqual(1 - proposed / base, 0.779487, places=6)

    def test_paper_reconciliation_exposes_mismatches(self):
        rows = {row[0]: row for row in audit.paper_reconciliation_rows(self.claims)}
        self.assertIn("77.9487%", rows["offered_load_reduction_3000"][2])
        self.assertIn("33.76 months", rows["battery_life_cold"][2])
        self.assertIn("64.06%", rows["ev_capture_20kmh"][2])

    def test_ev_capture_requires_unmeasured_per_ad_probability(self):
        cfg = self.claims["ble_capture"]
        dwell = cfg["detection_zone_m"] / (cfg["vehicle_speed_kmh"] / 3.6)
        opportunities = math.floor(dwell / cfg["advertising_interval_s"])
        p = 1 - (1 - cfg["claimed_capture_probability"]) ** (1 / opportunities)
        self.assertEqual(opportunities, 5)
        self.assertAlmostEqual(p, 0.640557, places=6)

    def test_battery_claim_does_not_follow_stated_schedule_arithmetic(self):
        b = self.claims["battery"]
        current = (b["active_current_ua"] * b["active_hours_per_day"]
                   + b["sleep_current_ua"] * b["sleep_hours_per_day"]) / 24
        months = b["cold_capacity_mah"] * 1000 / current / 24 / 30.4375
        self.assertAlmostEqual(months, 33.76, places=2)
        self.assertNotAlmostEqual(months, b["claimed_cold_life_months"], places=0)

    def test_hand_authored_overlap_fixtures(self):
        for case in self.fixtures["cases"]:
            with self.subTest(case=case["name"]):
                collided, _ = traffic_simulation.collision_rate(
                    [tuple(packet) for packet in case["packets"]],
                    case["channels"], case["duration_seconds"])
                self.assertEqual(collided, case["packets_in_collision"])

    def test_fixed_seed_workload_is_reproducible(self):
        first = traffic_simulation.packets_batched(self.scenario, random.Random(27))
        second = traffic_simulation.packets_batched(self.scenario, random.Random(27))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
