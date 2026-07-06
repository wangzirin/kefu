# H2W-DATA2 真实客户脱敏资料接收目录

把客户回传文件放在本目录，文件名必须固定为：

- `customer_materials_received.csv`
- `customer_trial_questions_received.csv`
- `customer_material_manifest_received.json`

模板文件：

- `customer_materials_real_template.csv`
- `customer_trial_questions_real_template.csv`
- `customer_material_manifest_template.json`

硬边界：

- 不放手机号、邮箱、身份证号、订单号、平台 payload、密钥、token、密码。
- 不放客户真实聊天原文；只放脱敏后的问题和业务负责人确认的期望答案。
- 题库少于 50 条时只能进入资料准备中，不能写成真实客户试跑通过。
- 真实外发继续关闭，本目录只用于本地影子试跑和知识复测。

三份回传文件的用途：

- 知识资料：产品、服务、价格、流程政策、禁用承诺、转人工规则和可引用来源。
- 试跑问题：50-100 条脱敏客户问题、期望答案和期望动作。
- 资料说明：提供人角色、脱敏声明、文件说明，以及真实外发关闭确认。

填写要求：

- 禁用承诺要明确写出不能自动承诺的内容，例如最低价、绝对效果、无条件退款、平台规则外补偿。
- 转人工规则要明确写出需要人工处理的情况，例如投诉、付款异常、售后纠纷、敏感个人信息或资料不足。
- 资料到齐后仍先做本地复测和影子试跑，不代表正式客户签收。
