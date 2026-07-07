import type { WorkspacePageProps } from "./types";

export default function GapsPage({ ctx }: WorkspacePageProps) {
  const { KnowledgeGapPanel, KnowledgeWorkspacePage } = ctx.Components;
  return (
    <KnowledgeWorkspacePage
      mode="gaps"
      documentState={ctx.knowledgeWorkbench}
      gapState={ctx.knowledgeGaps}
      evaluationState={ctx.knowledgeEvaluation}
      meshState={ctx.knowledgeMemoryMesh}
      hasToken={Boolean(ctx.auth.token)}
      canManage={ctx.canManageKnowledgeWorkspace}
      onRefreshMesh={() => {
        if (ctx.auth.token && ctx.canReadKnowledgeDocuments(ctx.auth.user)) {
          void ctx.refreshKnowledgeMemoryMeshOverview(ctx.auth.user.tenant.id, ctx.auth.token);
        }
      }}
    >
      <KnowledgeGapPanel
        state={ctx.knowledgeGaps}
        listView={ctx.knowledgeGapListView}
        hasToken={Boolean(ctx.auth.token)}
        canManage={ctx.canManageKnowledgeWorkspace}
        onListViewChange={ctx.handleKnowledgeGapListViewChange}
        onRefresh={() => {
          if (ctx.auth.token && ctx.canReadKnowledgeGaps(ctx.auth.user)) {
            void ctx.refreshKnowledgeGaps(ctx.auth.user.tenant.id, ctx.auth.token, ctx.knowledgeGapListView);
            void ctx.refreshKnowledgeMemoryMeshOverview(ctx.auth.user.tenant.id, ctx.auth.token);
          }
        }}
        onSync={() => void ctx.handleSyncKnowledgeGaps()}
        onUpdate={(gap: any, statusValue: any) => void ctx.handleUpdateKnowledgeGap(gap, statusValue)}
        onCreateDocumentDraft={(gap: any) => void ctx.handleCreateKnowledgeGapDocumentDraft(gap)}
        onCreateRegressionCase={(gap: any) => void ctx.handleCreateKnowledgeGapRegressionCase(gap)}
        onPublishDocument={(gap: any) => void ctx.handlePublishKnowledgeGapDocument(gap)}
      />
    </KnowledgeWorkspacePage>
  );
}
