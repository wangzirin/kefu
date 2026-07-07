import type { WorkspacePageProps } from "./types";

export default function KnowledgePage({ ctx }: WorkspacePageProps) {
  const { KnowledgeDocumentsPanel, KnowledgeWorkspacePage } = ctx.Components;
  return (
    <KnowledgeWorkspacePage
      mode="library"
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
      <KnowledgeDocumentsPanel
        state={ctx.knowledgeWorkbench}
        evaluationState={ctx.knowledgeEvaluation}
        customerQualityReport={ctx.customerQualityReport}
        customerQualityReportSignoffs={ctx.customerQualityReportSignoffs}
        updatePackageDraft={ctx.knowledgeUpdatePackageDraft}
        replyStrategyState={ctx.tenantReplyStrategy}
        replyStrategyDraft={ctx.replyStrategyDraft}
        businessObjectDraft={ctx.businessObjectDraft}
        objectKnowledgeCardDraft={ctx.objectKnowledgeCardDraft}
        draft={ctx.knowledgeDraft}
        searchQuery={ctx.knowledgeSearchQuery}
        listView={ctx.knowledgeDocumentListView}
        hasToken={Boolean(ctx.auth.token)}
        canImport={ctx.canManageKnowledgeWorkspace}
        onBusinessObjectDraftChange={ctx.setBusinessObjectDraft}
        onUpdatePackageDraftChange={ctx.setKnowledgeUpdatePackageDraft}
        onReplyStrategyDraftChange={ctx.setReplyStrategyDraft}
        onObjectKnowledgeCardDraftChange={ctx.setObjectKnowledgeCardDraft}
        onDraftChange={ctx.setKnowledgeDraft}
        onSearchQueryChange={ctx.setKnowledgeSearchQuery}
        onListViewChange={ctx.setKnowledgeDocumentListView}
        onCreateBusinessObject={() => void ctx.handleSaveBusinessObject()}
        onPreviewUpdatePackage={() => void ctx.handlePreviewKnowledgeUpdatePackage()}
        onImportUpdatePackage={() => void ctx.handleImportKnowledgeUpdatePackage()}
        onSaveReplyStrategy={() => void ctx.handleSaveTenantReplyStrategy()}
        onCreateObjectKnowledgeCard={() => void ctx.handleCreateObjectKnowledgeCard()}
        onImportDocument={() => void ctx.handleImportKnowledgeDocument()}
        onSearchDocuments={() => void ctx.handleSearchKnowledgeDocuments()}
        onCheckPublishDocument={(document: any) => void ctx.handleCheckKnowledgeDocumentPublishGate(document)}
        onPublishDocument={(document: any) => void ctx.handlePublishKnowledgeDocument(document)}
        onRollbackDocument={(document: any) => void ctx.handleRollbackKnowledgeDocument(document)}
        onRefresh={() => {
          if (ctx.auth.token && ctx.canReadKnowledgeDocuments(ctx.auth.user)) {
            void ctx.refreshKnowledgeDocuments(ctx.auth.user.tenant.id, ctx.auth.token, ctx.canManageKnowledgeWorkspace);
            void ctx.refreshKnowledgeMemoryMeshOverview(ctx.auth.user.tenant.id, ctx.auth.token);
          }
        }}
      />
    </KnowledgeWorkspacePage>
  );
}
