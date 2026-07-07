import type { WorkspacePageProps } from "./types";

export default function ReviewsPage({ ctx }: WorkspacePageProps) {
  const { ReviewEvidenceDetail, ReviewInboxPanel } = ctx.Components;
  return (
    <section className="workspace-page-grid two-column">
      <ReviewInboxPanel
        state={ctx.reviewInbox}
        workerRun={ctx.lastInboundWorkerRun}
        listView={ctx.reviewListView}
        hasToken={Boolean(ctx.auth.token)}
        canManageConversations={ctx.canManageConversation}
        canRunInboundWorker={ctx.canRunInboundWorkerWorkspace}
        canManageOutboxDraft={ctx.canManageOutboxDraft}
        selectedReviewId={ctx.selectedReview?.id ?? null}
        onListViewChange={ctx.setReviewListView}
        onRefresh={() => {
          if (ctx.auth.token && ctx.canReadConversations(ctx.auth.user)) {
            void ctx.refreshReviewInbox(ctx.auth.user.tenant.id, ctx.auth.token);
          }
        }}
        onRunInboundWorker={() => void ctx.handleRunInboundWorker()}
        onSelect={(item: any) => ctx.setSelectedReviewId(item.id)}
        onApprove={(item: any) => void ctx.handleReviewApprove(item)}
        onReject={(item: any) => void ctx.handleReviewReject(item)}
      />
      <ReviewEvidenceDetail
        item={ctx.selectedReview}
        outboxDrafts={ctx.outboxDrafts}
        failureReviews={ctx.failureReviewItems}
        deliveryJobs={ctx.deliveryJobs}
        onSelectReview={(item: any) => ctx.setSelectedReviewId(item.id)}
      />
    </section>
  );
}
