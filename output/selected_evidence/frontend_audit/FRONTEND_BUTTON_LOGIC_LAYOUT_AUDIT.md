# 前端逐按钮逻辑与排版审计

## 结论

- 审计状态：passed_without_p0_p1
- 前端地址：http://127.0.0.1:5182/
- 后端地址：http://127.0.0.1:8081
- 覆盖页面：13
- 可见控件：288
- 实际点击：47
- 禁用控件：37
- 风险跳过：2
- 本地坐席回复：通过
- 问题数量：0

## 高优先级问题


## 页面按钮清单摘要

- 运营总览 #overview：控件 20，点击 6，禁用 0，风险跳过 0，截图 `01-overview-before.png`、`01-overview-after.png`
- 本地试运行准备 #pilot：控件 26，点击 2，禁用 4，风险跳过 1，截图 `02-pilot-before.png`、`02-pilot-after.png`
- 接待工作台 #live：控件 12，点击 8，禁用 0，风险跳过 0，截图 `03-live-before.png`、`03-live-after.png`
- 联系人中心 #contacts：控件 10，点击 5，禁用 2，风险跳过 0，截图 `04-contacts-before.png`、`04-contacts-after.png`
- 线索跟进 #leads：控件 15，点击 1，禁用 10，风险跳过 0，截图 `05-leads-before.png`、`05-leads-after.png`
- 知识库运营 #knowledge：控件 49，点击 5，禁用 8，风险跳过 0，截图 `06-knowledge-before.png`、`06-knowledge-after.png`
- 知识缺口 #gaps：控件 31，点击 7，禁用 8，风险跳过 0，截图 `07-gaps-before.png`、`07-gaps-after.png`
- 知识评测 #evals：控件 22，点击 2，禁用 3，风险跳过 0，截图 `08-evals-before.png`、`08-evals-after.png`
- 质量复盘 #quality：控件 60，点击 1，禁用 0，风险跳过 0，截图 `09-quality-before.png`、`09-quality-after.png`
- 渠道接入 #channels：控件 19，点击 7，禁用 0，风险跳过 0，截图 `10-channels-before.png`、`10-channels-after.png`
- 自动回复策略 #model：控件 1，点击 1，禁用 0，风险跳过 0，截图 `11-model-before.png`、`11-model-after.png`
- 运维与告警 #ops：控件 1，点击 1，禁用 0，风险跳过 0，截图 `12-ops-before.png`、`12-ops-after.png`
- 账号与本地维护 #settings：控件 22，点击 1，禁用 2，风险跳过 1，截图 `13-settings-before.png`、`13-settings-after.png`

## 解释

- 本地试运行准备：用于看资料导入、知识复测、质量/月报、诊断备份和交付档案是否齐备，不代表正式上线。
- 发送到本地会话：当前不是平台发送，只是把坐席回复写入本地会话记录；正式渠道通过前不得显示可点击的“发送给客户”。
- 客户资料与商机记录：当前按轻量客服资料处理，不替代完整 CRM。

## 证据文件

- Summary：`output/p3_06u_frontend_button_logic_layout_audit/summary.json`
- Button inventory：`output/p3_06u_frontend_button_logic_layout_audit/button_inventory.json`
