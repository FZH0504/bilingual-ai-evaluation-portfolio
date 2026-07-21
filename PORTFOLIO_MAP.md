# Portfolio Classification Map

This map separates research evidence from exploratory coursework and local working materials.

## A. Strongest Evidence for EdTech / Learning Sciences Applications

| Category | Evidence | Why It Matters |
| --- | --- | --- |
| Multilingual LLM evaluation | Cross-domain translation evaluation, COMET, BLEU-family metrics, linguistic features, questionnaires | Shows bilingual data work and multidimensional evaluation |
| Statistical benchmarking | ANOVA / mixed-model result organization, paired comparisons, cautious interpretation | Shows ability to connect measurements to research questions |
| Longitudinal evaluation | Four ChatGPT snapshots across three professional domains | Connects model change to reliability of bilingual learning support |
| Corpus construction | Chinese source, English reference, LLM output, unit-level alignment | Shows traceability from raw language data to evaluation evidence |
| Learning technology prototyping | OpenClaw / OpenMAIC, evaluator prompts, writing workflows, timed practice | Connects analysis to learner-facing AI feedback design |

## B. Useful Supporting Evidence

| Category | Evidence | Recommended Presentation |
| --- | --- | --- |
| Document preprocessing | PDF cropping, OCR preparation, text cleaning | Present as a small reproducible tools project |
| Exploratory NLP visualization | Chinese segmentation and word-cloud GUI | Present as an early exploratory project, not as the main research contribution |
| File / corpus organization | TXT archive inventory and aligned evaluation tables | Show selected representative records rather than a large file dump |

## C. Keep Private or Archive Only

- Virtual environments, `__pycache__`, PyCharm `.idea` metadata, build artifacts, logs, and local server batch files.
- Full OCR text of *Piao / 飘* and other copyrighted source material.
- Raw human evaluation questionnaires or sensitive respondent-level data.
- Full manuscript files before publication unless the venue and co-authors permit public release.

## Existing PyCharm Projects

| Project | Main Contents | Recommended Classification |
| --- | --- | --- |
| `PythonProject` | Word-cloud functions / GUI, CAJ-to-PDF helper, sample output generation, exploratory scripts | Exploratory NLP visualization and document utility work |
| `PythonProject1` | PyCharm project metadata only; no substantive source files found | Empty scaffold; do not publish as a project |
| `PythonProject2` | PDF cropping and a configurable ANOVA / mixed-model analysis script | Document preprocessing plus statistical analysis prototype |
| `PythonProject3` | PyCharm project metadata only; no substantive source files found | Empty scaffold; do not publish as a project |
| `PythonProject4` | PyCharm project metadata only; no substantive source files found | Empty scaffold; do not publish as a project |
| `PythonProject5` | PDF crop script and generated PDF artifacts | Document preprocessing utility |
| `PythonProject6` | OCR preparation, page selection, text cleaning, and large novel corpus files | OCR / corpus preprocessing; publish code only, exclude corpus |

The strongest research-facing implementation is organized as the paired bilingual evaluation pipeline under `research/01-llm-translation-evaluation/`.
