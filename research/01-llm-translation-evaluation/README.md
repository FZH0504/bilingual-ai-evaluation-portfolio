# LLM Translation Evaluation Pipeline

## Research purpose

This project supports paired Chinese-English translation evaluation under two configurable prompt conditions. It is designed for transparent data validation, COMET scoring, linguistic feature analysis, external metric import, and paired statistical comparison.

## Workflow

```text
Paired bilingual input
  -> validation of IDs, prompts, source/reference consistency, and duplicates
  -> COMET scoring with whole-text or manually aligned segments
  -> local readability, lexical, overlap, and connective measures
  -> external linguistic feature import when available
  -> merged results and paired statistical diagnostics
```

## Research-facing strengths

- Uses `text_id + condition + generation_id` as an auditable key.
- Checks that Chinese source and English reference remain constant across paired conditions.
- Does not silently truncate long texts; records alignment review cases.
- Records COMET model, device, batch size, and scoring timestamp.
- Keeps automatic metrics, local operational measures, and externally imported features distinct.
- Reports descriptive differences, confidence intervals, effect sizes, and low-power warnings.

## Role and scope

The scripts represent evaluation tooling and analysis support. They do not claim that new metrics or translation models were developed. The portfolio contribution is the organization, validation, application, cleaning, and interpretation of multilingual evaluation data.

## Running the pipeline

1. Place an authorized workbook in `data/input.xlsx` using the template schema.
2. Run `01_validate_data.py` and inspect `outputs/validation_report.xlsx`.
3. Run `02_run_comet.py` in the COMET environment.
4. Run `03_run_text_metrics.py` in the text-metrics environment.
5. Run `04_merge_and_statistics.py` to produce merged outcomes, paired tests, and diagnostic figures.

The original local project contains the detailed environment notes. This public version intentionally excludes virtual environments, logs, and private raw data.
