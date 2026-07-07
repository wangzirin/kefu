import type { WorkspacePageProps } from "./types";

export default function OutboxPage({ ctx }: WorkspacePageProps) {
  const { OutboxPanel } = ctx.Components;
  return (
    <OutboxPanel
      state={ctx.outbox}
      workerRun={ctx.lastWorkerRun}
      deliveryQueue={ctx.deliveryQueue}
      deliveryQueueRun={ctx.lastDeliveryQueueRun}
      listView={ctx.outboxListView}
      hasToken={Boolean(ctx.auth.token)}
      canManageConnector={ctx.canManageChannelConnector}
      canManageDraft={ctx.canManageOutboxDraft}
      canManageSendAttempt={ctx.canManageOutboxSendAttempt}
      canManageSendPlan={ctx.canManageOutboxSendPlan}
      canManageDeliveryJob={ctx.canManageOutboxDeliveryJob}
      onListViewChange={ctx.setOutboxListView}
      onRefresh={() => {
        if (ctx.auth.token) {
          if (ctx.canReadOutboxDrafts(ctx.auth.user)) void ctx.refreshOutbox(ctx.auth.user.tenant.id, ctx.auth.token);
          if (ctx.canReadOutboxDeliveryJobs(ctx.auth.user)) void ctx.refreshDeliveryQueue(ctx.auth.user.tenant.id, ctx.auth.token);
        }
      }}
      onRunWorker={() => void ctx.handleRunWorker()}
      onRunDeliveryQueue={() => void ctx.handleRunDeliveryQueue()}
      onDryRun={(draftId: number) => void ctx.handleDryRun(draftId)}
      onConnectorPlan={(draft: any) => void ctx.handleConnectorPlan(draft)}
      onCreateDeliveryJob={(draft: any) => void ctx.handleCreateDeliveryJob(draft)}
      onConfirm={(draftId: number) => void ctx.handleConfirmDraft(draftId)}
    />
  );
}
