# Temporal Reliability of ChatGPT-Generated Bilingual Texts

## Study focus

This study examines whether successive ChatGPT service snapshots produce consistently more reliable and accessible Chinese-English bilingual texts. It treats generated translations as potential bilingual reading-support materials rather than as fully designed instructional lessons.

## Research design

- Four snapshots: GPT-5.0, GPT-5.4, GPT-5.5, and GPT-5.6 Sol
- Three professional domains: finance, technology, and public policy
- One fixed zero-shot translation prompt
- Fixed Chinese source texts and professional English references
- Data collection period: October 2025 to July 2026
- Measures: COMET, Flesch Reading Ease, Flesch-Kincaid Grade Level, word count, average sentence length, TTR, adjacent content-word overlap, adjacent noun overlap, and connective incidence

## Main descriptive findings

No snapshot improved consistently across all domains and dimensions. Public-policy COMET increased from 0.8220 under GPT-5.0 to 0.8393 under GPT-5.6 Sol, while later outputs became less readable. Technology outputs became shorter and showed stronger lexical overlap over time, but COMET declined after GPT-5.4. Finance peaked semantically under GPT-5.5, while readability peaked under GPT-5.4.

These are descriptive comparisons. Each domain contains one source text and one output per snapshot, so the manuscript does not claim inferential evidence of general temporal superiority.

## Educational relevance

The study connects model reliability to bilingual reading support and AI-assisted language learning. It shows why semantic correspondence, readability, sentence structure, and discourse characteristics should be examined separately when LLM outputs may be used by multilingual learners.

## Limitations

The design uses one source text per domain, one generation per snapshot-text combination, automatic indicators, and no learner comprehension or classroom outcome data. Future work should use more texts, repeated generations, human error annotation, and learner-centered evaluation.

## Publication materials

The manuscript and submission documents are maintained separately from this public summary. Publish the full manuscript only when the venue and collaborators permit public release.

## Cleaned data

The `data/` folder contains aggregate CSV files derived from the batch COMET and text-metric workbooks. The original COMET workbook contained many empty export columns, so only meaningful fields are retained for public analysis.
