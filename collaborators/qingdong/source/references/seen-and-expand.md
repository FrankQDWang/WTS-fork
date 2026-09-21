# 已看台账与轮内扩张

步骤 1、10、11.5 读。台账回答"谁的详情已经打开过"，扩张回答"这一轮效果好时，再从同一页多看谁"。两者都不改变轮次结构：每轮仍是主路径 5 份、第二路 3 份详情。

## 已看台账

路径：`<TASK_WORK_DIR>/wts/seen.json`。它是"已打开详情"的唯一事实来源；评分去重、搜索计划的 `exclude_candidate_refs`、扩张挑人都从它读。

```json
{
  "merged_from": ["/ABSOLUTE/PREVIOUS_TASK_WORK_DIR/wts/seen.json"],
  "entries": [
    {
      "candidate_ref": "liepin:a1b2c3d4e5",
      "iteration": 1,
      "expansion": 0,
      "section": "details.primary",
      "result_ref": "result://TASK_ID/<sha256>",
      "detail_status": "matched",
      "opened_at": "2026-09-21T03:00:00Z"
    }
  ]
}
```

| 字段 | 内容 |
| --- | --- |
| `merged_from` | 从上一次寻访合并进来的台账路径；本次新建时为空数组 |
| `candidate_ref` | 与详情结果里的 `candidate_ref` 逐字一致 |
| `iteration` / `expansion` | 首次打开所在的轮次；常规轮 `expansion` 为 0，扩张为 K |
| `section` | `details.primary` / `details.secondary` / `details.expand` |
| `result_ref` | 打开它的那次运行的结果引用；评分条目的 `detail_ref` 直接用它 |
| `detail_status` | 详情硬筛状态 `matched` / `unknown` / `rejected`，采集失败写 `failed` |
| `opened_at` | 运行结果的 `finished_at` |

写入规则：

- **步骤 10 读完结果立刻追加**。`details.*` 里每个人一条，`failures.*` 里每个人也一条（`detail_status: failed`）。已在台账里的 candidate_ref 不重复追加，也不改写首次记录。
- **失败可重开一次**。`failed` 的人在下一轮不放进 `exclude_candidate_refs`；第二次仍失败就放进去，不再重开。
- **rejected 也算已看**。详情硬筛淘汰的人已经有详情，不需要再打开；需求版本变化后从 `result_ref` 重读详情重评，而不是重新打开页面。
- **跨任务合并**。步骤 1 发现对话历史里有上一次寻访报告的 `seen_ledger_path` 时，把那份台账的 `entries` 全部并入本次，`merged_from` 记下来源。合并进来的人同样进 `exclude_candidate_refs`。
- **每次寻访结束**，台账路径写进 `report.json` 的 `seen_ledger_path`（`references/final-report.md`）。

## 排除已看的人

第 2 轮起、或本次合并了上一次的台账时，`iteration-N.json` 的 `exclude_candidate_refs` = 台账里全部 candidate_ref（`failed` 且只失败过一次的除外）。Builder 把它编译成卡片谓词，命中的卡片在硬筛阶段被拒绝，理由记 `already_seen`，不占详情预算。这样每轮固定的 5 份和 3 份详情自然落到没看过的人身上。

结果里 `candidates.<path>` 中 `card_hard_filter_reasons` 含 `already_seen` 的卡片数就是"因已看被跳过"的人数，进 `coverage.skipped_seen`，播报里可以说"这一页有 X 位上次已经看过，直接跳过了"。

## 轮内扩张

### 触发

步骤 11 评完本轮新人后，按 `references/scoring.md` 的**扩张门**判断：本轮新人里可推荐占比 ≥ 50%，或本轮新增强匹配 ≥ 2，且尚未成强池。达到即扩张，而不是进下一轮；未达到照常走步骤 12。

扩张完成、评完扩张新人后再判断一次：仍达标且本页还有值得看的人，可以再扩一次；同一轮最多 3 次。扩张不计入轮次预算，也不改变"最大轮次 = min(轮次预算, 3)"。

停止扩张的三种情况：扩张门不再成立；本页没有值得挑的卡片了；当天累计打开的详情已达风控上限（默认 60，可由任务上下文覆盖）。第三种要播报原因。

### 挑人

Agent 从达标那条查询的 `candidates.<path>` 卡片里挑，卡片带公司、职位、年限、城市、学历、技能摘要和卡片硬筛状态。三条规则：

1. **不全开**。一次挑 5–10 人。先挑 `card_hard_filter_status` 为 matched 的，再挑 unknown；rejected 和台账里已有的一律不挑。
2. **按刚评完的人学**。本轮强匹配和可推荐的人在卡片上呈现什么共性（公司类型、职位写法、年限区间、技能词），优先挑符合这个共性的卡片；和本轮低分候选人长得像的往后放。
3. **理由进决策记录**。每个被挑的 candidate_ref 一句依据（"同为大厂平台部门、职位写 Agent 平台"）；没被挑的不用写。

两路都达标时分别写两份扩张计划（K 递增），先扩主路径。

### 执行

按 `references/search-plan.md` 的扩张计划契约写 `iteration-N-expand-K.json`，编译：

```
python "/ABSOLUTE/BUILTIN_SKILLS_DIR/wts/scripts/build_workflow.py" expand --task-id TASK_ID --iteration N --expansion K --task-work-dir "/ABSOLUTE/TASK_WORK_DIR" --plan-file "/ABSOLUTE/TASK_WORK_DIR/wts/search-plans/iteration-N-expand-K.json"
```

调用一次 browser_run_workflow，读 `details.expand`（同步骤 10 的读法），追加台账，只对新人评分（同步骤 11，`detail_section` 写 `details.expand`，`scored_iteration` 写 N），再回到"触发"判断是否继续。扩张评出的人和常规轮的人一起进下一轮的 `decision_basis.candidate_scores`，也一起参与 Top 10、PRF 种子和目标公司池扩充。

### 播报

扩张前："这轮开出来的人质量不错，我再从这一页挑 N 位打开看看，预计 X 分钟，期间不会有新消息。"扩张后并入步骤 11 的播报口径：本次扩张看了几人、新增几位可推荐、几位强匹配。挑人依据、candidate_ref、扩张次数留在决策记录里。
