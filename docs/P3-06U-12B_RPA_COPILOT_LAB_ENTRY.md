# P3-06U-12B RPA 副驾驶实验入口

日期：2026-07-02

## 1. 本片结论

本片没有把 RPA 副驾驶直接塞进现有多渠道对话台，而是做成隔离实验入口：

```text
#rpa-lab
```

原因：

- 现在仍是内部研究，不应污染已收束过的接待台主界面。
- 只在 Codex 命令行里试，无法评估未来坐席是否看得懂策略结果。
- 最稳路径是“后端策略服务先可复用，前端实验页可删除”。

如果后续验证它成为核心能力，保留的是：

```text
后端策略试算/决策服务
```

可以隐藏或删除的是：

```text
RPA 副驾驶试验页
```

主中台以后只需要在多渠道对话台、质量复盘、知识缺口等页面调用同一套策略服务。

## 2. 已新增能力

### 2.1 后端 API

新增接口：

```text
POST /api/rpa-copilot/strategy-dry-run
```

特点：

- 需要正式登录。
- 需要 `conversation.read` 权限。
- 不写数据库。
- 不建会话。
- 不创建 outbox。
- 不触发 worker。
- 不读取平台账号。
- 不执行真实外发。

请求字段：

| 字段 | 说明 |
|---|---|
| `channel` | 研究渠道，例如人工导入、千牛研究、拼多多研究 |
| `customer_name` | 客户展示名 |
| `text` | 人工粘贴的客户消息 |
| `attachments` | 仅记录是否有附件，不做自动视觉判断 |
| `metadata` | 实验来源标记 |

返回字段：

| 字段 | 说明 |
|---|---|
| `draft` | 回复草稿 |
| `guardrail` | 风控状态和转人工原因 |
| `reply_strategy` | 意图、回答模式、动作模式、下一步动作 |
| `actions` | RPA dry-run 动作计划 |
| `audit` | 外发关闭、未落库、未自动发送等审计字段 |

### 2.2 前端实验页

新增入口：

```text
实验室 -> RPA副驾驶试验
```

可见角色：

```text
owner / admin / agent
```

页面能力：

- 人工粘贴客户消息。
- 选择研究渠道。
- 标记是否包含附件。
- 运行策略试算。
- 展示填草稿、人工接管或补知识三类结果。
- 展示草稿、引用、风控原因、质量信号和动作计划。
- 一键复制草稿。

页面明确显示：

```text
本页只做人工粘贴消息后的回复策略试算；不读取平台账号、不保存客户消息、不点击发送。
```

## 3. 本片关键文件

```text
backend/app/schemas/rpa_copilot.py
backend/app/services/rpa_copilot.py
backend/app/api/rpa_copilot.py
backend/app/main.py
backend/tests/test_p3_06u_12b_rpa_copilot_api.py
frontend/src/api/client.ts
frontend/src/components/rpa/RpaCopilotLabPanel.tsx
frontend/src/data/navigation.ts
frontend/src/App.tsx
frontend/src/styles.css
scripts/check_p3_06u_12b_rpa_copilot_lab_entry.py
```

## 4. 工程边界

本片不做：

- 真实平台登录。
- 真实平台消息抓取。
- 浏览器或桌面 RPA 自动观察。
- 自动填真实平台回复框。
- 自动点击发送。
- Cookie、Token 或私有协议复用。
- 将消息保存到正式会话库。

## 5. 验证结果

已验证：

```text
backend/.venv/bin/pytest -q backend/tests/test_p3_06u_12b_rpa_copilot_api.py backend/tests/test_ai_rpa_closed_loop_research.py
python3 scripts/check_ai_rpa_closed_loop_research.py
npm run typecheck
npm run build
```

其中：

- 后端策略接口测试通过。
- 研究 dry-run 仍保持 `external_write_performed=false`。
- 前端类型检查通过。
- 前端构建通过。

## 6. 下一步

下一步可以做 P3-06U-12C：

```text
把策略结果嵌入多渠道对话台，但不展示实验表单。
```

具体方式：

- 当前实验页继续保留为内部验证工具。
- 多渠道对话台只展示当前会话的策略结果摘要。
- 后端统一调用同一个策略服务。
- 如果未来官方渠道或 RPA 观察层进入，只替换消息来源，不重写策略逻辑。
