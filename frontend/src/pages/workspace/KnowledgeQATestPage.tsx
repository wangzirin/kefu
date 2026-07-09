import type { WorkspacePageProps } from "./types";

export default function KnowledgeQATestPage({ ctx }: WorkspacePageProps) {
  const { KnowledgeQATestPanel } = ctx.Components;
  return (
    <KnowledgeQATestPanel
      state={ctx.knowledgeWorkbench}
      searchQuery={ctx.knowledgeQaSearch.query}
      searchResult={ctx.knowledgeQaSearch.result}
      searchStatus={ctx.knowledgeQaSearch.status}
      searchMessage={ctx.knowledgeQaSearch.message}
      hasToken={Boolean(ctx.auth.token)}
      onSearchQueryChange={ctx.handleKnowledgeQaSearchQueryChange}
      onSearchDocuments={() => void ctx.handleSearchKnowledgeQaDocuments()}
      onRefresh={() => {
        if (ctx.auth.token && ctx.canReadKnowledgeDocuments(ctx.auth.user)) {
          void ctx.refreshKnowledgeDocuments(ctx.auth.user.tenant.id, ctx.auth.token, ctx.canManageKnowledgeWorkspace);
        }
      }}
    />
  );
}
