# H2W-KB1 客户专属知识包导入与签收 rehearsal

## 结论

- 阶段状态：`ready_for_customer_specific_knowledge_package_rehearsal`
- 可进入客户专属知识包本地试点 rehearsal：`true`
- 可作为客户资料包导入预检候选：`true`
- 客户专属知识库正式就绪：`false`
- 正式客户签收：`false`

## 本阶段实际验证

- 使用内部脱敏客户专属知识包，不使用真实客户原始聊天、订单、手机号、邮箱或平台昵称。
- 通过后端真实接口完成首任负责人创建、登录、知识更新包预检、导入、查询、回滚。
- 资料包同时包含业务对象、标准问答、流程政策、禁用承诺、转人工规则和回归题。
- 签收只生成 rehearsal 边界，不生成电子签章、合同签收或客户确认完成态。

## 资料包结构

- 业务对象：3
- 对象知识卡：8
- 来源文档：5
- 回归题：8
- 知识类型：business_object, forbidden_commitment, handoff_rule, process_policy, standard_qa

## 后端 rehearsal 证据

- 预检 can_apply：`true`
- 导入 can_apply：`true`
- 导入批次：`1`
- 导入后业务对象：3
- 导入后文档：5
- 导入后回归题集：1
- 文档 chunk：5
- 回滚状态：`rolled_back`
- 回滚后 active 文档：0
- 回滚后 active 回归题集：0

## 停止门禁

- 资料包未覆盖业务对象、标准问答、流程政策、禁用承诺、转人工规则时，不能进入客户试点。
- 资料包不能通过后端预检、导入、查询、回滚时，不能写成可交付。
- 回归题少于 8 条、没有引用来源或高风险题不转人工时，不能进入启用前复测。
- 出现手机号、邮箱、身份证、原始订单号等疑似敏感信息时，立即阻断。
- `customer_confirmed=false` 前，不能写成客户专属知识库已正式签收。

## 固定边界

- `real_customer_data_used=false`
- `provider_call_performed=false`
- `real_platform_send_performed=false`
- `formal_customer_signoff_performed=false`
- `customer_specific_knowledge_ready=false`

## 下一步

- 把该资料包流程映射到前端“知识维护总流程”的客户可操作路径。
- 准备真实客户资料收集模板，但仍需脱敏和客户确认后才能进入正式知识库签收。
- 继续推进非技术客户启动器/安装器和售后运维交接 rehearsal。

## 阻断项

- 无

## 警告

- 无
