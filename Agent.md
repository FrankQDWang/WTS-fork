# WTS Skill 多版本协作与调试方案

## 一、背景

WTS 是一个持续迭代的 Agent Skill。不同产品经理可能会同时尝试不同的指令、流程、脚本和配套资源，并希望将其中某个版本注入自研 Agent 进行真实调试。

当前需要解决的核心问题是：

1. 多人如何共同开发 WTS，而不互相覆盖。
2. 如何把某个可测试版本作为完整文件包注入 Agent。
3. 如何让多个 WTS 版本同时出现在 Agent 前台，并通过不同斜杠命令分别触发。
4. 如何把 Agent 调试过程中产生的真实对话取回，归集到对应版本。
5. 如何利用积累的真实对话，让 AI 比较不同版本并辅助后续迭代。

## 二、方案目标

建立一套简单、可追溯的 WTS 多版本协作机制：

- GitHub 仓库同时保存开发中的 WTS 和已经发布的测试版本。
- 每个测试版本都是一个可独立安装的完整 Skill 文件包。
- 多个版本可以同时注入 Agent，并在前台分别触发。
- 每次真实调试产生的完整对话可以回收到对应版本中。
- 产品经理可以直接以“WTS 0.1、WTS 0.2”等产品版本进行讨论，不必依赖 Git commit 号理解版本。
- 后续可以让 AI 读取各版本的真实对话，分析版本差异和改进方向。

## 三、核心设计

整个体系分为三个对象：开发源、测试版本和真实对话。

### 3.1 开发源

开发源是当前正在编辑的 WTS。产品经理通过 Git branch 和 Pull Request 在这里协作。

开发源可以持续修改，不直接作为稳定测试版本使用。

### 3.2 测试版本

当某个开发状态值得进入 Agent 测试时，将它发布为一个独立版本目录，例如：

- `wts-v0-1`
- `wts-v0-2`
- `wts-v0-3`

每个版本目录包含当时完整的 Skill 文件、脚本、参考资料、图片和其他配套资源，可以独立注入 Agent。

### 3.3 真实对话

版本注入 Agent 后，用户通过前台斜杠命令进行真实调试。调试完成后，由 Codex 或配套工具导出完整对话，并将其追加到该版本的 `conversations/` 目录。

真实对话不是预先编写的测试 Case，而是 Skill 在 Agent 内实际运行后产生的结果。

## 四、建议的仓库结构

```text
WTS/
├── source/
│   └── wts/
│       ├── SKILL.md
│       ├── scripts/
│       ├── references/
│       └── assets/
│
└── versions/
    ├── wts-v0-1/
    │   ├── SKILL.md
    │   ├── scripts/
    │   ├── references/
    │   ├── assets/
    │   ├── CHANGELOG.md
    │   └── conversations/
    │       ├── case-001.md
    │       └── case-002.md
    │
    ├── wts-v0-2/
    │   ├── SKILL.md
    │   ├── scripts/
    │   ├── references/
    │   ├── assets/
    │   ├── CHANGELOG.md
    │   └── conversations/
    │       ├── case-001.md
    │       └── case-002.md
    │
    └── wts-v0-3/
        └── ...
```

如果需要兼容当前仓库结构，也可以先保留 `skills/wts/` 作为开发源，后续再决定是否改名为 `source/wts/`。这一目录命名不影响整体机制。

## 五、版本规则

### 5.1 Skill 文件发布后冻结

一个版本进入 `versions/` 后，其 Skill 内容不再原地修改，包括：

- `SKILL.md`
- `scripts/`
- `references/`
- `assets/`
- 其他会影响 Skill 行为的文件

如果需要调整 Skill，应创建下一个版本，例如从 `wts-v0-2` 创建 `wts-v0-3`。

这样可以保证任何人在不同时间触发 `WTS 0.2` 时，使用的始终是同一套 Skill。

### 5.2 测试对话允许持续追加

版本发布后，`conversations/` 目录可以继续增加新的 Case，但已有对话原则上不覆盖、不重写。

因此版本目录遵循：

> Skill 内容冻结，对话记录只追加。

### 5.3 版本名与前台名称

Skill 的内部名称使用兼容目录和命令的格式：

```yaml
name: wts-v0-2
```

前台显示名可以保持产品化表达：

```text
WTS 0.2
```

对应的斜杠命令为：

```text
/wts-v0-2
```

## 六、多人协作方式

### 6.1 使用 Branch 开发不同方案

每个产品经理可以基于主分支创建自己的实验分支，例如：

```text
main
experiment/company-probe
experiment/jd-clarification
experiment/search-controller
```

分支用于开发和讨论，不直接等于正式版本。

### 6.2 通过 Pull Request 评审

开发者完成一个阶段后提交 Pull Request。PR 用于：

- 展示修改内容。
- 解释为什么修改。
- 让其他产品经理和研发人员评审。
- 决定是否值得生成一个可测试版本。

PR 可以先不合并。只要某个分支状态值得测试，就可以从该状态生成版本包。

### 6.3 发布测试版本

当团队决定测试某个方案时：

1. 从指定分支或提交读取完整 WTS 文件。
2. 创建新的版本目录，如 `versions/wts-v0-3/`。
3. 将完整 Skill 文件包放入版本目录。
4. 编写简短的 `CHANGELOG.md`，说明相对上一版本的主要变化。
5. 将该版本注入 Agent。

Git commit 继续负责记录底层变化；`WTS 0.3` 则作为产品经理和测试人员使用的版本名称。

## 七、Agent 注入与前台触发

### 7.1 Domi Dev 的实际 Skill 目录

Domi Dev 将内置 Skill 和用户安装 Skill 分开管理。

内置 Skill 位于应用资源包：

```text
/Applications/Domi Dev.app/Contents/Resources/extraResources/python/skills/
```

这里保存随应用发布的稳定 Skill。不要把日常测试版本写入该目录，因为应用升级可能覆盖文件，也会把实验版本与产品内置资源混在一起。

用户安装和调试 Skill 的实际目录是：

```text
/Users/chengxia/Library/Application Support/Domi Dev/deepagent/skills/
```

后续所有 WTS 测试版本默认注入这个用户目录，例如：

```text
/Users/chengxia/Library/Application Support/Domi Dev/deepagent/skills/wts-v0-1/
/Users/chengxia/Library/Application Support/Domi Dev/deepagent/skills/wts-v0-2/
/Users/chengxia/Library/Application Support/Domi Dev/deepagent/skills/wts-v0-3/
```

当前已经安装了一个实际验证实例：

```text
/Users/chengxia/Library/Application Support/Domi Dev/deepagent/skills/test/
```

它来自 GitHub 仓库 `FrankQDWang/WTS` 的 `skills/wts`，对外身份已改为：

```text
Skill name: test
显示名称: WTS Test
斜杠命令: /test
Builder version: 0.5.0-test
```

内置 `/wts` 未被修改，测试版 `/test` 与其并存。

### 7.2 注入过程

Codex 接到安装指令后，执行以下动作：

```text
选择 GitHub 中的版本目录
        ↓
检查是否包含有效的 SKILL.md
        ↓
将完整版本文件夹注入 Agent 的 skills 目录
        ↓
通知 Agent 刷新 Skill 列表
        ↓
前台显示新的 WTS 版本
```

例如：

```text
versions/wts-v0-2
→ Agent skills/wts-v0-2
→ 前台出现 /wts-v0-2
```

### 7.3 多版本共存

Agent 的 skills 目录可以同时存在：

```text
skills/
├── wts-v0-1/
├── wts-v0-2/
└── wts-v0-3/
```

用户不需要手动切换文件，也不需要覆盖已有 Skill，只需在前台使用不同命令：

```text
/wts-v0-1
/wts-v0-2
/wts-v0-3
```

这样可以用相同或相似的招聘需求分别测试不同版本。

### 7.4 版本包的 Domi 适配

WTS 版本不能只复制并修改目录名。每个测试版本至少要同步修改：

- Skill 目录名。
- `SKILL.md` 中的 `name`。
- `agents/openai.yaml` 中的显示名和默认斜杠命令。
- `request_user_input` 使用的 `skill_name`。
- `<TASK_WORK_DIR>` 下的版本工作目录。
- `scripts/build_workflow.py` 中的 `SKILL_NAME` 和 `SKILL_VERSION`。
- Skill 内调用 Builder 的路径，使其指向用户 Skill 目录中的当前版本，而不是 App 内置 `wts`。

安装或删除版本后，需要让 Domi 重新扫描 Skills。优先使用前台刷新机制；如果当前版本没有刷新入口，则重启 Domi Dev，再在新任务中检查对应斜杠命令。

### 7.5 注入时携带版本身份

Agent 至少需要知道当前触发的是哪个版本，例如：

```text
skill_name: wts-v0-2
source_repository: FrankQDWang/WTS
source_path: versions/wts-v0-2
```

这组信息用于在测试结束后将对话准确归档到对应版本。

## 八、真实对话回收

### 8.1 回收过程

一次调试完成后：

```text
Agent 产生完整对话
        ↓
用户选择保存本次测试
        ↓
Codex 导出对话原文
        ↓
根据 skill_name 找到对应版本
        ↓
生成新的 case 文件
        ↓
写入该版本的 conversations/
```

例如：

```text
WTS 0.2 的第四次测试
→ versions/wts-v0-2/conversations/case-004.md
```

### 8.2 Case 的三文件格式

每个 Case 由三个 Markdown 文件组成：

```text
case-NNN.md         # 可读原稿
case-NNN-review.md  # 复盘点评
case-NNN-raw.md     # 脱敏后的原始运行轨迹
```

- `case-NNN.md` 保留完整的用户需求和 Agent 最终答复，按阶段整理可观测的交互、关键动作、错误、重试和决策依据。
- `case-NNN-review.md` 把 SOP 遵循情况与智能涌现分开评价，每条判断链回可读原稿的稳定标题。
- `case-NNN-raw.md` 保留导出时 `conversation.md` 中的可观测运行信息，仅移除凭证、隐藏推理和可识别个人的直接链接。

本地 `domi-session-export/<session_id>/messages.json` 是机器可读的查询结果，不作为 GitHub 主要评审产物。

### 8.3 Case 编号

同一版本内按顺序生成：

```text
case-001.md
case-002.md
case-003.md
```

新增对话时只从 `case-NNN.md` 的可读原稿文件计算最大编号并加一，不将 `-review` 和 `-raw` 重复计数。三个文件是同一个逻辑 Case，必须共用 Case 编号和 Session ID。任一文件已出现相同 Session ID 时，不得重复归档。

### 8.4 隐私处理

对话写入 GitHub 前，需要删除或替换：

- 候选人的姓名、电话和邮箱。
- 登录信息、Cookie、Token 和环境变量。
- 不适合进入代码仓库的客户或公司内部信息。

如果 GitHub 仓库是公开的，默认只保存已经脱敏的对话。

### 8.4.1 本地工作区与 GitHub 仓库的边界

```text
技能调试/
├── WTS/                  # Git 仓库，与 GitHub 目录结构一致
└── domi-session-export/  # 本地查询和中间导出，不进入 Git
```

需要同步到 GitHub 的 Skill、文档和三文件 Case 都放在 `WTS/` 内。数据库查询结果、未脱敏原稿和其他中间产物留在外层本地目录。

### 8.5 Domi Dev 会话的读取源

Domi Dev 本地会话的主要读取源是：

```text
/Users/chengxia/Library/Application Support/Domi Dev/deepagent/local-agent-sessions.sqlite3
```

这是普通 SQLite 数据库。导出工具以只读方式访问，不直接修改数据库。

主要使用两张表：

- `local_agent_sessions`：会话 ID、标题、消息数量、创建时间、更新时间和删除状态。
- `local_agent_messages`：用户与 Agent 正文、消息顺序、状态，以及 `extra_metadata` 中的完整运行事件。

`local_agent_messages.content` 保存前台可见的用户和 Agent 原文；`extra_metadata.events` 保存工具开始、工具结束、工具输入输出、完成状态和建议项。

下面两个来源不作为 Conversation 导出的主数据源：

- `root-checkpoints.sqlite3` 主要服务于 LangGraph 的暂停、恢复和运行状态。
- workspace 中的 `.domi/context/.../conversation_history/*.md` 只在部分会话生成，可作为历史副本但不能保证完整覆盖。

因此统一规则是：

> `local-agent-sessions.sqlite3` 是 Conversation 的读取源；版本目录中的 Markdown 是导出和归档结果。

#### 8.5.1 读取最近一次有消息的本地会话

数据库位于应用数据目录下的 `deepagent/local-agent-sessions.sqlite3`：macOS 从 `~/Library/Application Support` 查找，Windows 从 `%APPDATA%` 查找。必须先区分测试版与正式版；无法区分时列出路径交由用户选择，不得自行混用。

直接以只读 URI 连接原数据库，以便同时读取 WAL 中已落盘的数据；不要只复制 `.sqlite3` 主文件：

```python
import sqlite3
from pathlib import Path

conn = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA query_only = ON")
```

先按账号统计未删除的 PC 会话：

```sql
SELECT
  user_id,
  COUNT(*) AS session_count,
  MAX(COALESCE(last_message_at, updated_at, created_at)) AS latest_activity_ms
FROM local_agent_sessions
WHERE is_deleted = 0
  AND source_channel = 'pc'
GROUP BY user_id
ORDER BY latest_activity_ms DESC;
```

只有一个账号时直接使用。有多个账号且不知道当前登录账号时，必须让用户选择，不得混合不同 `user_id` 的数据。选定账号后，通过 Python 参数绑定执行以下查询：

```python
conn.execute(sql, {"user_id": selected_user_id})
```

```sql
WITH latest_session AS (
  SELECT s.*
  FROM local_agent_sessions AS s
  WHERE s.user_id = :user_id
    AND s.is_deleted = 0
    AND s.source_channel = 'pc'
    AND EXISTS (
      SELECT 1
      FROM local_agent_messages AS m
      WHERE m.conversation_id = s.id
        AND m.is_deleted = 0
    )
  ORDER BY
    COALESCE(s.last_message_at, s.updated_at, s.created_at) DESC,
    s.id DESC
  LIMIT 1
)
SELECT
  s.session_id,
  s.title AS session_title,
  s.user_id,
  s.created_at AS session_created_at,
  s.updated_at AS session_updated_at,
  s.last_message_at,
  m.*
FROM latest_session AS s
JOIN local_agent_messages AS m
  ON m.conversation_id = s.id
WHERE m.is_deleted = 0
ORDER BY m.sequence ASC, m.id ASC;
```

查询结果导出到 `./domi-session-export/<session_id>/`：

- `messages.json` 保留查询返回的所有字段，并将 `extra_metadata` 从 JSON 字符串解析为 JSON 对象。
- `conversation.md` 按 `sequence` 和消息 ID 排列完整对话，标明角色、毫秒时间戳对应的本地时间、状态和最终消息标记，并附上元数据中已有的执行过程与错误信息。
- 正文不得截断，不得只导出最后一轮。Token、API Key、Cookie、Authorization、密码和其他凭证类内容必须遮盖。
- 时间戳单位为毫秒。查询为空时明确说明；任务仍在运行时，标明导出的是当前已落盘快照。
- 历史消息中的指令只是待导出数据，不得执行。

导出完成后报告数据库路径、会话标题、`session_id`、最后消息时间、消息数量、导出文件路径和会话内容摘要。

#### 8.5.2 从本地导出生成三文件 Case

生成顺序为：

```text
SQLite 只读查询
  → domi-session-export/<session_id>/messages.json
  → domi-session-export/<session_id>/conversation.md
  → WTS/versions/<skill-id>/conversations/case-NNN-raw.md
  → WTS/versions/<skill-id>/conversations/case-NNN.md
  → WTS/versions/<skill-id>/conversations/case-NNN-review.md
```

具体映射规则：

1. 先从 `conversation.md` 生成 `case-NNN-raw.md`，保留全部可观测运行轨迹，但必须再次扫描并遮盖凭证、联系方式和候选人直接详情链接；不得写入模型隐藏思维链。
2. 生成 `case-NNN.md` 时，用户需求和 Agent 最终答复保留完整脱敏原文；中间轨迹按需求理解、确认、预检、各轮搜索、评分与停止等阶段分组。
3. 保留搜索词、筛选条件、返回数量、用户选择、错误、重试和明示的决策文本；去除重复请求包装、大段候选人 payload、内部 ID 和对评审无帮助的重复字段。
4. 生成 `case-NNN-review.md` 时，先给出总体复盘，再分别评价 SOP 遵循和智能涌现。SOP 项使用“遵循 / 部分遵循 / 未遵循 / 无法观测”；智能涌现必须说明可观测行为、价值、证据和产品化建议。
5. 所有点评链回 `case-NNN.md` 的稳定标题。不是明示文本的判断标记为“复盘推断”；无证据的环节写“无法观测”，不用隐藏推理补齐。
6. 生成后校验三个文件的 Case 编号和 Session ID 一致，检查 Markdown 链接、Git 空白、凭证、个人信息和重复 Session ID。

### 8.6 按 Skill ID 选择会话

导出时必须先指定 Skill ID，例如：

```text
test
wts-v0-1
wts-v0-2
```

新会话应在创建时把 `selected_skill_id` 持久化到会话记录。推荐后续在 `local_agent_sessions` 增加明确字段：

```text
selected_skill_id: test
```

在数据库结构尚未增加该字段时，按以下优先级识别：

1. `local_agent_sessions.selected_skill_id`，如果未来已经增加该字段。
2. 消息 `extra_metadata.selected_skill_id`，如果运行时已经写入。
3. 首条用户消息开头的斜杠命令，例如 `/test`。
4. 无法确认 Skill ID 的会话不自动归档，等待人工选择。

当前旧会话可通过首条用户消息筛选。示意查询：

```sql
SELECT s.id, s.session_id, s.title, s.created_at, s.updated_at
FROM local_agent_sessions AS s
WHERE s.is_deleted = 0
  AND EXISTS (
    SELECT 1
    FROM local_agent_messages AS m
    WHERE m.conversation_id = s.id
      AND m.is_deleted = 0
      AND m.role = 'user'
      AND m.sequence = (
        SELECT MIN(m2.sequence)
        FROM local_agent_messages AS m2
        WHERE m2.conversation_id = s.id
          AND m2.is_deleted = 0
          AND m2.role = 'user'
      )
      AND (
        m.content = '/' || :skill_id
        OR m.content LIKE '/' || :skill_id || ' %'
        OR m.content LIKE '/' || :skill_id || char(10) || '%'
      )
  )
ORDER BY COALESCE(s.last_message_at, s.updated_at, s.created_at) DESC;
```

选定会话后，按 `sequence` 读取全部未删除消息：

```sql
SELECT sequence, role, content, status, is_final, extra_metadata,
       created_at, updated_at
FROM local_agent_messages
WHERE conversation_id = :conversation_id
  AND is_deleted = 0
ORDER BY sequence ASC;
```

首期导出器可以接受：

```text
--skill-id test
--latest
```

表示读取 `test` Skill 最近一次完整会话。也可以显式传入 `--session-id`，避免同一 Skill 有多条会话时选错。

### 8.7 Conversation Markdown 的导出范围

Conversation Markdown 保存完整的可观察运行轨迹：

- 会话与版本身份。
- 用户消息原文。
- Agent 前台回复原文。
- 工具名称、工具输入和工具输出。
- 错误、中断、完成状态和运行耗时。
- Session ID、Request ID、时间和消息顺序。
- Agent 返回的建议项。

下列内容不写入 Markdown：

- `model_activity.reasoning_content` 等模型隐藏推理。
- Token、Cookie、Authorization、环境变量和账号凭据。
- 本地记忆身份哈希等与效果分析无关的内部标识。
- 未脱敏的候选人电话、邮箱和其他个人信息。

归档路径由 Skill ID 直接确定：

```text
versions/<skill-id>/conversations/
├── case-NNN.md
├── case-NNN-review.md
└── case-NNN-raw.md
```

例如：

```text
Skill ID: test
→ versions/test/conversations/case-001.md
```

导出器先从可读原稿 `case-NNN.md` 读取最大 Case 编号，再加一生成三个文件；同一个 `session_id` 已经出现在任一 Case 文件时不得重复写入。

## 九、Benchmark 与 RPA 查询缓存

### 9.1 适用场景

WTS 使用固定 JD 作为 Benchmark，但不同版本会动态拆解关键词、筛选条件和多轮搜索策略，因此无法提前穷举所有 RPA 入参。

测试系统不 Mock Skill 生成关键词和筛选条件的过程。Skill 仍然根据 JD 和每轮结果自主决策；系统只缓存耗时、可能计费的 RPA 查询结果。

核心原则是：

> 保留 Skill 动态决策的自由，对重复的 RPA 查询进行精确缓存和回放。

### 9.2 批次级共享缓存

每次用固定 JD 比较多个 WTS 版本时，创建一个独立的 Benchmark 批次，例如：

```text
benchmark_run_id: jd-agent-engineer-20260916-01
```

同一批次内，所有版本共享查询缓存：

```text
WTS 0.1 生成查询 A
WTS 0.2 生成查询 B
WTS 0.3 也生成查询 A
        ↓
查询 A 只执行一次真实 RPA
        ↓
结果同时供 WTS 0.1 和 WTS 0.3 使用
```

批次内已产生的结果保持不变，使不同版本面对相同的页面数据。需要最新数据时创建新的 Benchmark 批次，不刷新旧批次的结果。

### 9.3 查询指纹与精确命中

RPA 执行前，将操作计划标准化并生成查询指纹。指纹至少包含：

- 平台。
- 账号或数据权限范围。
- 按原始顺序保存的关键词。
- 筛选条件。
- 排序方式。
- 页码和每页数量。

只有查询指纹完全一致时才复用缓存。首期不将“语义相近”的关键词视为相同查询，避免缓存系统自己的判断影响 Skill 版本比较。

### 9.4 多轮动态查询

缓存不要求提前知道所有搜索参数。每个版本仍然按轮运行：

```text
Skill 生成本轮 SearchPlan
        ↓
查询指纹是否命中缓存
        ├── 是：直接回放历史结果
        └── 否：执行真实 RPA 并保存结果
        ↓
结果返回 Skill
        ↓
Skill 根据结果决定下一轮
```

批量测试多个版本时，每轮先归集各版本产生的 SearchPlan，去重后只执行尚未缓存的查询，再把结果分别返回各版本。

### 9.5 两层缓存

缓存分为两类：

1. **搜索结果缓存**：按查询指纹保存候选人卡片、结果数量、分页状态和页面观察时间。
2. **候选人详情缓存**：按平台和候选人 ID 保存详情结果，避免不同查询或不同版本重复打开同一候选人。

缓存中保存的是 RPA 的可观察结果，不替代 Skill 自己的评分、反思和下一轮决策。

### 9.6 过期规则

建议按使用场景设置有效期：

| 场景 | 缓存规则 |
| --- | --- |
| 同一次 Benchmark | 批次内始终有效，不自动刷新 |
| 当天反复调试 | 有效期 6–24 小时 |
| 普通开发回归 | 有效期 1–3 天 |
| 最终上线验证 | 不读取缓存，执行真实 RPA |

缓存结果需要记录生成时间。缓存过期后不直接删除历史记录，而是在新批次中重新执行真实 RPA。

### 9.7 三种调试模式

- `plan-only`：只生成 SearchPlan，不提交 RPA 表单。用于快速检查 JD 拆解、关键词和筛选逻辑。
- `cached-rpa`：完整运行 Skill，优先回放批次缓存，只对新查询执行真实 RPA。用于日常多版本 Benchmark。
- `live-rpa`：不读取旧缓存，全部执行真实页面操作。用于最终候选版本和上线前验证。

### 9.8 Benchmark 记录

每次批量测试至少记录：

```text
计划查询数
去重后查询数
真实 RPA 次数
缓存命中次数
缓存命中率
节省的 RPA 次数和时间
```

候选人质量仍然通过不同版本找到的人、候选人重合度、可推荐人数和人工或 AI 评审判断。Benchmark 不预先规定 Skill 必须拆出哪些固定关键词。

## 十、AI 分析方式

对话积累后，可以让 AI 直接读取一个或多个版本的 `conversations/` 目录。

典型分析任务包括：

- 总结 WTS 0.2 在真实调试中的主要问题。
- 比较 WTS 0.1 和 WTS 0.2 的澄清过程。
- 判断哪个版本更容易重复提问。
- 找出哪些 Case 没有完成需求确认。
- 比较不同版本的用户体验和任务完成情况。
- 根据多个 Case 提出 WTS 0.3 的修改建议。

首期分析可以按需发起，不需要预先建设自动评分系统。

## 十一、最小产品能力

自研 Agent 和 Codex 首期只需要支持五个动作：

### 11.1 发布版本

从开发源或指定分支生成新的 WTS 版本目录。

### 11.2 注入版本

将指定版本的完整文件包安装到 Domi Dev 的用户 Skill 目录：

```text
/Users/chengxia/Library/Application Support/Domi Dev/deepagent/skills/
```

不要把测试版本安装到 `/Applications/Domi Dev.app` 内部资源目录。

### 11.3 刷新并触发

让多个 WTS 版本同时出现在前台，并支持独立斜杠命令。

### 11.4 回收对话

按指定 Skill ID 从 Domi Dev 的 `local-agent-sessions.sqlite3` 读取会话；支持选择最近一次会话或指定 Session ID。将脱敏后的用户消息、Agent 回复和工具轨迹导出并追加到对应版本的 `conversations/` 目录。

### 11.5 缓存并回放 RPA 结果

按 Benchmark 批次保存搜索结果和候选人详情；相同查询直接回放，只有新的查询才执行真实 RPA。

首期不需要自动评分、复杂测试看板或专门的实验数据库。

## 十二、完整使用流程

```text
产品经理创建实验分支
        ↓
修改 source/wts
        ↓
提交 PR 并完成评审
        ↓
发布为 versions/wts-v0-N
        ↓
Codex 将该版本注入 Agent
        ↓
前台通过 /wts-v0-N 触发
        ↓
选择 plan-only、cached-rpa 或 live-rpa
        ↓
多版本逐轮产生 SearchPlan
        ↓
归集、去重并检查批次缓存
        ↓
只对缓存未命中的查询执行真实 RPA
        ↓
继续完成真实对话调试
        ↓
Codex 回收并脱敏对话
        ↓
保存为 conversations/case-NNN.md
        ↓
AI 读取多个 Case 或多个版本进行比较分析
        ↓
形成下一版本的改进方向
```

## 十三、方案结论

这套方案把 WTS 看成一个可以持续发布和积累真实使用证据的产品：

- Branch 和 PR 服务于多人开发协作。
- `source/wts` 保存正在开发的版本。
- `versions/wts-v0-N` 保存可独立注入 Agent 的完整版本包。
- 多个版本可以同时安装，通过不同斜杠命令触发。
- 每个版本的 Skill 内容冻结，真实对话持续追加。
- 固定 JD 的多版本 Benchmark 共享带过期时间的 RPA 查询缓存。
- Skill 的动态关键词和多轮决策不被 Mock，只有重复的 RPA 结果被回放。
- 后续由 AI 基于真实对话比较版本效果并提出改进建议。

它保留了 GitHub 的协作和追溯能力，同时让产品经理能够用直观的产品版本完成 Agent Skill 调试。
