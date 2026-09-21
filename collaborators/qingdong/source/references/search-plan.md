# 搜索计划契约

仅在生成或调整猎聘搜索计划时读取本文件。计划文件是 Agent 与 Skill Builder 之间的领域输入，不是浏览器命令。Builder 会拒绝未知字段，并把计划与 Skill 内的渠道资产编译为 `browser.workflow.v1`。

搜索计划轮次允许 1-3。第一轮必须直接创建 `iteration-1.json`，后续轮次依次使用 `iteration-2.json`、`iteration-3.json`。第 N 轮计划的唯一合法路径是：

```text
<TASK_WORK_DIR>/wts/search-plans/iteration-N.json
```

`iteration-0` 只用于 preflight。同一轮修正时原地覆盖同一个 `iteration-N.json`。Builder 会同时校验任务工作目录、1-3 轮次和文件名，不符合即拒绝编译。

第 1 轮只能有主路径。第 2 轮起可以增加第二路；两路查询不能相同。一次编译会把本轮两路连续写进同一份工作流。

## 字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `requirement_version` | string | 从第 1 轮起填写已确认需求版本；同版本条件保持一致 |
| `primary_query` | string | 必填，1-50 字符；主路径自然语言查询，不使用 `OR`、`AND`、`NOT`。可含 1 个公司词（SKILL.md 步骤 3.5） |
| `secondary_query` | string | 可选；第二路自然语言查询，只含锚点和支持词。第 1 轮禁止出现 |
| `site_filters` | object | 猎聘页面可直接设置的筛选条件 |
| `hard_filters` | object | Builder 将其编译为通用 `data.filter` 谓词；先做卡片预筛，再做详情终筛 |
| `semantic_criteria` | object | 给隔离评分用，不编译进页面动作 |
| `decision_basis` | object | 第 2 轮起必填；保存截至上一轮的完整评分、PRF 判定和既定下一步 |
| `limits.max_cards_per_path` | integer | 1-30，默认 30；每路首屏最多抽取的卡片数 |
| `limits.primary_max_details` | integer | 0-5，默认 5 |
| `limits.secondary_max_details` | integer | 0-3，默认 3；没有第二路时视为 0 |
| `exclude_candidate_refs` | string[] | 可选，最多 500 个；已看台账（`references/seen-and-expand.md`）里全部 candidate_ref。Builder 编译为卡片阶段谓词 `already_seen`：命中即 reject，不占详情预算。第 2 轮起和上一次寻访延续时必填 |
| `action_delay_ms` | integer | 800-5000，默认 1200；作为普通操作延迟基准，Builder 生成 ±20% 的浮动值，不由 Agent 逐步等待 |

每路固定只采首屏。同一轮两路之间不去重：第二路可能重开主路径刚开过的人，这种重复由步骤 11 的评分去重吸收。

Builder 把每份详情的 15 秒预算分配到读取列表位置、点击打开、提取详情之前，三段各约 4–6 秒、合计恰好 15 秒；每个候选人分别生成分配，不作为 SearchPlan 可调字段。普通点击原有固定尾延迟被浮动前置等待替代，输入、内容读取和导航后也等待。验证码检测和页面加载轮询不增加延迟。弹窗捕获预算包含前置等待及列表页恢复时间；详情加载和搜索超时保持原值。

`semantic_criteria` 只接受：

- `must_have`：必须满足，最多 20 条
- `nice_to_have`：加分项，最多 20 条
- `exclude_signals`：排除信号，最多 20 条

`decision_basis` 的字段与示例以 Builder 校验为准：`requirement_version`、`completed_iteration`、`candidate_scores`、`prf_decision`、`next_action`。同一需求版本的 `hard_filters` 与 `semantic_criteria` 必须保持一致；只换关键词不能同步改写条件。每条候选人评分保留 candidate_ref、真实 detail_ref、详情分区、首次评分轮次、三维原始分、matches、unknown 和证据说明。纠错或需求版本变化时写 correction_reason，但不改首次评分轮次，也不删除历史候选人。

Builder 会把本轮输入计划写入受工作流摘要保护的 `input_plan`。下一轮及 settle 从已完成工作流恢复真实执行计划；旧 iteration 文件即使被修改，也不作为绕过一致性校验的依据。

## 站内筛选字段

`site_filters` 支持：

- `current_cities`、`expected_cities`: 最多 9 个城市名称或标准编码。
- `experience_years`: 仅支持 `{min:0,max:0}`、`{min:1,max:3}`、`{min:3,max:5}`、`{min:5,max:10}`、`{min:10,max:null}`。
- `education`: 最多一个值，支持本科、硕士、博士/博士后、大专、中专/中技、高中及以下。
- `school_requirements`: 最多一个值，支持 `211`、`985`、`double_first_class`、`overseas`。

策略允许写入但页面没有控件的字段：

- `company`、`work_content`: 写入 `site_filters` 时 Builder 会记 `SITE_FILTER_UNSUPPORTED` 并跳过页面筛选；请同时写入 `hard_filters` 做文本硬筛。

不要写入 `age_range`、`activity_recency`、`job_hop_frequency`。年龄、活跃度、跳槽频率不参与检索或硬筛。

站内筛选只能使用猎聘支持的离散预设。Selector、控件定位、弹窗交互和取值标签由 Skill 渠道资产维护，计划中不得出现 Selector 或点击步骤。不要为了表达 `0-3 年` 等精确范围而选近似预设；把精确条件保留在 `hard_filters`。若站内工作年限不是受支持的预设，Builder 只会在 `hard_filters` 存在完全相同范围时移除该站内条件并返回 warning，否则拒绝计划。

所有站内筛选都采用“失败后继续并上报”：某个字段的页面操作失败时跳过该字段、继续关键词搜索，并把字段、请求值和错误原因写入对应路径的 `search.<path>.unsupported_filters`。站内筛选只是缩小召回范围；同字段若属于硬条件，仍由后续卡片和详情 `data.filter` 执行。

## 硬性过滤字段

`hard_filters` 支持：

- `current_cities`、`expected_cities`、`education`: 字符串数组。
- `experience_years`: `{min,max}`。
- `school_requirements`: 字符串数组，支持 `211`、`985`、`double_first_class`、`overseas`；数组内按“满足任一项”判断。
- `company`、`work_content`: 字符串数组；卡片阶段缺失或未命中记 unknown，详情阶段未命中记不符合。
- `required_keywords.all`: 必须全部命中的关键词数组。
- `required_keywords.any`: 至少命中一个的关键词数组。
- `required_keyword_groups`: 二维字符串数组。组与组之间是 AND，每组内部是 OR。

编译后的顺序固定为：对每一路执行关键词搜索并应用站内筛选，抽取该路首屏最多 30 张卡片，使用卡片已知字段做硬性预筛，只为 `matched` 和 `unknown` 候选人按该路详情预算采集详情，再使用详情字段做硬性终筛。第 2 轮起若有第二路，同一份工作流会接着跑完第二路。所有步骤由一次 `browser_run_workflow` 在模型外连续执行。

卡片上能够明确读到的城市、学历、工作年限等字段可以直接淘汰不符合者。列表摘要没有出现关键词、院校标签或其他可能被页面折叠的信息时只记为 `unknown`，不得提前淘汰。Builder 为卡片和详情分别生成声明式谓词；通用浏览器不理解招聘字段。

用户或 JD 明确声明为硬性的站内条件必须同步写入 `hard_filters`。不要假设站内筛选等同于最终硬筛。

## 探测计划

公司词探测（SKILL.md 步骤 6.5）只在第 1 轮前做一次，计划文件固定为 `<TASK_WORK_DIR>/wts/search-plans/probe-1.json`，编译命令的 `workflow_type` 为 `probe`、`--iteration 1`；Builder 拒绝其他轮次。字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `anchor` | string | 必填，主锚点 |
| `companies` | string[] | 必填，1-3 家、不重复；每家编译为一条查询 `"<anchor> <公司名>"`，合计 ≤ 50 字符 |
| `site_filters` | object | 与搜索计划相同，取自硬性筛选条件 |
| `action_delay_ms` | integer | 同搜索计划 |

没有 `hard_filters`、`semantic_criteria`、`limits`：探测只搜索并抽取首屏卡片（每家最多 30 张），不做硬筛、不采详情。

结果：`summary.workflow` 为 `company_probe`；`summary.paths.company_K` 每家一项 `{company, query, card_count, unsupported_filter_count}`；`search.company_K` 含 `unsupported_filters` 与 `pages`。`summary.recall_threshold` 为 10：`card_count` > 10 可用，≤ 10 不可用。

```json
{
  "anchor": "AI Agent",
  "companies": ["阿里巴巴", "字节跳动"],
  "site_filters": {"expected_cities": ["上海"], "education": ["本科"]}
}
```

## 扩张计划

轮内扩张（SKILL.md 步骤 11.5）在本轮评分达到扩张门之后执行，只重开本轮某一条查询首屏上 Agent 点名的卡片。计划文件固定为：

```text
<TASK_WORK_DIR>/wts/search-plans/iteration-N-expand-K.json
```

N 是当前轮次，K 是本轮第几次扩张（1-3）。编译命令的 `workflow_type` 为 `expand`，带 `--iteration N --expansion K`。字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `requirement_version` | string | 与本轮 iteration-N.json 相同 |
| `query` | string | 必填；必须逐字等于本轮已执行的 `primary_query` 或 `secondary_query`，扩张只重开同一页 |
| `include_candidate_refs` | string[] | 必填，1-30 个、不重复；Agent 从该路 `candidates.<path>` 卡片里挑出要打开的人。Builder 编译为卡片谓词 `selected_for_expansion`：不在名单内即 reject；详情预算 = 名单长度 |
| `site_filters` | object | 照抄本轮计划 |
| `hard_filters` | object | 照抄本轮计划；与已执行计划不一致即拒绝编译 |
| `semantic_criteria` | object | 照抄本轮计划；与已执行计划不一致即拒绝编译 |
| `action_delay_ms` | integer | 同搜索计划 |

没有 `secondary_query`、`limits`、`decision_basis`、`exclude_candidate_refs`。Builder 从 Workflow Store 找回本轮真实执行的计划做一致性校验，本轮没有已完成结果时拒绝编译。扩张工作流的 `iteration` 仍是 N，但带 `expansion=K` 标记，下一轮和 settle 找回本轮计划时会跳过它。

```json
{
  "requirement_version": "v1",
  "query": "AI Agent LangGraph RAG 阿里巴巴",
  "include_candidate_refs": ["liepin:a1b2c3d4e5", "liepin:f6g7h8i9j0"],
  "site_filters": {"expected_cities": ["上海"]},
  "hard_filters": {"expected_cities": ["上海"], "required_keyword_groups": [["AI Agent"]]},
  "semantic_criteria": {"must_have": ["有大模型应用或 Agent 落地经历"], "nice_to_have": [], "exclude_signals": []}
}
```

结果只有一个分区 `expand`：`summary.paths.expand`、`search.expand`、`candidates.expand`、`details.expand`、`failures.expand`；`summary.workflow` 为 `candidate_expand`。评分条目的 `detail_section` 写 `details.expand`，`scored_iteration` 写 N。

## 结果分区

工作流按路径落盘，不要把两路结果混成一个无标记列表：

- `summary.paths.primary` / `summary.paths.secondary`
- `search.primary` / `search.secondary`
- `candidates.primary` / `candidates.secondary`
- `details.primary` / `details.secondary`
- `failures.primary` / `failures.secondary`

卡片和详情会带 `search_path=primary|secondary`。没有第二路时，不要读 `secondary` 分区。

## 示例

第 1 轮只有主路径（主锚点 + 2 支持词 + 公司词）：

```json
{
  "primary_query": "AI Agent LangGraph RAG 阿里巴巴",
  "site_filters": {
    "expected_cities": ["上海"],
    "education": ["本科"]
  },
  "hard_filters": {
    "expected_cities": ["上海"],
    "education": ["本科"],
    "required_keyword_groups": [["AI Agent"], ["LangGraph", "LangChain"]]
  },
  "semantic_criteria": {
    "must_have": ["有大模型应用或 Agent 落地经历"],
    "nice_to_have": ["熟悉 RAG"],
    "exclude_signals": ["纯销售岗"]
  }
}
```

第 2 轮主路径（第 1 轮召回少，Agent 减到 1 支持词并换公司词）+ 第二路：

```json
{
  "primary_query": "AI Agent LangGraph 字节跳动",
  "secondary_query": "AI Agent RAG",
  "site_filters": {
    "expected_cities": ["上海"]
  },
  "hard_filters": {
    "expected_cities": ["上海"]
  },
  "semantic_criteria": {
    "must_have": ["有大模型应用或 Agent 落地经历"],
    "nice_to_have": ["熟悉 RAG"],
    "exclude_signals": ["纯销售岗"]
  }
}
```
