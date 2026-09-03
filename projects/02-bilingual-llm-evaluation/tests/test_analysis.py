import importlib.util
import unittest
from pathlib import Path

import pandas as pd

MODULE_PATH = Path(__file__).parents[1] / "analysis.py"
SPEC = importlib.util.spec_from_file_location("bilingual_analysis", MODULE_PATH)
analysis = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(analysis)


class AnalysisTests(unittest.TestCase):
    def test_validation_and_text_metrics(self):
        frame = pd.DataFrame([{
            "text_id": "T1",
            "domain": "finance",
            "model": "M1",
            "prompt": "zero",
            "source_zh": "示例",
            "reference_en": "A clear reference sentence.",
            "output_en": "A clear model sentence.",
        }])
        result = analysis.evaluate_text_rows(frame)
        self.assertEqual(result.loc[0, "word_count_output"], 4.0)
        self.assertIn("flesch_kincaid_grade_difference", result.columns)

    def test_duplicate_study_key_is_rejected(self):
        row = {
            "text_id": "T1", "domain": "finance", "model": "M1", "prompt": "zero",
            "source_zh": "示例", "reference_en": "Reference.", "output_en": "Output.",
        }
        with self.assertRaises(ValueError):
            analysis.validate_study_frame(pd.DataFrame([row, row]))

    def test_aligned_comet_aggregation_is_arithmetic_mean(self):
        rows = [
            {"text_id": "T1", "domain": "finance", "model": "M1", "prompt": "zero", "segment_id": 1, "comet_score": 0.6},
            {"text_id": "T1", "domain": "finance", "model": "M1", "prompt": "zero", "segment_id": 2, "comet_score": 0.8},
        ]
        result = analysis.aggregate_aligned_comet_segments(pd.DataFrame(rows))
        self.assertAlmostEqual(result.loc[0, "comet_score"], 0.7)
        self.assertEqual(result.loc[0, "aggregation_method"], "arithmetic_mean_of_manually_aligned_segments")

    def test_temporal_summary_is_marked_descriptive(self):
        frame = pd.DataFrame([
            {"model_version": "v1", "domain": "policy", "COMET": 0.7},
            {"model_version": "v2", "domain": "policy", "COMET": 0.8},
        ])
        result = analysis.summarize_temporal_metrics(frame, ["COMET"])
        self.assertTrue(result["interpretation_scope"].eq("descriptive_snapshot_only").all())


if __name__ == "__main__":
    unittest.main()
