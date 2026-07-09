import type { WorkspacePageProps } from "./types";

export default function KnowledgeRecallPage({ ctx }: WorkspacePageProps) {
  const { KnowledgeRecallPanel } = ctx.Components;
  return (
    <KnowledgeRecallPanel
      state={ctx.knowledgeWorkbench}
      searchQuery={ctx.knowledgeSearchQuery}
      hasToken={Boolean(ctx.auth.token)}
      onSearchQueryChange={ctx.handleKnowledgeSearchQueryChange}
      onSearchDocuments={(category?: string) => void ctx.handleSearchKnowledgeDocuments(category)}
      onRefresh={() => {
        if (ctx.auth.token && ctx.canReadKnowledgeDocuments(ctx.auth.user)) {
          void ctx.refreshKnowledgeDocuments(ctx.auth.user.tenant.id, ctx.auth.token, ctx.canManageKnowledgeWorkspace);
        }
      }}
    />
  );
}
