import type { WorkspacePageProps } from "./types";

export default function ChannelsPage({ ctx }: WorkspacePageProps) {
  const { ChannelConnectorCenterPanel } = ctx.Components;
  return (
    <ChannelConnectorCenterPanel
      selectedChannelId={ctx.getChannelEntryIdFromHash(ctx.workspaceHash)}
      reviewItems={ctx.reviewItems}
      outboxDrafts={ctx.outboxDrafts}
      failureReviews={ctx.failureReviewItems}
      deliveryJobs={ctx.deliveryJobs}
      workerRun={ctx.lastInboundWorkerRun}
      channelAccountState={ctx.channelAccountState}
      connectorState={ctx.channelConnectorSelfService}
      hasToken={Boolean(ctx.auth.token)}
      canManageConnector={ctx.canManageChannelConnector}
      tenantId={ctx.auth.user.tenant.id}
      onConfigureChannelAccount={(channelId: number, payload: any) => ctx.handleConfigureChannelAccount(channelId, payload)}
      onDeleteChannelAccount={(accountId: number) => ctx.handleDeleteChannelAccountConnection(accountId)}
      onConfigureConnector={(channelId: number, provider: string, publicConfig?: Record<string, unknown>) =>
        ctx.handleConfigureChannelConnector(channelId, provider, publicConfig)
      }
      onStartAuthorization={(channelId: number, provider: string, connectMode: "qr" | "manual") =>
        ctx.handleStartChannelConnectorAuthorization(channelId, provider, connectMode)
      }
      onSaveSecrets={(channelId: number, secrets: Record<string, string>) => ctx.handleUpsertChannelConnectorSecrets(channelId, secrets)}
      onDeleteSecrets={(channelId: number) => ctx.handleDeleteChannelConnectorSecrets(channelId)}
      onVerifyConnector={(channelId: number) => ctx.handleVerifyChannelConnector(channelId)}
      onRefreshChannelAccounts={() => {
        if (ctx.auth.token && ctx.canReadChannels(ctx.auth.user)) {
          void ctx.refreshChannelAccounts(ctx.auth.user.tenant.id, ctx.auth.token);
        }
      }}
      onCreateSafeTestConversation={ctx.handleCreateSafeTestConversation}
    />
  );
}
