# 权威JSON字段规范

`JSON-Schema.json` 校验内部双语资产。`dimensions` 只存解析状态及原因，所有可执行规则集中在 `rules`，避免 core_dna 与 visual_systems 重复维护。四个输出版本从规则列表筛选生成；视觉维度和基因分类通过规则ID映射，不另造相互冲突的规则文本。

| 字段 | 说明 |
|---|---|
| schema_version / style_id / version | 协议、资产及版本 |
| sources | 参考证据源；真实来源不可虚构 |
| dimensions | 24维状态与原因 |
| rules | 唯一规则列表，包含双语文本和证据 |
| rule_id / dimension / gene_type | 规则ID、维度、基因类别 |
| instruction / allowed_variation | 执行指令和容许范围 |
| condition | 类别与复杂度条件，两项均须满足；空数组表示不限 |
| priority | 1–100，同类规则按降序排列 |
| confidence / validation | 定性置信度与验证要求 |

结构校验之外还必须检查ID唯一、引用有效、核心存在且无条件、analyzed维度有非free规则、unknown/not_applicable无规则、存在通用adaptive回退。候选、实验中、示例可用于测试，但不得对外标记已验证。JSON字段不会自动使模型遵守规则；模型适配层负责转成其实际可接受的输入。

## 中英字段映射
中文输出使用中文键名和中文内容；英文使用英文键名和英文内容。两者共用 rule_id、资产ID、优先顺序、条件选择结果。规则允许范围也须在长短文本中表达。机器可验证ID覆盖，但语义翻译仍需人工校验。
