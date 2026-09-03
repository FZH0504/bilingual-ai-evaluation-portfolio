import importlib.util
import unittest
from pathlib import Path

import pandas as pd

MODULE_PATH = Path(__file__).parents[1] / "analysis.py"
SPEC = importlib.util.spec_from_file_location("jtw_analysis", MODULE_PATH)
analysis = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(analysis)


def judgment(output_id: str, point: str, score: int, evidence: str) -> dict[str, object]:
    return {
        "source_id": "Chapter14",
        "output_id": output_id,
        "content_point_id": point,
        "content_point_definition": f"Definition {point}",
        "score": score,
        "evidence_exact_excerpt": evidence,
        "evidence_location": "sentence 1" if evidence else "not found",
        "brief_reason": "Dummy test reason",
        "uncertain": "no",
        "confidence": "high",
    }


class AnalysisTests(unittest.TestCase):
    def test_metrics_and_short_mattr(self):
        metrics = analysis.calculate_text_metrics("Cats run. Dogs run.", mattr_window=5)
        self.assertEqual(metrics["word_count"], 4)
        self.assertAlmostEqual(metrics["ttr"], 0.75)
        self.assertFalse(metrics["mattr_full_window"])

    def test_official_lexile_is_parsed_not_estimated(self):
        self.assertEqual(analysis.parse_lexile("840L"), 840.0)
        with self.assertRaises(ValueError):
            analysis.parse_lexile("approximately 840")

    def test_content_requires_evidence_and_complete_coverage(self):
        rows = [
            judgment("A", "CP1", 1, "Evidence A"),
            judgment("A", "CP2", 0, ""),
            judgment("B", "CP1", 1, "Evidence B1"),
            judgment("B", "CP2", 1, "Evidence B2"),
        ]
        summary = analysis.summarize_content_preservation(pd.DataFrame(rows)).set_index("output_id")
        self.assertEqual(summary.loc["A", "content_preservation_rate"], 50.0)
        self.assertEqual(summary.loc["B", "content_preservation_rate"], 100.0)

    def test_stability_flags_normalized_exact_match(self):
        table = analysis.compare_output_texts([
            {"output_id": "A", "source_id": "S1", "text": "Hello, WORLD! one two three four five."},
            {"output_id": "B", "source_id": "S1", "text": "hello world one two three four five"},
        ])
        self.assertEqual(table.loc[0, "review_classification"], "EXACT_DUPLICATE")


if __name__ == "__main__":
    unittest.main()
