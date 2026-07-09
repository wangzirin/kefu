import type { WorkspacePageProps } from "./types";

export default function BotModelServicePage({ ctx }: WorkspacePageProps) {
  const { BotModelServicePanel } = ctx.Components;
  return (
    <BotModelServicePanel
      state={ctx.modelService}
      hasToken={Boolean(ctx.auth.token)}
      canManage={ctx.canManageKnowledgeWorkspace}
      onRefresh={() => {
        if (ctx.auth.token && ctx.canReadKnowledgeDocuments(ctx.auth.user)) {
          void ctx.refreshModelService(ctx.auth.user.tenant.id, ctx.auth.token);
        }
      }}
      onSaveApiKey={(apiKey: string) => void ctx.handleSaveModelServiceApiKey(apiKey)}
      onClearApiKey={() => void ctx.handleClearModelServiceApiKey()}
      onProbe={() => void ctx.handleProbeModelService()}
    />
  );
}
