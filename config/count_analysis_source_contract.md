# 固定计数工作单元：作者点分数核 + 一种参考固定的替代估计

这是已经完成的方法设计与已编写程序的说明，不是重新选题。旧的 DNA-PK NO-GO、A rejected、双模块交叉未重复、Wilson DESIGN_SERIES_BLOCKED 都保留。

## 科学目标

检验**当前 DDRi 观测在实际构建体、样本和汇总方式层面获得什么支持**，并比较一种不使用药物结果挑选 guide/TSS 的描述估计。不预测新靶点；不解释技术/生物学各占多少比例；不以提高 v2-v3 相关为目标。

## 当前授权与范围

- v2：用完整22个样本重建父方法过滤及归一化；只报告五个单药及独立gamma。组合条件参与作者原有过滤/归一化，不新增组合生物学命题。
- v3：严格分开背景，本次效应只做parent WT；完整输入的KO样本只用于文件结构/身份核验，KO效应不进入主分析。
- 原作者全流程适配器另提供：v2 0.4.14；v3 0.4.15。只能在已有相应环境中调用，不静默升级/安装。
- 使用两份原HDF5整数count对象。`.h5ad.gz` 实为HDF5内部压缩；按签名处理，不按扩展名gunzip。
- 参考映射从已上传 Stage-0R 总包中实际解析完整273,731行重新制成压缩表，文件hash固定；所有矩阵ID都有对应记录。不是用少数后续验证guide代替文库。

## 两个严格区分的轨道

### P：作者 compare_reps 点分数核重建

这部分为源码核对后的独立算术实现，不声称已完成论文所有gene-level输出复现。

v2对全部22样本执行all raw counts >=1的原过滤；v3 WT先按父代码添加 floor(mean(two real T0)) 的合成记录，再执行all counts >=40过滤。此合成记录只在P使用；真实T0 N永远是2。

所有零值仅替换为0.5。用PyDESeq2文档化的median-log-ratio size-factor公式归一化。原研究PyDESeq2的精确传递依赖版本未公开于所读watermark，因此公式一致不等于环境/全部导出bitwise一致。

逐比较筛选：v2归一化ref/drug所有列均值>=40；v3 rho使用either/any>=40。gamma仍走源码默认mean筛选，不把rho参数错误传给gamma。

对保留的control集合，逐位置计算：

`d_g,r = [log2(drug_g,r)-log2(ref_g,r) - median_NTC(log2(drug)-log2(ref))_r] / growth`。

v2 growth=1；v3 rho分母为abs(mean vehicle PD - mean drug PD)。分数表取配对位置的均值。`buildPhenotypeData`逐重复的增长分母另有不同定义；不得与summary point score混作同一个数。

没有已恢复的文化分支祖先pairing，故这里的rep1-rep1是**源码位置/标签约定**，不是新证实的生物学配对。P不产生新的生物学p/FDR。

完整父方法还包括：v2从NTC抽样pseudogenes、每组每个重复取绝对效应最大3条guide均值、按最小p选TSS。这些只有`run_historical_parent.py`在历史包内执行；不由本核冒名替代。原随机种子未记录，本适配器种子固定为20260920，不能声称复现了原随机control分组。全流程成功后也仍需与指定原导出核对才叫数值复现通过。

### R：唯一的参考固定替代估计

目的：不因某条guide在药物下很强才保留它，不按最小p选转录本；保留显著耗竭的drug记录。

1. 对每个parent campaign，在**真实T0 mean raw>=40且真实vehicle mean raw>=40**的参考信息中选可观测构建体。阈值40继承原处理数量级，是工作阈值而非实测有效敲低证据。它会限制推断总体；不能称其全基因无偏。
2. 全文库同一序列对应多个gene标签的记录不进入此替代估计，但完整ledger保留；P仍完全保留父处理的身份。因为这一改变与汇总方法同时发生，二者差异不能分解成某一个因素的因果贡献。
3. 合格NTC集合固定，至少20个；不足即停，不自动放宽。
4. 逐sample计算 log2(count with zero-only .5) 减去同sample合格NTC的median log count。
5. 同一 **target×transcript** 内对所有参考合格构建体取等权median，得到每个真实sample一个数。未知transcript单列；不挑最佳TSS，不合并重复gene identities。
6. drug对vehicle使用样本均值差。gamma独立用vehicle对真实T0，不拿gamma代替rho，不将不同背景或培养基混合。
7. 参考不足的target×transcript也保留行，记不可估计；drug零值保留并计数。没有成功hit筛选。

R是描述性log-count差，既不叫growth-normalised rho，也不叫因果药效。它和P不是同一估计量，比较目的在于测量/汇总依赖性，不是挑赢家。

## 不确定性如何处理

- 输出每个真实sample的基因组描述；guide不是生物学重复。
- 独立端点培养假设下计算working SE：sqrt(s2_drug/n_drug+s2_vehicle/n_vehicle)。明确只是工作模型。
- 精确配对未知时，对2!或3!全部排列计算paired SE的范围；这些排列不是新样本、不是bootstrap CI、不决定选用哪个配对。
- 无matched T0第三真实样本；R绝不制造它。两个/三个培养重复不等于精度充分。
- 不把某个模型SE或零SE当成已经校准的生物学置信区间，不报告p/FDR，不估计生物学假阴性率。

## 预定交付

所有construct的P选择账本及点分数；全部target×transcript的R结果和缺失原因；真实sample值；NTC和library-mapped count QC；增长分母；代码/参数/输入hash。完整结果按ID排序，不做新候选提名。

## 验收

文件签名、hash、样本身份、条件alias、构建体映射与target必须一致；零/负/非整数/缺失检查照实。P每个比较的control median消去可在数值测试中检查。单元测试与synthetic端到端必须通过。

**主统计任务可完成，并不表示完整作者gene导出已复现；完整父环境不可用只阻塞optional adapter，不取消已经完成的P/R结果。**

## 停止

只在必要输入/映射/数值无法解释时停止相关轨道。低覆盖或不利结果写进结果，不自动改规则。禁止把这里的新估计用于改写已冻结原报告或重新提名原交叉命题。确认、模型、正交新数据及新队列均不在本轮。
