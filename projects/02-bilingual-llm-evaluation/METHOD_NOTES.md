# Method Notes

## Research questions

1. How do model, professional domain, and prompting strategy relate to Chinese–English translation evaluation scores?
2. How stable are selected translation and readability measures across changing ChatGPT snapshots?

## Cross-model design

The private study crosses six models, three domains, and three prompt strategies. The 54 full-text records represent design cells rather than 54 independent source texts. Segment-level records provide additional observations but must be interpreted with their within-text dependence in mind.

## Evaluation measures

- **COMET:** a learned reference-based translation metric using source, model output, and reference.
- **BLEU / chrF++ / TER / ROUGE:** surface-overlap or edit-based measures with different sensitivities.
- **BERTScore:** contextual-embedding similarity.
- **Readability and lexical measures:** describe form and accessibility; they are not direct translation-quality or learning-outcome measures.
- **Cohesion features:** operational indicators, not a complete theory of discourse quality.

No single metric is treated as ground truth.

## COMET handling for long text

COMET encodes source, output, and reference components. Long texts are not split independently. When manually aligned segments are available, each segment is scored and a document-level score is the arithmetic mean of accepted segment scores. Without aligned segments, an over-limit record is reported for review.

## Cross-model statistics

The primary public function fits model, domain, and prompt as categorical factors and reports Type II ANOVA main effects. Optional two-way interactions may be examined only when the design supports them. Tukey HSD is a post-hoc pairwise comparison for a chosen factor.

The dependent variable is one metric at a time. F-values compare systematic factor-related variation with residual variation. P-values do not measure practical importance, and they do not show that one system is universally better.

## Supplementary paired analysis

The paired utility compares two conditions on matched `text_id` values. It reports a paired t-test, confidence interval, Cohen's dz, and—when defined—a Wilcoxon signed-rank result. It is useful for a separate paired workflow but is **not** the six-model paper's main design.

## Temporal-reliability boundary

The snapshot comparison is descriptive because there is only one source text per domain/snapshot condition. The plots show observed variation and metric disagreement, not population-level trends or causal model improvement.

## Human-evaluation boundary

Preliminary rubric/questionnaire design exists, but the audited files do not establish completed participant-level human evaluation. It is therefore not presented as a completed method.



