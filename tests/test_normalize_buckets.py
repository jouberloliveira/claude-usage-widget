import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from claude_usage import _normalize_buckets


class NormalizeBucketsTests(unittest.TestCase):
    def test_bare_key_shape(self):
        raw = {
            "five_hour": {"utilization": 0.45, "resets_at": "2026-05-20T06:00:00Z"},
            "seven_day": {"utilization": 0.2, "resets_at": "2026-05-25T00:00:00Z"},
            "seven_day_opus": {"utilization": 0.1, "resets_at": "2026-05-25T00:00:00Z"},
            "seven_day_sonnet": {"utilization": 0.3, "resets_at": "2026-05-25T00:00:00Z"},
            "seven_day_oauth_apps": {"utilization": 0.0, "resets_at": "2026-05-25T00:00:00Z"},
            "seven_day_cowork": {"utilization": 0.0, "resets_at": "2026-05-25T00:00:00Z"},
            "seven_day_omelette": {"utilization": 0.0, "resets_at": "2026-05-25T00:00:00Z"},
            "tangelo": {"utilization": 0.0, "resets_at": "2026-05-25T00:00:00Z"},
            "iguana_necktie": {"utilization": 0.0, "resets_at": "2026-05-25T00:00:00Z"},
            "omelette_promotional": {"utilization": 0.0, "resets_at": "2026-05-25T00:00:00Z"},
            "extra_usage": {"utilization": 0.0, "resets_at": "2026-05-25T00:00:00Z"},
        }
        buckets = _normalize_buckets(raw)
        labels = {b["label"] for b in buckets}
        self.assertIn("Janela 5h", labels)
        self.assertIn("Janela 7 dias", labels)
        self.assertIn("OAuth Apps · 7 dias", labels)
        self.assertIn("Co-work · 7 dias", labels)
        self.assertIn("Tangelo", labels)
        self.assertIn("Iguana Necktie", labels)
        self.assertIn("Omelette Promo", labels)
        self.assertIn("Uso Extra", labels)
        self.assertEqual(len(buckets), 11)
        five = next(b for b in buckets if b["label"] == "Janela 5h")
        self.assertEqual(five["utilization"], 45.0)
        self.assertEqual(five["resets_at"], "2026-05-20T06:00:00Z")

    def test_limit_window_shape_still_works(self):
        raw = {
            "five_hour_limit_window": {"utilization": 0.5, "resets_at": "x"},
            "seven_day_limit_window": {"utilization": 0.25, "resets_at": "y"},
        }
        buckets = _normalize_buckets(raw)
        labels = [b["label"] for b in buckets]
        self.assertIn("Janela 5h", labels)
        self.assertIn("Janela 7 dias", labels)
        self.assertEqual(len(buckets), 2)

    def test_no_dedup_between_window_and_bare(self):
        raw = {
            "five_hour_limit_window": {"utilization": 0.5, "resets_at": "x"},
            "five_hour": {"utilization": 0.7, "resets_at": "y"},
        }
        buckets = _normalize_buckets(raw)
        self.assertEqual(len(buckets), 1)
        self.assertEqual(buckets[0]["utilization"], 50.0)

    def test_prefix_pair_shape(self):
        raw = {"five_hour_used": 100, "five_hour_limit": 1000, "five_hour_resets_at": "z"}
        buckets = _normalize_buckets(raw)
        self.assertEqual(len(buckets), 1)
        self.assertEqual(buckets[0]["used"], 100)
        self.assertEqual(buckets[0]["limit"], 1000)

    def test_non_dict_input(self):
        self.assertEqual(_normalize_buckets(None), [])
        self.assertEqual(_normalize_buckets([]), [])


if __name__ == "__main__":
    unittest.main()
