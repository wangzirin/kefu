import type { WorkspacePageProps } from "./types";

export default function KnowledgeQATestPage({ ctx }: WorkspacePageProps) {
  const { KnowledgeQATestPanel } = ctx.Components;
  return (
    <KnowledgeQATestPanel
      state={ctx.knowledgeWorkbench}
      searchQuery={ctx.knowledgeSearchQuery}
      hasToken={Boolean(ctx.auth.token)}
      onSearchQueryChange={ctx.handleKnowledgeSearchQueryChange}
      onSearchDocuments={() => void ctx.handleSearchKnowledgeDocuments()}
      onRefresh={() => {
        if (ctx.auth.token && ctx.canReadKnowledgeDocuments(ctx.auth.user)) {
          void ctx.refreshKnowledgeDocuments(ctx.auth.user.tenant.id, ctx.auth.token, ctx.canManageKnowledgeWorkspace);
        }
      }}
    />
  );
}
