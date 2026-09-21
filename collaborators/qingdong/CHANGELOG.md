# qingdong Changelog

## 待合并

### 2026-09-21 · 已看台账、跨轮/跨任务去重、轮内扩张

基线：`WTS/source/` 于 origin/main `dda38ba`（Builder 0.5.2）。`source/` 是在该基线上修改后的完整 Skill 包，Builder 版本标识改为 `0.6.0`。

#### 改了什么

- **已看台账 `wts/seen.json`**（新 `references/seen-and-expand.md`）：步骤 10 读完结果后把 details 和 failures 里的每个人追加进台账；它是"详情已打开"的唯一事实来源。步骤 15 把台账路径写进 `report.json.seen_ledger_path`；步骤 1 在用户选了备选方向发起新任务时合并上一次的台账。
- **搜索计划新增 `exclude_candidate_refs`**（`references/search-plan.md`、`build_workflow.py`）：台账里的 candidate_ref 全部写入，Builder 编译为卡片阶段谓词 `already_seen`，命中即 reject，不占详情预算。这样每轮固定的 5 份和 3 份详情自然落到没看过的人身上。第 2 轮起必填。
- **轮内扩张（新步骤 11.5，新 Builder 子命令 `expand`）**：每轮详情数量不变；本轮评分后若达到**扩张门**（`references/scoring.md`：本轮新人可推荐占比 ≥ 50% 或新增强匹配 ≥ 2，且未成强池），就留在本轮从同一页再挑一批人打开，而不是进下一轮。挑谁、挑几个由 Agent 根据规则初筛后的卡片信息自行判断，不规定数量（建议：不全开，挑认为比较可能的，优先与本轮高分候选人相似的；Builder 只设一次最多 30 人的技术上限），写 `iteration-N-expand-K.json`，字段 `query` + `include_candidate_refs` + 照抄本轮的筛选和评分项。Builder 编译为卡片谓词 `selected_for_expansion`（只保留名单内的卡片，详情预算 = 名单长度），并校验 query 必须是本轮已执行的查询之一、hard_filters / semantic_criteria 与已执行计划一致。同一轮最多 3 次，扩张不计入轮次。
- **结果分区新增 `details.expand`**；`decision_basis.py` 的 `detail_section` 放开为 primary / secondary / expand，`candidate_scores` 上限从 25 提到 120（三轮加扩张会超过 25），计划文件和最终评分快照上限从 64 KiB 提到 256 KiB。
- **`executed_plan` 跳过扩张工作流**：扩张工作流带 `expansion=K` 标记，下一轮和 settle 找回本轮计划时忽略它，避免把扩张计划当成本轮搜索计划。
- **终态报告**（`references/final-report.md`）：`coverage` 新增 `expansions` 和 `skipped_seen`；新增 `not_recommended`（看过但没推荐的人数与原因聚合），用户视图只说数量和原因，不列个人。

#### 同批次的策略与可读性改动（只改 SKILL.md 和 references，不涉及 Builder）

- **简历可见性测试与面试核实项**（步骤 2、`requirements-draft.md`、`scoring.md`、`final-report.md`）：通过反事实测试的每条要求再问"猎聘详情的哪个区块能看出来"，答不出来的（顶会论文、绩效、口碑、抗压等）进新桶 `verify_in_interview`，不删除、不评分、不筛选，画像和终态报告里单列提醒用户面试核实。必须满足分只按有证据的条目算，unknown 从分母剔除。
- **年龄要求的转换**（步骤 2、3、决策规则）：年龄仍不参与任何筛选和评分，也不估算；改为标记 [年龄→年限] 进第 4 轮澄清，固定四个选项问真实关切（工作年限 / 职级 / 薪资带宽 / 都不是），选年限就写进 experience_years，来源标"用户确认（由年龄转换）"。
- **播报可读性**（"播报"一节）：列出禁止出现在用户面前的内部名词清单（decision_basis、candidate_ref、PRF、Controller、Builder、证据文本、主锚点等）和白话对照表（主锚点→核心岗位词、强匹配→很匹配……）；Builder/宿主返回的校验提示一律不直接播报，修好就不提；轮次小结改为三句固定填空，杜绝"决策要求不至少"这类残句。
- **沿用旧评分逐字复制**（步骤 11）：carry-forward 上一轮 candidate_scores 时不润色 evidence_summary 等字段，Builder 提示"视为修订"时恢复原文再编译，不向用户解释。

#### 为什么改

- 顶会等简历不会写的条件被放进评分后，要么把人误杀，要么被模型自作主张删掉；现在给它一个明确去处。
- 年龄要求被直接拒绝导致用户诉求丢失；转成年限既合规又保留了业务意图。
- 用户反馈看不懂"证据文本""决策要求不至少""主锚点"，根因是内部名词和工具提示直接漏到了播报里。
- 现有工作流按列表顺序取前 5 / 前 3 张卡片开详情，第 2 轮的前几张往往就是第 1 轮开过的人；同一对话里第二次寻访更是完全不知道第一次看过谁。
- 猎聘首屏 30 张卡片，规则初筛后常剩二十多张；一轮只看 5 个，效果好的时候没有办法在同一页继续深挖，只能换词进下一轮。

#### 对宿主的假设（未验证，用不了再改）

- `data.filter.v1` 支持取反算子 `text.excludes_all`（值不包含 expected 中任何一项即通过）。`exclude_candidate_refs` 依赖它；扩张的 `include_candidate_refs` 只用现有的 `text.includes_any`，不依赖新算子。
- 扩张工作流沿用 `candidate.search` 的 `workflow_type` 和能力声明，只多一个顶层 `expansion` 字段；宿主若拒绝未知顶层字段需要放行。

#### 需要重点测试

1. 第 2 轮的 `exclude_candidate_refs` 是否真的让第 1 轮开过的人不再进详情（看 `candidates.primary` 里 `card_hard_filter_reasons` 含 `already_seen` 的数量）。
2. 扩张：编译是否通过、`details.expand` 是否只含名单内的人、扩张评出的人能否顺利进入下一轮 `decision_basis` 和 settle。
3. 选备选方向发起第二次寻访时，台账是否被合并、第一次看过的人是否被跳过。
4. 一轮内连续扩张两三次后，猎聘是否触发"操作频繁"；台账里当天累计打开数的上限（默认 60）是否合适。

#### 本地验证

- `python3 -m unittest discover -s test-cases/automated -v` 通过（这些测试针对主 `source/`，本次未改主 `source/`）。
- 对 `collaborators/qingdong/source/scripts` 做了临时脚本验证：exclude 谓词编译、非法 ref 拒绝、扩张的 query / 条件漂移拒绝、扩张工作流编译（步骤前缀 `expand-`、`max_items` = 名单长度、`summary.workflow = candidate_expand`）、`executed_plan` 跳过扩张工作流、第 2 轮 `decision_basis` 含 `details.expand` 条目时回执正常。
