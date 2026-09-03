# AI-Assisted Research in Educational Text and LLM Evaluation

I use AI-assisted coding to operationalize research questions in LLM evaluation, educational text analysis, and learning technology.

This repository has been deliberately reduced to three projects that I can explain clearly. It does not present a large software product or claim that every line was written independently. I defined the research questions, analytical requirements, data structure, validation criteria, and interpretation workflow; OpenAI Codex substantially assisted implementation, refactoring, debugging, tests, and documentation.

## Projects

### 1. [AI Educational Text Evaluation](projects/01-ai-educational-text-evaluation/)

The primary project evaluates 45 AI-generated adaptations of selected *Journey to the West* chapters: 3 chapters × 3 systems × 5 runs. It examines readability, externally supplied Lexile results, lexical characteristics, content preservation, and repeated-output stability.

This study evaluates **AI-generated educational materials**. It did not include a learner experiment and does not claim to measure learning outcomes.

### 2. [Bilingual LLM Evaluation](projects/02-bilingual-llm-evaluation/)

This project combines a six-model Chinese–English comparison across domain and prompt conditions with a smaller temporal-reliability case study. The primary cross-model design uses model × domain × prompt analysis. A paired comparison is retained only as a supplementary utility and is not described as the paper's main statistical design.

### 3. [Timed Academic Writing](projects/03-timed-academic-writing/)

A small offline Python/Tkinter writing-practice tool with a ten-minute timer, prompt, word count, copy, clear, restart, and local draft saving. It is not an official ETS product and contains no AI scoring or feedback service.

## Public-data boundary

Research datasets and generated texts are intentionally excluded. This repository contains code, methodological documentation, tests that create temporary dummy values, and selected aggregate figures only.

The repository does **not** include:

- CSV, XLSX, XLS, or TMX research data;
- source texts, reference translations, or generated research texts;
- Lexile result files or content-preservation coding tables;
- questionnaire files or participant data;
- API keys, environment files, local deployment screenshots, or third-party source repositories.

## How the code is organized

Metric code is grouped by research project rather than presented as one file or repository per metric. Each research folder contains one analysis module, one statistics module, tests, and a plain-language `METHOD_NOTES.md`.

## Evidence and limitations

Selected figures are aggregate research outputs. They document work completed with private research materials but do not make the underlying texts public. The method notes state the sample/design limits and distinguish user decisions from AI-assisted implementation.

## License

Unless otherwise noted, source code is released under the MIT License. Research figures and written research content remain © FZH0504 and are not research datasets licensed for reuse.
