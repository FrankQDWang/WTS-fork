# WTS Skill 多版本测试仓库

这个仓库用于开发 WTS Skill、发布可独立测试的冻结版本，并用一组可重复使用的岗位 JD 比较不同版本的实际表现。

核心目标不是让 Agent 复现唯一的“标准搜索路径”，而是同时观察：

- 是否正确理解岗位并遵循 WTS 的关键要求。
- 是否在需求澄清、公司研究、搜索调整和候选人判断中产生有价值的智能涌现。
- 不同 WTS 版本在同一 JD 上的行为和结果有何差异。

## 目录结构

```text
WTS/
├── README.md
├── source/                         # 正在开发的 WTS Skill
│   ├── SKILL.md
│   ├── agents/
│   ├── assets/
│   ├── references/
│   └── scripts/
├── test-cases/                     # 跨版本复用的 JD Benchmark
│   └── case-001-system-architect.md
└── versions/                       # 已发布的冻结测试版本
    ├── wts-v0-1/
    ├── wts-v0-2/
    └── wts-v0-3/
```

## 各目录的职责

### `source/`

`source/` 直接是一个完整的 Skill 目录，不再增加 `wts/` 中间层。日常开发和 PR 评审在这里进行。

### `versions/`

当某个状态值得进入真实测试时，将完整 Skill 发布为 `versions/wts-v0-N/`。

- 每个版本都必须可独立安装。
- 版本内的 Skill 行为文件发布后原则上冻结。
- `conversations/` 可以继续追加真实测试记录。
- 行为调整应该发布为新版本，不原地改写旧版本。

### `test-cases/`

`test-cases/` 保存全部 WTS 版本共用的岗位 JD。每个 Markdown 同时记录冻结输入和人工评估参考。

运行测试时，**只能把“测试输入”边界中的 JD 提交给 Agent**。“测试目的”、“关键观察点”、“成功信号”和“失败信号”只供测试者复盘，不得泄露给被测 Agent。

Case 采用弱约束观察：不预设具体搜索词、轮数、候选人或唯一正确路径，避免抑制 Agent 的有效探索。

## 如何使用

### 1. 开发 Skill

在 `source/` 中修改 Skill，通过 branch 和 Pull Request 进行评审。

### 2. 发布测试版本

从审核过的开发状态创建 `versions/wts-v0-N/`，同步版本身份、斜杠命令、任务工作目录和 Builder 身份，并在 `CHANGELOG.md` 中说明变化。

### 3. 注入 Domi Dev

测试版本安装到 Domi Dev 的用户 Skill 目录：

```text
~/Library/Application Support/Domi Dev/deepagent/skills/
```

每个版本必须使用带版本号的独立身份，例如：

```text
wts-v0-2 / WTS 0.2 / /wts-v0-2
```

不得把版本包覆盖到 `test`，也不得覆盖已安装的其他版本。目标版本已存在时，先确认再处理。

### 4. 选择 JD 并运行

选择 `test-cases/` 中的一份 Case，记下 `case_id` 和 `revision`，只向待测 WTS 提供其“测试输入”。

### 5. 回收真实会话

每次运行在相应版本的 `conversations/` 中归档三个文件：

```text
case-NNN.md         # 可读原稿
case-NNN-review.md  # SOP 和智能涌现复盘
case-NNN-raw.md     # 脱敏原始轨迹
```

三个文件通过以下元数据指向同一份 JD：

```yaml
test_case_id: jd-case-001
test_case_revision: 1
```

JD Case 本身不记录每次运行历史，避免每次测试都回写和修改冻结输入。

### 6. 复盘与比较

复盘时先检查 SOP 是否遵循，再单独评价是否出现有价值的新判断、新路径或市场洞察。对于没有可观测证据的环节，标记“无法观测”，不用隐藏推理补齐。

## 隐私与本地文件

进入 GitHub 前，必须遮盖候选人姓名、电话、邮箱、详情链接、Cookie、Token 和其他凭证。

以下内容留在 WTS 仓库外：

- 项目操作者的本地 `Agent.md`。
- Domi Dev 数据库和 `domi-session-export/` 中间导出。
- 未脱敏的会话、候选人信息和其他不适合公开的资料。
