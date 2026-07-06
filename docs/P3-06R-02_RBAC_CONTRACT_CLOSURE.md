# P3-06R-02 后端权限契约与前端权限请求收口

日期：2026-07-01

## Engineering Control Card

- Stage: P3-06R-02
- 当前主线阶段: P3-06R 工程性优化、升级、修复计划
- 上一阶段真正完成: P3-06R-01 已完成中台壳层固定和运营总览 BI 第一版；P3-06R-01B 已补齐桌面端右侧工作区独立滚动、移动端自然滚动和浏览器 QA。
- 上一阶段明确没有完成: 没有完成后端权限契约收口、前端按权限请求、坐席一屏闭环、渠道连接器中心和真实外发。
- 本轮要交付的客户可见价值: 让不同角色进入中台后不再因为前端无差别拉取接口而出现一串 403；让试点环境更接近正式权限边界。
- 本轮是否只是评测: 否。
- 本轮不做什么: 不做字段脱敏、不做渠道真实外发、不做新 UI 重构、不接真实企业微信公网回调。
- 外部风险: 无真实外部平台写入；无模型付费调用；不修改生产配置。
- 需要用户授权的动作: 无。
- 验证方式: 后端新增权限合同测试、完整后端测试、前端 typecheck、前端 build。
- 写回文件: 本阶段卡、产品化总控手册、Project_012 执行记录/文件索引/复盘。
- 下一阶段: P3-06R-03 坐席工作台一屏闭环，或先做 P3-06R-04 渠道连接器中心。

## 本轮完成内容

### 1. 后端权限契约收口

- `STANDARD_OPS_DEV_BOOTSTRAP_ENABLED` 已加入配置模板和运行配置。
- 生产/试点模式下，无 token `/api/auth/me` 不再返回开发演示 owner。
- 租户、渠道、联系人 foundation 接口补齐登录与命名权限。
- workflow、人审、reply orchestration、trusted inbound worker 迁到命名权限：
  - `conversation.read`
  - `conversation.manage`
  - `channel.read`
  - `channel.manage`
- 新增 owner/admin/agent/viewer 合同测试，验证未登录、viewer、agent、owner 的边界。

### 2. 前端按权限请求数据

- 新增前端权限 helper，按 `/api/auth/me` 或登录响应里的 `permissions` 快照判断可读模块。
- 登录成功后只刷新当前账号有权读取的资源。
- 顶部“检查连接”不再全量刷新所有模块，而是先刷新当前身份，再按最新权限刷新允许资源。
- 无权限模块被置为明确的“当前账号无权读取此模块，请联系管理员开通权限。”状态，不显示接口错误堆栈。
- 知识文档列表对 agent 只拉 `knowledge.read` 可访问的数据；发布记录、知识缺口和知识评测仍按 `knowledge.manage` 收口，避免 agent 因 publication/evaluation 管理接口触发 403。
- 可信入站 worker 前端动作从 `conversation.manage` 改为 `channel.manage`，普通坐席不能越权运行后台 worker。

## 修改文件

- `backend/app/core/config.py`
- `backend/app/core/rbac.py`
- `backend/app/api/auth.py`
- `backend/app/api/tenants.py`
- `backend/app/api/workflows.py`
- `backend/app/api/inbound_worker.py`
- `backend/app/api/reply_orchestrator.py`
- `backend/tests/test_p3_06r_contract_closure.py`
- `.env.example`
- `frontend/src/App.tsx`

## 验证结果

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/frontend
npm run typecheck
npm run build
```

结果：通过。

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python -m pytest backend/tests/test_p3_06r_contract_closure.py -q
```

结果：3 个测试通过。

```bash
.venv/bin/python -m pytest backend/tests/test_foundation_api.py backend/tests/test_workflows_api.py backend/tests/test_trusted_inbound_worker_api.py backend/tests/test_p3_06n_channel_delivery_rbac.py backend/tests/test_p3_06p_outbox_resource_rbac.py -q
```

结果：17 个测试通过。

```bash
.venv/bin/python -m pytest backend/tests -q
```

结果：173 个后端测试通过。仅保留既有 `StarletteDeprecationWarning`。

## 仍未完成

- 还没有做字段级 allowlist 和脱敏策略。
- 还没有做一次性安装 token、生产账号初始化策略和密码策略。
- 还没有完成坐席一屏闭环的编辑草稿、确认引用、内部备注和发送前确认整合。
- 还没有完成渠道连接器中心的 Webhook URL、密钥引用、最近事件、最近错误和测试入口。
- 还没有做真实外发、真实平台回调公网 smoke、真实 Prometheus/Grafana 和真实告警通知。

## 下一步建议

优先进入 `P3-06R-03 坐席工作台一屏闭环`。原因是权限噪音收口后，坐席主界面仍需要从“能看见会话和草稿”升级为“能在一屏完成审核、改写、引用确认、备注和进入待发送”。
