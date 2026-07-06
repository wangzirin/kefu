# P3-06U-10 前端组件和状态结构拆分第一片

日期：2026-07-01

## 目标

本片先处理维护风险最高、复用价值最明确的一块：把 P3-06U-09 新增的统一状态体系从 `frontend/src/App.tsx` 抽出到 `frontend/src/components/common/WorkspaceState.tsx`。

这不是完整页面拆分完成态。它的价值是先把“加载、空数据、无权限、配置缺失、接口失败、演示样本、真实服务端数据、真实外发关闭、禁用原因”这些跨页面通用能力变成独立组件，后续再拆知识、质量、渠道、运维等页面时可以复用同一套状态表达。

## 已完成

- 新增 `frontend/src/components/common/WorkspaceState.tsx`。
- 抽出并导出：
  - `WorkspaceStateNotice`
  - `PanelStateNotice`
  - `DataSourceBadge`
  - `DisabledReason`
  - `WorkspaceRuntimeStateStrip`
  - `formatAccessDisabledReason`
  - `WorkspaceStateKind`
  - `DataSourceMode`
- `frontend/src/App.tsx` 改为从 `components/common/WorkspaceState` 导入状态组件。
- `scripts/check_p3_06u_09_unified_states.py` 改为同时检查 `App.tsx` 和 `WorkspaceState.tsx`，避免旧脚本把组件必须留在 `App.tsx` 当成正确结构。
- 新增 `scripts/check_p3_06u_10_state_component_extraction.py`，专门验证本片结构拆分。

## 保持不变

- 不改页面路由。
- 不改后端接口。
- 不改权限逻辑。
- 不改真实外发开关。
- 不改渠道配置、模型调用、知识库写入或 worker 行为。
- 不改变客户可见文案和交互含义。

## 验收

- `python3 scripts/check_p3_06u_09_unified_states.py`
- `python3 scripts/check_p3_06u_10_state_component_extraction.py`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`

## 后续拆分顺序

1. `components/knowledge/`：知识文档、知识缺口、评测运行页。
2. `components/quality/`：质量复盘 BI 和修复路径。
3. `components/channels/`：渠道连接器中心。
4. `components/ops/`：worker 健康、告警规则、指标出口。
5. `components/layout/`：壳层、导航、状态条和页面框架。

后续每片都必须保持“行为不变，结构变清楚”，并继续通过 typecheck、build 和对应静态检查。
