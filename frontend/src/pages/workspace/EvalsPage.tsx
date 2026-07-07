import type { WorkspacePageProps } from "./types";

export default function EvalsPage({ ctx }: WorkspacePageProps) {
  const { KnowledgeEvaluationPanel, KnowledgeWorkspacePage } = ctx.Components;
  return (
    <KnowledgeWorkspacePage
      mode="evals"
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
      <KnowledgeEvaluationPanel
        state={ctx.knowledgeEvaluation}
        draft={ctx.evaluationDraft}
        questionBankDraft={ctx.customerQuestionBankDraft}
        labelImportDraft={ctx.finalAnswerLabelImportDraft}
        setListView={ctx.evaluationSetListView}
        resultListView={ctx.evaluationResultListView}
        hasToken={Boolean(ctx.auth.token)}
        canManage={ctx.canManageKnowledgeWorkspace}
        onDraftChange={ctx.setEvaluationDraft}
        onQuestionBankDraftChange={ctx.setCustomerQuestionBankDraft}
        onLabelImportDraftChange={ctx.setFinalAnswerLabelImportDraft}
        onPrecheckQuestionBank={() => void ctx.handlePrecheckCustomerQuestionBank()}
        onImportQuestionBank={() => void ctx.handleImportCustomerQuestionBank()}
        onSetListViewChange={ctx.setEvaluationSetListView}
        onResultListViewChange={ctx.setEvaluationResultListView}
        onCreateSet={() => void ctx.handleCreateKnowledgeEvaluationSet()}
        onRunSet={(setId: number) => void ctx.handleRunKnowledgeEvaluation(setId)}
        onLoadRun={(runId: number) => void ctx.handleLoadKnowledgeEvaluationRun(runId)}
        onLabelFactuality={(runCase: any, statusValue: any) => void ctx.handleLabelEvaluationRunCaseFactuality(runCase, statusValue)}
        onCaptureFinalAnswerSample={(runCase: any, finalAnswerText: string) =>
          void ctx.handleCaptureEvaluationRunCaseFinalAnswerSample(runCase, finalAnswerText)
        }
        onBatchLabelSampledFactuality={(run: any, statusValue: any) => void ctx.handleBatchLabelSampledFactuality(run, statusValue)}
        onExportReport={(runId: number, reportFormat: any) => void ctx.handleExportKnowledgeEvaluationRunReport(runId, reportFormat)}
        onExportFinalAnswerLabels={(runId: number) => void ctx.handleExportFinalAnswerLabels(runId)}
        onPrecheckFinalAnswerLabels={(runId: number) => void ctx.handlePrecheckFinalAnswerLabels(runId)}
        onImportFinalAnswerLabels={(runId: number) => void ctx.handleImportFinalAnswerLabels(runId)}
        onRefresh={() => {
          if (ctx.auth.token && ctx.canReadKnowledgeEvaluations(ctx.auth.user)) {
            void ctx.refreshKnowledgeEvaluations(ctx.auth.user.tenant.id, ctx.auth.token, true);
            void ctx.refreshKnowledgeMemoryMeshOverview(ctx.auth.user.tenant.id, ctx.auth.token);
          }
        }}
      />
    </KnowledgeWorkspacePage>
  );
}
