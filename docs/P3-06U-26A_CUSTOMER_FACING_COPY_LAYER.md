# P3-06U-26A 对外界面去演示味与文案分层

日期：2026-07-02  
阶段来源：`P3-06U-26_ENGINEERING_OPTIMIZATION_MASTER_PLAN.md`  
阶段性质：前端客户视角口径收束  
真实外发：继续关闭

## 1. 本片目标

P3-06U-26A 只处理一个问题：客户或试点人员进入中台时，不应该在主界面看到“演示模式、演示样本、开发演示身份”这类研发口径。

本片不改变业务能力，不打开真实平台，不接真实客户数据，不修改后端状态机。

## 2. 本轮完成

### 2.1 公共状态口径

新增公共口径常量：

- `PREVIEW_DATA_LABEL = "样例数据"`
- `REAL_DATA_LABEL = "真实服务端数据"`
- `EXTERNAL_WRITE_OFF_LABEL = "真实外发关闭"`

这些常量进入 `WorkspaceState.tsx`，用于状态条、数据来源标签和外发边界标签。

### 2.2 登录页口径

登录页做了三处收束：

- 原本偏研发的本地研究说明，改为“可以使用测试入口快速查看工作台；正式账号请填写租户、邮箱和密码。”
- “本地测试进入”改为“测试账号进入”。
- “开发演示进入”改为“预览工作台”。

按钮保留 `data-role-smoke` 标识，方便后续浏览器验收脚本不再依赖中文按钮文案。

### 2.3 连接状态与客户主界面

主界面中的旧口径统一替换：

- “演示样本”改为“样例数据”。
- “演示模式”改为“预览工作区”。
- “开发演示身份”改为“预览身份”。
- 样例渠道、样例会话、样例工单、样例题库继续保留，但不再使用研发式“演示”口径。

### 2.4 保留真实外发边界

本片没有把“真实外发关闭”去掉。

原因：这是安全边界，不是演示味。客户可以少看到研发字眼，但必须知道系统当前不会向真实平台自动发送。

## 3. 涉及文件

| 文件 | 改动 |
| --- | --- |
| `frontend/src/components/common/WorkspaceState.tsx` | 新增公共文案常量，统一状态条和禁用原因口径。 |
| `frontend/src/App.tsx` | 替换登录页、连接卡、样例数据、知识/评测/运维样例种子的客户可见口径。 |
| `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx` | 对话台复用 `PREVIEW_DATA_LABEL`，禁用原因改为预览工作区。 |
| `frontend/src/components/channels/ChannelConnectorCenterPanel.tsx` | 渠道中心复用统一状态标签。 |
| `frontend/src/components/quality/QualityReviewPanel.tsx` | 质量复盘复用统一状态标签。 |
| `scripts/check_p3_06u_26a_customer_facing_copy.py` | 新增静态门禁，防止中文“演示”口径重新进入前端源码。 |

## 4. 验收

本片验收命令：

```bash
.venv/bin/python scripts/check_p3_06u_26a_customer_facing_copy.py
cd frontend && npm run typecheck && npm run build
```

只读扫描预期：

```bash
rg -n "演示模式|演示样本|开发演示身份" frontend/src
```

预期无输出。

## 5. 停止条件

如果后续出现以下情况，必须先停止继续加功能，回到本片修正：

- 客户主界面重新出现“演示模式、演示样本、开发演示身份”。
- 为了看起来正式而移除了“真实外发关闭”边界。
- 预览工作区被文案写成正式接通真实平台。
- 浏览器验收脚本继续依赖中文按钮文案，而不是稳定的 `data-role-smoke`。

## 6. 不做事项

- 不打开真实外发。
- 不新增真实渠道配置。
- 不调用真实模型。
- 不修改客户账号权限。
- 不导入真实客户数据。
- 不把预览工作区写成正式生产链路。

## 7. 下一步

完成 P3-06U-26A 后，下一片建议进入 `P3-06U-26B`：多渠道对话台进一步微信式收束，让首屏更像真实客服对话，而不是工程解释面板。
