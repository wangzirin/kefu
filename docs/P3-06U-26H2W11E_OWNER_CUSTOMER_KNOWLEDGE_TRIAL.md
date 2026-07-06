# H2W-11E 负责人真实登录逐页试用验收

## 定位

H2W-11E 是 H2W-11D 之后的负责人真实登录试用验收片。它不新增真实渠道外发、不调用真实模型、不使用真实客户原始数据，也不把本地确认记录写成正式电子签章、正式验收或合同签收；真实外发继续关闭，本片不是正式客户验收。

本片要证明一件事：负责人从登录页进入系统后，可以按客户能理解的路径完成知识维护主链路的逐页试用，并且页面上的关键入口不是空按钮、不是重复看板、不是只画流程卡。

## 本片覆盖范围

1. 负责人真实登录。
   - 脚本创建临时本地租户和首任负责人账号。
   - 通过登录表单提交租户、邮箱和密码。
   - 不使用当前浏览器登录态，也不注入 `localStorage` token 伪造登录。

2. 知识库运营页。
   - 进入 `#knowledge`。
   - 检查“知识维护总流程”存在。
   - 检查 `整理资料 -> 检查 -> 导入 -> 启用 -> 复测 -> 确认` 对应的客户可理解路径。
   - 点击“生成资料包”。
   - 点击“检查资料包”。
   - 点击“导入知识库”。
   - 验证页面展示检查和导入结果。
   - 通过后端 API 读取同一租户的业务对象、知识文档和评测集，证明服务端落库。

3. 知识评测中心。
   - 进入 `#evals`。
   - 检查“知识评测中心”可达。
   - 检查页面仍明确说明：知识评测不是完整线上客服准确率。

4. 质量诊断与客户质量报告。
   - 进入 `#quality`。
   - 检查“质量诊断”和“客户可读质量报告”可达。
   - 检查确认边界仍说明：本地确认不是正式验收，也不是正式电子签章。

5. 知识缺口页。
   - 进入 `#gaps`。
   - 检查知识缺口、补知识和回归路径可达。

## 验收命令

```bash
python3 scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.py
backend/.venv/bin/pytest backend/tests/test_p3_06u_26h2w11e_owner_customer_knowledge_trial.py -q
node scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.mjs
```

## 证据输出

浏览器验收输出目录：

```text
output/p3_06u_26h2w11e_owner_customer_knowledge_trial/
```

核心证据：

- `summary.json`
- `01-knowledge-publish-path-before-clicks.png`
- `02-knowledge-after-convert.png`
- `03-knowledge-after-preview.png`
- `04-knowledge-after-import.png`
- `05-evaluation-page.png`
- `06-quality-report-page.png`
- `07-knowledge-gap-page.png`
- `backend.log`
- `frontend.log`
- `chrome.log`

`summary.json` 必须包含：

- `owner_login_performed_through_ui=true`
- `demo_mode_used=false`
- `customer_publish_path_actions_checked=true`
- `customer_publish_path_clicked_through_ui=true`
- `server_persistence_verified=true`
- `external_platform_write_performed=false`
- `real_platform_send_performed=false`
- `model_call_performed=false`
- `formal_customer_signoff_performed=false`
- `real_customer_data_used=false`

## 停止门禁

出现任一情况，本片不能通过：

- 登录不是通过真实登录表单完成。
- 知识维护总流程的动作按钮只有图标、没有文字、不可见或无法点击。
- 点击“生成资料包 / 检查资料包 / 导入知识库”后没有页面结果。
- 前端显示已导入，但同一租户后端查不到业务对象、知识文档或评测集。
- 页面出现“全平台已接通”“真实外发已开启”“正式电子签章已完成”“合同签收已完成”等越界表达。
- 质量报告页把本地确认写成正式电子签章或正式客户验收。
- 知识评测页把检索命中率写成完整线上客服准确率。
- 浏览器运行出现前端运行时异常。
- 验收脚本依赖用户当前浏览器、当前端口或当前登录态。

## 本片不做

- 不接企业微信、公众号、抖音、淘宝、京东、拼多多真实渠道。
- 不启用真实平台外发。
- 不启用 RPA 自动发送。
- 不调用真实大模型供应商。
- 不上传真实客户原始题库。
- 不生成正式电子签章。
- 不做移动端验收。

## 下一步

H2W-11E 通过后，可以进入 H2W-11F：前端客户术语和页面去重的最后收束，重点看客户知识维护入口、质量报告入口、知识评测入口是否还有重复流程或内部工程词残留。
