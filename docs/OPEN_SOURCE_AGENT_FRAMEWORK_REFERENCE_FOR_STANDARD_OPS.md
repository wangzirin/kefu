# 开源爬虫与 Agent 框架对标准运营版的工程参考

日期：2026-06-25

来源文档：

- `/Users/ericlee/Desktop/Workspace/Project_022_开源爬虫与Agent框架研究/outputs/开源爬虫与Agent框架代码级解读_2026-06-25.md`
- `/Users/ericlee/Desktop/Workspace/Project_022_开源爬虫与Agent框架研究/outputs/Project_012结合Scrapling与AstrBot工程判断_2026-06-25.md`

本文件用于 Project_012 的 `standard_ops` 后续工程推进。它不是对 LangGraph、Scrapling、AstrBot 的再分发，也不复制这些项目的源码；只整理可借鉴的架构思想、合规边界和下一步落地路线。

## 总结判断

三类开源项目对智能客服系统的价值不同：

| 项目 | 最值得学什么 | 是否适合直接嵌入当前客服系统 | 结论 |
|---|---|---|---|
| LangGraph | 状态图、检查点、人工中断/恢复、重试、流程回放 | 暂不建议 | 学工程思想，先做轻量 workflow/checkpoint 表 |
| Scrapling | 授权网页读取、证据留存、选择器漂移、RAG 入库前清洗 | 不直接接原 MCP，不用 stealth 能力 | 学安全子集，做 allowlist-only 采集层 |
| AstrBot | 生命周期、平台适配器、Provider 管理、插件边界、Dashboard | 不建议直接嵌入，AGPL 风险高 | 学模块边界，用自研实现 |

最关键的判断：这些项目不是“可以直接拿来变成智能客服”的万能底座。它们分别覆盖流程编排、网页采集、多平台机器人 runtime 的局部能力。标准运营版应该吸收它们的设计模式，然后继续坚持自研的租户、权限、审计、知识库、渠道和坐席台主线。

## 可借鉴的一号线：LangGraph

### 适合借鉴

LangGraph 的 `StateGraph` 思想非常适合客服会话和知识入库：

- 每个节点读取共享状态，返回局部更新。
- 流程先定义，再编译成可执行图。
- checkpoint 绑定 thread，用于暂停、恢复、回放。
- interrupt/resume 适合人工审核。
- retry policy 应按节点细分，而不是全局粗暴重试。

对应到智能客服，可以设计为：

```text
入站消息
  -> 意图识别
  -> 知识检索
  -> 模型路由
  -> 生成草稿
  -> 风险判断
  -> 自动发送 / 人工审核 / 转工单
```

### 不建议现在引入的复杂度

- 不直接把完整 LangGraph/Pregel runtime 放进主链路。
- 不复刻 channel_versions、versions_seen、checkpoint_blobs 等内部细节。
- 不先做完整 time-travel UI。
- 不让 retry 覆盖人工审核、权限拒绝或业务拒绝。

### 建议后续自研表

```text
workflow_runs
workflow_checkpoints
workflow_step_attempts
human_review_tasks
workflow_writes 或 outbox
```

这些表可以先用 PostgreSQL JSON 字段保存轻量状态。等会话、知识入库、模型路由稳定后，再考虑更复杂的图执行能力。

## 可借鉴的二号线：Scrapling

### 适合借鉴

Scrapling 最适合支持“授权网页资料采集 + 证据留存 + RAG 入库前清洗”：

- 静态 fetch：抓取公开官网、帮助中心、FAQ、文档页。
- 动态 fetch：静态正文不足时，用浏览器渲染授权页面。
- selector/adaptive：维护抽取规则版本，发现 DOM 漂移。
- crawler engine：限定域名内低频链接发现。
- MCP server 思路：把采集封成受控工具，而不是让模型自由浏览。

### 必须排除

以下能力不进入正式客服系统：

- stealth fetch。
- 反检测、指纹伪装、Cloudflare solver。
- 代理池、账号池。
- 保存密码、cookie、Authorization header、浏览器 profile。
- 绕过登录墙、验证码、风控、付费墙。
- 用于绕过小红书、抖音、淘宝、京东等平台限制。

### 建议后续自研表

```text
knowledge_sources
capture_jobs
page_snapshots
ingestion_candidates
selector_profiles
```

### 推荐最小工具

```text
capture_public_page(source_id, url)
capture_page_evidence(source_id, url)
extract_allowed_links(source_id, seed_url)
preview_ingestion_candidate(candidate_id)
```

所有工具都必须经过：

1. allowlist 校验。
2. robots 校验。
3. rate limit。
4. blocked/captcha/login wall stop。
5. 证据留存。
6. 人工审核后才能进入 RAG。

## 可借鉴的三号线：AstrBot

### 适合借鉴

AstrBot 最有价值的是模块边界，不是代码：

- lifecycle：统一初始化配置、数据库、平台、Provider、知识库、插件、Dashboard。
- Platform Manager：可改造为客服语义下的 `ChannelManager`。
- Provider Manager：可抽象为 chat、embedding、rerank、STT、TTS。
- Plugin Manager：可演化为内部 `ExtensionManager`。
- Dashboard：可参考运行时控制台结构。
- Main Agent Build Config：可转成 `ReplyOrchestratorConfig`。

### 不建议引入

- 不复制 AstrBot 代码、Dashboard UI、插件协议、Adapter 实现。
- 不引入泛机器人平台，例如 QQ、Telegram、Discord、Slack。
- 不引入任意插件热重载、自动 pip install、插件市场。
- 不引入 computer-use、复杂 subagent、Cron 主动任务，除非客服场景已经验证。
- 不把 persona/wake prefix/群聊白名单作为客服主模型。

### AGPL 边界

AstrBot 是 AGPL-3.0-or-later。标准运营版如果是闭源商用或客户交付，不能把它作为可直接复制/修改/嵌入的代码来源。只能学习架构思想，必要时重新实现。

## 对当前 standard_ops 的直接影响

本轮已经推进：

- 前端新增正式登录页。
- 登录成功后保存 bearer token。
- `/api/auth/me` 支持 token 获取真实用户。
- 保留“开发演示进入”作为本地预览路径。
- 用户、角色、团队管理开始进入权限保护：初始化后需要 `owner/admin`。

本轮暂不推进：

- 不做完整 LangGraph 化 workflow 表。
- 不做 Scrapling 采集实现。
- 不做 AstrBot 风格插件系统。

原因：当前基础身份、权限、审计和登录 UI 刚建立，先把主线体验和受保护接口稳定住，再进入 RAG/采集/工作流。

## 后续推荐路线

### P1：登录和权限收口

- 完成登录页错误状态、退出、token 恢复。
- 把更多写接口纳入权限保护。
- 设计租户初始化流程，避免长期保留开放创建能力。
- 审计中记录 actor、resource、payload 摘要。

### P2：轻量工作流底座

参考 LangGraph，但自研简化版：

- `workflow_runs`
- `workflow_checkpoints`
- `workflow_step_attempts`
- `human_review_tasks`

先覆盖客服会话处理和低置信人工审核。

### P3：授权网页知识采集

参考 Scrapling 的安全子集：

- `knowledge_sources`
- `capture_jobs`
- `page_snapshots`
- `ingestion_candidates`

只允许 allowlist 页面，不做 stealth，不做第三方平台绕过。

### P4：运行时管理器

参考 AstrBot 的模块边界：

- `ChannelManager`
- `ProviderManager`
- `KnowledgeManager`
- `ExtensionManager`
- `ReplyOrchestratorConfig`

先落 provider/channel 状态管理，再考虑插件体系。

## 可迁移到其他语言的点

这些设计不依赖 Python：

- 状态图和 checkpoint 可以用 Java/Spring、Node、Go 实现。
- ProviderManager 本质是接口注册和策略路由。
- ChannelManager 本质是 connector registry。
- selector profile 和 ingestion candidate 是数据模型，不依赖 Scrapling。
- human review / interrupt / resume 是业务流程，不依赖 LangGraph。

真正要避免的是复制许可证受限源码，而不是避免学习架构。

## 结论

可以深度参考，但不能直接粗暴搬：

- LangGraph：学状态图、checkpoint、interrupt、retry。
- Scrapling：学授权采集、证据留存、清洗、selector 漂移。
- AstrBot：学 manager/lifecycle/provider/plugin/dashboard 边界。

标准运营版最稳的路线是：继续自研核心客服中台，逐步把这些成熟项目里的工程思想变成我们自己的表结构、服务层和控制台能力。
