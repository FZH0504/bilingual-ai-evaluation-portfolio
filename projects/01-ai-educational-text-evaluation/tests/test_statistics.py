import importlib.util
import unittest
from pathlib import Path

import pandas as pd

MODULE_PATH = Path(__file__).parents[1] / "statistics.py"
SPEC = importlib.util.spec_from_file_location("jtw_statistics", MODULE_PATH)
statistics = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(statistics)


class StatisticsTests(unittest.TestCase):
    def setUp(self):
        rows = []
        for system, system_shift in [("A", 0.0), ("B", 1.0), ("C", 2.0)]:
            for chapter, chapter_shift in [("14", 0.0), ("23", 0.5), ("27", 1.0)]:
                for run in range(1, 6):
                    rows.append({
                        "System": system,
                        "Chapter": chapter,
                        "Run": run,
                        "FKGL": 5.0 + system_shift + chapter_shift + run * 0.03,
                    })
        self.frame = pd.DataFrame(rows)

    def test_anova_reports_required_values(self):
        table, _ = statistics.two_way_anova(self.frame, "FKGL", "System", "Chapter")
        self.assertIn("F_value", table.columns)
        self.assertIn("p_value", table.columns)
        self.assertIn("partial_eta_squared", table.columns)

    def test_tukey_and_run_sensitivity(self):
        self.assertFalse(statistics.tukey_comparisons(self.frame, "FKGL", "System", "Chapter").empty)
        sensitivity = statistics.run_sensitivity(self.frame, "FKGL", "System", "Chapter", "Run")
        self.assertIn("C(Run)", set(sensitivity["effect"]))


if __name__ == "__main__":
    unittest.main()
