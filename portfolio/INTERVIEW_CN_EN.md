# Interview narratives and evidence answers

These scripts describe a completed AI-assisted project, not unaided personal invention. Use the factual responsibility statement in `docs/PERSONAL_RESPONSIBILITY.md`; do not memorize a claim you cannot defend.

## One sentence
**EN:** I studied whether a pathway-prioritization argument from public CRISPR data depends on which comparator genes are actually analyzable.

**中：**我研究公共 CRISPR 筛选里，一个通路优先级判断是否依赖于实际纳入了哪些比较基因。

## Three sentences
**EN:** Pooled screens can compare unequal fractions of named pathways, so a strong-looking summary may not describe the same biological population. I completed an AI-assisted case study that reconstructs source-table and count-export analyses, separates targeting-unit changes from new genes, and preserves failed predictions. In this archive the contrast reverses mainly because the comparator changes while the mitochondrial component is stable; expanded coverage also reaches count floors, so the analysis does not establish a true opposite mechanism.

**中：**同样的通路名字，可能对应很不一样的实际可分析成员，所以一个漂亮差值未必能代表整个通路。我用 AI 辅助完成源评分表和计数导出分析，把同一基因的靶向单位变化与新增基因分开，并保留失败预测。结果是比较集合明显改变、线粒体分量基本稳定，差值因此反转；扩大覆盖也加入低计数，所以不能把后一版称为真正机制。

## 60–90 seconds: hiring scientist
My project concerns a practical step before following up a functional-screen hit: checking whether the comparison actually supports the biological argument. I used public CRISPR data, not experiments I generated. The central case compares mitochondrial translation with a fixed translation-elongation set in A549 WT and PRDX1-knockout cells, with vehicle and a DNA-PK inhibitor.

The key choice was to separate two things that are often hidden in a pathway mean: additional targeting units for the same genes, and additional genes. The contrast changed from positive to negative. But the mitochondrial component hardly changed; the comparator did. Restoring comparator coverage also brought in low-count observations, so I did not claim that the newer result was the biological truth.

The project contribution is this explicit empirical diagnosis and its reproducible source-table/count-export record. AI assisted the implementation and drafting; the original experiments and established mechanisms belong to the source investigators. It demonstrates how I approach a bounded evidence problem, not that I discovered a drug target or completed a clinical validation programme.

**中文讲法：**这个项目处理的是功能筛选命中之后、真正投入跟进之前的问题：现有比较到底能支持什么生物学判断。我用的是公开 CRISPR 实验，不是自己做的湿实验。主体比较 A549 的 WT 和 PRDX1-KO 在 vehicle／DNA-PK 药物下，两组固定功能基因的相对变化。最关键的是分开同一基因增加靶向单位和新增基因。差值从正变负，但线粒体分量基本没变，变化主要来自比较组。新增成员又有低计数问题，所以我没有说新结果就是真相。成果是这个具体经验诊断和可复算流程；实现有 AI 辅助，原实验和机制归原作者。

## Five minutes: technical / research interview
### 0:00–0:50 — The question
I started from the broader issue that a genetic nomination is not automatically a pharmacological target. The completed project contains earlier, unsuccessful transfer comparisons, but the final main question is narrower and more answerable: is one pathway-prioritization contrast stable to how its comparator population becomes analyzable? I selected a public-data case study rather than claiming that computational complexity could replace missing experiments.

### 0:50–1:40 — What the data actually are
The terminal input is a complete integer-count export with 64,237 physical constructs and 16 real sample records. WT and PRDX1-KO each have two T0 records and three vehicle and three drug endpoint records. A dual-guide cassette is one physical reagent. The transcript label identifies a targeting annotation, not measured isoform abundance. The original investigators generated the data; this project reanalyses them. Clone establishment and PRDX1 background cannot be separated completely.

### 1:40–2:35 — The decisive comparison
I retained fixed Reactome definitions and two declared count transforms. S0 keeps the original qualified genes and targeting units. S1 keeps the genes but expands their T0-qualified units. S2 adds all T0-qualified genes. Within each sample, values are averaged by construct, unit, gene and pathway. Drug-minus-vehicle is computed in each background; the difference of those effects is compared between pathways. The same NTC centre cancels from the within-sample balance, but it does not remove selection or count floors.

### 2:35–3:30 — What changed the decision
With zero-only replacement, the M-minus-E contrast is +0.861, +0.477 and −1.761. The crucial disclosure is that M stays near +1.04 while E grows from +0.183 to +2.814. The old E set has 23 genes and the expanded set 91. The added 68 have a different observed mean. Count+1 preserves the reversal. This is not a discovery that averages depend on membership; it is an empirical finding of which members drive this particular argument and why the original positive balance cannot represent a membership-insensitive priority.

### 3:30–4:15 — Why I did not overinterpret it
S2 also includes many counts near zero. Eligibility used vehicle counts that also occur in the response. Consequently, composition, measurement and growth remain entangled. Neither S0 nor S2 is established as the true pathway-wide drug effect. Member and sample deletion are local influence checks, not extra experiments. Passing tests and matching hashes establish computation and identity, not biology. The old crossing remains failed and the original 12-of-36 PRKDC evaluation remains conditional.

### 4:15–5:00 — Contribution, responsibility and what I would change
The project contributes the specific secondary analyses, fixed comparisons, decomposition, and a runnable evidence record. Standard methods and original mechanisms are not mine. AI helped develop and implement the work; I must identify the exact parts I understand and maintain rather than claim unaided authorship. Starting again, I would define the estimand, analyzable population and verification roles earlier and avoid an audit-heavy first presentation. I would not add a new dataset simply to obtain a favourable result. This version is complete as a research case study.

**中文五分钟提示：**先讲可回答的主问题；再讲16个真实样本而不是海量“独立N”；用S0/S1/S2解释靶向单位和基因的区别；展示M基本稳定、E改变；承认低计数和选择／响应共用vehicle；最后明确数据、标准方法、项目贡献和AI责任边界。不要用“后来终于解释了所有早期失败”收尾。

## Professional challenges: precise answers
| Question | Answer and evidence |
|---|---|
| Why did you do S1? | It separates changes within the same genes from addition of genes. See `decision_grid.tsv` and `component_steps.tsv`. |
| Isn't a changed mean trivial? | The general principle is known; the exact sign change, driver and eligibility trade-off here are empirical, not a new theorem. |
| Why not use S2 as truth? | More coverage also means more low-count observations and a changed population. See all four endpoint groups in `count_floor.tsv`. |
| Did you verify a mitochondrial mechanism? | No. M is approximately stable on the fixed reference and the comparison is not an efficacy/occupancy experiment. |
| Why no p-values? | This release describes a finite archive. A biological sampling model would require justified units; gene bootstraps or 81 reused omissions cannot create them. |
| Does two guides mean two reagents? | No. Both arms in one cassette form one physical reagent. |
| Did the full PRKDC rule fail? | No. Only 12 of 36 source calls entered the primary panel. |
| Was R2 untouched validation? | No. It was historically exposed and the crossing was post-discovery. |
| Do source assays validate your pathway? | No. They are source-study experiments on selected reagents with distinct normalization. |
| What is computational QC? | Hashes, equality checks, path tests and reference cancellation. They protect implementations, not causal interpretations. |
| What did you write yourself? | Use the signed responsibility record; distinguish personally reviewed/modified work from AI-origin suggestions or code. No percentages are inferred. |
| How can I reproduce it? | `tools/run.py core` from count export; `tools/run.py historical` from source score tables. No full FASTQ claim. |

## Read-only live walkthrough
Run `python tools/explain_result.py`, open the exact table, and explain the units and components. Then point to the relevant frozen function and one test. Do not edit data or scientific definitions during the demonstration to improve a result.
