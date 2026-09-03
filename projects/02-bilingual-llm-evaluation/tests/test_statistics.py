import importlib.util
import unittest
from pathlib import Path

import pandas as pd

MODULE_PATH = Path(__file__).parents[1] / "statistics.py"
SPEC = importlib.util.spec_from_file_location("bilingual_statistics", MODULE_PATH)
statistics = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(statistics)


class StatisticsTests(unittest.TestCase):
    def test_factorial_anova_has_three_primary_factors(self):
        rows = []
        for model, model_shift in [("A", 0.0), ("B", 1.0), ("C", 2.0)]:
            for domain, domain_shift in [("finance", 0.0), ("policy", 0.4), ("technology", 0.8)]:
                for prompt, prompt_shift in [("zero", 0.0), ("domain", 0.2), ("glossary", 0.3)]:
                    for replicate in range(2):
                        rows.append({
                            "model": model,
                            "domain": domain,
                            "prompt": prompt,
                            "COMET": 0.5 + model_shift + domain_shift + prompt_shift + replicate * 0.01,
                        })
        table, _ = statistics.factorial_anova(pd.DataFrame(rows), "COMET")
        effects = set(table["effect"])
        self.assertTrue({"C(model)", "C(domain)", "C(prompt)"}.issubset(effects))
        self.assertIn("partial_eta_squared", table.columns)

    def test_paired_function_is_explicitly_supplementary(self):
        frame = pd.DataFrame([
            {"text_id": "T1", "condition": "A", "score": 1.0},
            {"text_id": "T1", "condition": "B", "score": 1.2},
            {"text_id": "T2", "condition": "A", "score": 2.0},
            {"text_id": "T2", "condition": "B", "score": 2.1},
            {"text_id": "T3", "condition": "A", "score": 3.0},
            {"text_id": "T3", "condition": "B", "score": 3.3},
        ])
        result = statistics.supplementary_paired_comparison(frame, "score")
        self.assertEqual(result["analysis_scope"], "supplementary_paired_two_condition_utility")
        self.assertEqual(result["n_pairs"], 3)


if __name__ == "__main__":
    unittest.main()
