import type { WorkspacePageProps } from "./types";

export default function OverviewPage({ ctx }: WorkspacePageProps) {
  const { WorkbenchCommandCenter } = ctx.Components;
  return (
    <WorkbenchCommandCenter
      businessOpsDashboard={ctx.businessOpsDashboard.data}
      dashboardStatus={ctx.businessOpsDashboard.status}
      dashboardMessage={"message" in ctx.businessOpsDashboard ? ctx.businessOpsDashboard.message : null}
      reviewItems={ctx.reviewItems}
      outboxDrafts={ctx.outboxDrafts}
      failureReviews={ctx.failureReviewItems}
      deliveryJobs={ctx.deliveryJobs}
      latestEvaluationRun={ctx.knowledgeEvaluation.lastRun}
      onRequestBusinessOpsDashboard={(params: any) => {
        if (ctx.auth.mode === "token" && ctx.auth.token && ctx.canReadDashboard(ctx.auth.user)) {
          void ctx.refreshBusinessOpsDashboard(ctx.auth.user.tenant.id, ctx.auth.token, params);
        }
      }}
    />
  );
}
