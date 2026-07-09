import type { WorkspacePageProps } from "./types";

export default function KnowledgeRecallPage({ ctx }: WorkspacePageProps) {
  const { KnowledgeRecallPanel } = ctx.Components;
  return (
    <KnowledgeRecallPanel
      state={ctx.knowledgeWorkbench}
      searchQuery={ctx.knowledgeRecallSearch.query}
      searchResult={ctx.knowledgeRecallSearch.result}
      searchStatus={ctx.knowledgeRecallSearch.status}
      searchMessage={ctx.knowledgeRecallSearch.message}
      hasToken={Boolean(ctx.auth.token)}
      onSearchQueryChange={ctx.handleKnowledgeRecallSearchQueryChange}
      onSearchDocuments={(category?: string) => void ctx.handleSearchKnowledgeRecallDocuments(category)}
      onRefresh={() => {
        if (ctx.auth.token && ctx.canReadKnowledgeDocuments(ctx.auth.user)) {
          void ctx.refreshKnowledgeDocuments(ctx.auth.user.tenant.id, ctx.auth.token, ctx.canManageKnowledgeWorkspace);
        }
      }}
    />
  );
}
