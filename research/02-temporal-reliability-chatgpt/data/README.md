# Cleaned Summary Data

These CSV files are derived from the local batch COMET and batch text-metric workbooks. They retain model/domain-level evaluation outputs but omit raw Chinese source text, English output text, private prompts, and oversized empty Excel columns.

- `temporal_reliability_model_outputs.csv`: 12 model-output rows with COMET and selected linguistic indicators.
- `temporal_reliability_reference_outputs.csv`: 3 professional English reference rows with comparable text indicators.

The COMET values are reference-based scores from `Unbabel/wmt22-comet-da`. The linguistic indicators are descriptive text properties and should not be interpreted as direct learner outcomes.
