# 目标公司确认

步骤 3.5 主 Agent 在收到调研子 Agent 结果后读取。使用返回的 positioning、categories、companies 和 gaps；核对公司有名称、类别、简短理由、置信度和来源，保留研究置信度。字段缺失时只让原调研子 Agent 补齐已有结论，沿用原搜索预算；网页与搜索过程留在子 Agent。

资料不足时简短说明缺口，用已有公司加“不限”和自定义补充让用户决定；空清单也由用户决定补充公司或不限。随后按以下格式调用 request_user_input。完成标准：选择卡片已成功发出且已收到用户回答，再按回答建立公司池并进入步骤 4；仅准备好参数或输出“等待选择”仍未完成，卡片成功发出后才等待用户。

## 提问格式

一道多选题，选项按**推荐顺序**排列：第一排序键是分量（公司大、人多、候选人多），第二排序键是方向匹配。最多 7 家公司 + 固定一项"不限"，共 ≤ 8 个选项；allow_custom=true 供用户补充公司。

每家公司一个选项：label 是 `公司名 · 类别`，前三家写成 `[推荐] 公司名 · 类别`；description 是一句话理由，回答"为什么从这家找"——大概有多少人做这个岗位、方向匹配的依据是什么（"在 [城市] 有 200 人的 Agent 平台团队，近期在招同岗位"）。置信度留在决策记录里，选项上以理由代替数字。

## 最小调用示例

以下 JSON 是 request_user_input 的参数对象。保持结构和简短 prompt，按上述规则将示例公司选项替换为实际调研结果，保留“不限”；公司理由只写在各选项的 description。recommended 省略时默认为 false。

```json
{
  "skill_name": "wts",
  "step_id": "confirm-target-companies",
  "title": "确认目标公司范围",
  "reason": "JD 未指定目标公司，需要确认寻访范围。",
  "questions": [{
    "id": "target_companies",
    "type": "multiple_choice",
    "prompt": "您看从哪些公司找？可以多选，也可以补充。",
    "allow_custom": true,
    "options": [
      {"label": "[推荐] 示例公司 · 类别", "description": "根据实际调研填写一句推荐理由。"},
      {"label": "不限"}
    ]
  }]
}
```
