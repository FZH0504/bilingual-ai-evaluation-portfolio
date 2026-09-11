# Method Notes

## Research question

How do different generative AI systems differ in readability, content preservation, and output stability when adapting literary texts for possible educational use?

## Design

The private study contains 3 texts × 3 systems/conditions × 5 runs = 45 outputs. Repeated runs allow the analysis to examine whether a result is stable or driven by one generation.

## Readability and lexical measures

- **Lexile:** imported from an externally supplied official result; this code does not estimate or reverse-engineer Lexile.
- **FKGL:** a formula using sentence length and word syllables to estimate US grade-level readability.
- **Dale–Chall:** a formula that combines sentence length and the proportion of words outside a familiar-word list.
- **Mean sentence length:** words divided by sentences.
- **MATTR:** average type–token ratio over moving windows, used to reduce the length sensitivity of ordinary TTR.
- **Word count:** a descriptive length measure, not a quality score.

These measures describe different properties. A lower readability level is not automatically a better educational text.



## Output stability

The analysis checks normalized exact matches, word-frequency cosine similarity, and 5-/10-gram overlap. Thresholds flag pairs for review; similarity flags do not by themselves prove copying or quality.

## Statistics

- **ANOVA:** examines systematic differences across system and chapter factors.
- **Tukey HSD:** a post-hoc pairwise comparison after a multi-group ANOVA result.
- **Assumption checks:** residual normality and variance-homogeneity diagnostics help assess how cautiously results should be interpreted.
- **Run sensitivity:** adds `Run` as an additional categorical factor to check whether the main conclusions remain stable across repeated generations.

The dependent variable changes by analysis—for example Lexile or FKGL. `System` and `Chapter` are factors. A p-value is evidence against a null model under its assumptions; it is not an effect size or proof of educational benefit.

