import type { WorkspacePageProps } from "./types";

export default function KnowledgePage({ ctx }: WorkspacePageProps) {
  const { KnowledgeDocumentsPanel } = ctx.Components;
  return (
    <KnowledgeDocumentsPanel
      state={ctx.knowledgeWorkbench}
      evaluationState={ctx.knowledgeEvaluation}
      customerQualityReport={ctx.customerQualityReport}
      customerQualityReportSignoffs={ctx.customerQualityReportSignoffs}
      updatePackageDraft={ctx.knowledgeUpdatePackageDraft}
      templateImportDraft={ctx.knowledgeTemplateImportDraft}
      aiServiceStatus={ctx.aiServiceStatus}
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
      onSearchQueryChange={ctx.handleKnowledgeSearchQueryChange}
      onListViewChange={ctx.setKnowledgeDocumentListView}
      onCreateBusinessObject={() => void ctx.handleSaveBusinessObject()}
      onPreviewUpdatePackage={() => void ctx.handlePreviewKnowledgeUpdatePackage()}
      onImportUpdatePackage={() => void ctx.handleImportKnowledgeUpdatePackage()}
      onImportQuestionWorkbook={(file: File) => void ctx.handleImportKnowledgeQuestionWorkbook(file)}
      onRunTemplateSample={() => void ctx.handleRunKnowledgeTemplateSample()}
      onPublishTemplateImport={() => void ctx.handlePublishKnowledgeTemplateImport()}
      onSaveReplyStrategy={() => void ctx.handleSaveTenantReplyStrategy()}
      onCreateObjectKnowledgeCard={() => void ctx.handleCreateObjectKnowledgeCard()}
      onImportDocument={() => void ctx.handleImportKnowledgeDocument()}
      onSearchDocuments={(category?: string) => void ctx.handleSearchKnowledgeDocuments(category)}
      onCheckPublishDocument={(document: any) => void ctx.handleCheckKnowledgeDocumentPublishGate(document)}
      onPublishDocument={(document: any) => void ctx.handlePublishKnowledgeDocument(document)}
      onRollbackDocument={(document: any) => void ctx.handleRollbackKnowledgeDocument(document)}
      onUpdateDocumentStatus={(document: any, status: any) => void ctx.handleUpdateKnowledgeDocumentStatus(document, status)}
      onBulkUpdateDocuments={(documents: any[], status: any) => void ctx.handleBulkUpdateKnowledgeDocuments(documents, status)}
      onDeleteDocument={(document: any) => void ctx.handleDeleteKnowledgeDocument(document)}
      onBulkDeleteDocuments={(documents: any[]) => void ctx.handleBulkDeleteKnowledgeDocuments(documents)}
      onRefresh={() => {
        if (ctx.auth.token && ctx.canReadKnowledgeDocuments(ctx.auth.user)) {
          void ctx.refreshKnowledgeDocuments(ctx.auth.user.tenant.id, ctx.auth.token, ctx.canManageKnowledgeWorkspace);
        }
      }}
    />
  );
}
