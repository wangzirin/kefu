import type { WorkspacePageProps } from "./types";

export default function OpsPage({ ctx }: WorkspacePageProps) {
  const { OpsWorkerHealthPanel } = ctx.Components;
  return (
    <OpsWorkerHealthPanel
      state={ctx.opsWorkerHealth}
      alertRulesState={ctx.opsAlertRules}
      metricsState={ctx.opsMetrics}
      hasToken={Boolean(ctx.auth.token)}
      onRefresh={() => {
        if (ctx.auth.token) {
          if (ctx.canReadOpsWorkerHealth(ctx.auth.user)) void ctx.refreshOpsWorkerHealth(ctx.auth.user.tenant.id, ctx.auth.token);
          if (ctx.canReadOpsAlertRules(ctx.auth.user)) void ctx.refreshOpsAlertRules(ctx.auth.user.tenant.id, ctx.auth.token);
          if (ctx.canReadOpsMetrics(ctx.auth.user)) void ctx.refreshOpsMetrics(ctx.auth.user.tenant.id, ctx.auth.token);
        }
      }}
    />
  );
}
