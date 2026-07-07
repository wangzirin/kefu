import type { WorkspacePageProps } from "./types";

export default function ModelPage({ ctx }: WorkspacePageProps) {
  const { ModelRoutingPanel } = ctx.Components;
  return (
    <ModelRoutingPanel
      latestEvaluationRun={ctx.knowledgeEvaluation.lastRun}
      reviewItems={ctx.reviewItems}
      outboxDrafts={ctx.outboxDrafts}
      ragGovernance={ctx.ragCostGovernance}
      llmOpsReadiness={ctx.llmOpsReadiness}
      hasToken={Boolean(ctx.auth.token)}
      onRefresh={() => {
        if (ctx.auth.token && ctx.canReadOpsMetrics(ctx.auth.user)) {
          void ctx.refreshRagCostGovernance(ctx.auth.user.tenant.id, ctx.auth.token);
          void ctx.refreshLlmOpsReadiness(ctx.auth.user.tenant.id, ctx.auth.token);
        }
      }}
    />
  );
}
