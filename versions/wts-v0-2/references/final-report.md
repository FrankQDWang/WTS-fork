# 终态报告

步骤 15 读。先把内部记录写成 JSON 文件，再从它渲染给用户看的报告。

## 内部记录

路径：`<TASK_WORK_DIR>/wts-v0-2/report.json`。字段沿用报告原有的节名：

| 键 | 对应节 | 内容 |
| --- | --- | --- |
| `requirement_version` | — | 报告依据的需求版本 N |
| `results` | 【结果】 | Top 10 每人 `{candidate_ref, name, current_company, current_title, verdict: "符合" \| "不符合", total, must_have, nice_to_have, risk, basis, unknown_items: [], detail_url}` |
| `coverage` | 【搜索覆盖】 | `{rounds, queries: {primary, secondary}, seen, new, recommendable, strong, company_words: [{word, new_candidates}], probes: [{company, card_count, usable}], pool_size: {initial, from_candidates}, prf: {promoted: [], rejected: []}, degraded_filters: []}` |
| `stop_reason` | 【停止原因】 | 强匹配足够 / 新增候选不足 / 多轮无进展 / 达到最大轮次 / 词族耗尽 / 预算，取一 |
| `unmet` | 【未满足原因】 | `{gap_to_target, exhausted_families: [], unverifiable_hard_filters: []}` |
| `failures` | 【失败项】 | `{candidate_ref, reason}`，含详情采集失败和没有 detail_url 的 |
| `market_insights` | 【市场洞察】 | `{skills, profile, company_sources}` 三小节全文，见下 |

两条硬规则：`detail_url` 来自运行结果，没有的进 `failures`；所有数字来自运行结果和评分记录。以人找岗的输入就是 `results` 中 verdict 为符合且 total ≥ 60 的候选人。

## 用户视图模板

```text
# 寻访报告

找了 <rounds> 轮，看了 <seen> 位候选人，其中 <recommendable> 位值得推荐、<strong> 位很匹配。

推荐名单（按匹配度）：
1. <name> · <current_company> <current_title> · 匹配度 <total> · <basis 一句白话> · <unknown_items 非空时："还没确认：X、Y"> · [查看猎聘详情](detail_url)
...

为什么停下：<stop_reason 的白话，如"能想到的搜法都试过了" / "匹配的人已经够了" / "连续两轮没有新人">

还差什么：<gap_to_target 为 0 时省去本节；否则一句话说差几位、哪些条件在市场上很难同时满足>

没看到简历的：<failures 数量> 位，<原因白话>；为空则省去本节

市场观察：
- 技能：<skills 小节的结论，两三句>
- 这类人的特征：<profile 小节的结论，两三句>
- 公司来源：<company_sources 小节的结论，两三句>
```

渲染规则：`results` 每人一行，`failures` 每人计入数量；候选人的 candidate_ref、分项分数、PRF 词、公司探测数据、站内筛选降级项都留在文件里，用户视图不出现。报告输出后直接进入步骤 16 的方向选择。

## 市场洞察

给猎头的知识沉淀，回答"这个岗位的市场长什么样"。只综合三份已有材料：冻结的需求版本、步骤 3.5 的调研产物（岗位定位、公司类别、目标公司清单）、本次检索的候选人数据（详情字段、评分、PRF 晋升与拒绝记录）。每条结论注明样本量（"5 位可推荐中 4 位……"）。

1. **核心技能**（`skills`）：JD 的必须满足 vs 高分候选人（可推荐及以上）`skills` 与经历原文中的高频技能，并排对照。单独标出两类差异：JD 要求但高分候选人普遍没有的（JD 可能偏离市场），高分候选人普遍有但 JD 没提的（可补进 JD）。PRF 被拒绝的词作为"这个组合在市场上少见"的证据引用。
2. **高分候选人特征**（`profile`）：归纳维度固定为当前 title 分布、工作年限区间、技能组合、项目类型、公司类型、当前城市（受保护属性的排除见 SKILL.md 决策规则）。可推荐不足 3 人时写"样本不足，不做归纳"。
3. **公司来源**（`company_sources`）：高分候选人的当前与过往公司归类，对照步骤 3.5 的结论写命中情况——目标公司几家命中几家、其中探测可用几家、各公司类别出了几人、名单外的公司有哪些。三层对照：调研认为该去哪找、猎聘上实际有多少人（探测召回）、最后从哪找到，三者的差距就是这一节的结论。
