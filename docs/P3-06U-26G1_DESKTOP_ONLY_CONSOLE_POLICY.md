# P3-06U-26G1 桌面中台模式收口

日期：2026-07-02  
性质：内部工程口径与验收规则  
适用范围：`standard_ops` 前端中台、当前阶段浏览器 smoke 和后续工程验收  

## 1. 结论

从本阶段开始，万法常世 AI 全智能客服系统的中台前端只按桌面客服工作台设计和验收，不再设计、优化或验收手机端、移动端、小屏自然单列布局。

当前系统定位是给中小企业客服负责人、运营人员和坐席在电脑上使用的客服中台。它不是移动 H5 客服后台，也不是手机端商家 App。

## 2. 本轮实际改动

### 2.1 前端壳层

`frontend/src/styles.css` 已改为桌面最小宽度：

- 新增 `--console-min-width: 1180px`。
- `html/body/#root` 统一保留桌面最小宽度。
- `.app-shell` 固定为 `224px` 左侧导航 + 右侧主工作区。
- 小于桌面宽度时不再切成手机单列形态。

### 2.2 移除手机端媒体块

已从当前主样式中移除这些小屏/手机端布局块：

- `@media (max-width: 960px)`
- `@media (min-width: 721px) and (max-width: 960px)`
- `@media (max-width: 560px)`
- `@media (max-width: 980px)`
- `@media (max-width: 900px)`

保留的仅是桌面宽度增强和窄桌面规则，例如 `1180px` 桌面下限附近的排版调整。

### 2.3 当前阶段浏览器验收

已把当前阶段主线浏览器脚本里的手机视口移除：

- `scripts/check_p3_06u_26b_wechat_first_workbench.mjs`
- `scripts/check_p3_06u_26c_channel_account_configuration.mjs`
- `scripts/check_p3_06u_26d_knowledge_three_pages.mjs`
- `scripts/check_p3_06u_26e_answer_quality_evaluation.mjs`
- `scripts/check_p3_06u_26g_channel_sandbox_rpa_boundary.mjs`
- `scripts/check_p3_06u_24_knowledge_split_and_channel_accounts.mjs`
- `scripts/check_p3_06t_03_bi_overview.mjs`

后续默认验收视口为：

- `1440 x 900`
- `1280 x 800`
- `1180 x 768`

不再默认跑 `390px`、手机视口或移动端无横向溢出检查。

## 3. 历史记录处理

历史文档、历史截图和历史 README 里曾出现过的手机端、390 视口、移动端 QA 记录，只作为过往阶段证据保留，不再代表当前产品目标。

不删除历史证据的原因：

- 方便追溯之前为什么做过小屏修复。
- 避免破坏阶段记录和输出索引。
- 避免把历史验收误改成当前结论。

当前有效口径以本文档、当前 README 状态和 `scripts/check_p3_06u_26g1_desktop_only_console.py` 为准。

## 4. 后续工程规则

后续做前端优化时，默认遵守：

1. 只按桌面客服中台设计。
2. 左侧导航、右侧工作区、对话台、BI 总览、知识运营、渠道接入和运维页面都优先服务电脑端使用。
3. 不再为了手机端牺牲桌面主工作流密度。
4. 不再新增手机端截图、手机端验收脚本或移动端专用 CSS。
5. 如果未来要做手机端，必须单独立项为新的移动产品，而不是塞回当前中台。

## 5. 当前边界

本轮只收束前端产品形态和验收口径，不代表：

- 真实渠道已经接通。
- 真实外发已经开启。
- RPA 已进入正式默认交付链。
- 知识评测已经等于完整客服准确率。
- 生产级 RAG、高并发和全渠道官方接入已经完成。

## 6. 验收命令

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
python3 scripts/check_p3_06u_26g1_desktop_only_console.py
cd frontend && npm run typecheck && npm run build
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL='http://127.0.0.1:5182/?demo=1#live' node ../scripts/check_p3_06u_26b_wechat_first_workbench.mjs
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL='http://127.0.0.1:5182/?demo=1' node ../scripts/check_p3_06u_26g_channel_sandbox_rpa_boundary.mjs
```

## 7. 下一步

完成桌面中台口径收口后，下一步仍按总纲进入 `P3-06U-26H`：部署运维、客户账号、诊断包、备份恢复、告警和月度质量复盘收束。
