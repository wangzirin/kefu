import type { WorkspacePageProps } from "./types";

export default function SettingsPage({ ctx }: WorkspacePageProps) {
  const { AccountManagementPanel } = ctx.Components;
  return (
    <AccountManagementPanel
      state={ctx.accountManagement}
      diagnosticExport={ctx.diagnosticExport}
      diagnosticIntake={ctx.diagnosticIntake}
      diagnosticRemediation={ctx.diagnosticRemediation}
      localMaintenanceReadiness={ctx.localMaintenanceReadiness}
      localBackupState={ctx.localBackupState}
      localRestoreDryRun={ctx.localRestoreDryRun}
      signedUpdatePreflight={ctx.signedUpdatePreflight}
      signedUpdateStage={ctx.signedUpdateStage}
      currentUser={ctx.auth.user}
      hasToken={Boolean(ctx.auth.token)}
      onCreateUser={ctx.handleCreateAccountUser}
      onUpdateUserStatus={ctx.handleUpdateAccountUserStatus}
      onResetUserPassword={ctx.handleResetAccountUserPassword}
      onExportDiagnosticBundle={ctx.handleExportDiagnosticBundle}
      onCreateDiagnosticUploadPackage={ctx.handleCreateDiagnosticUploadPackage}
      onCreateDiagnosticIntakeRecord={ctx.handleCreateDiagnosticIntakeRecord}
      onUpdateDiagnosticIntakeRecord={ctx.handleUpdateDiagnosticIntakeRecord}
      onDownloadDiagnosticIntakeRecord={ctx.handleDownloadDiagnosticIntakeRecord}
      onCreateDiagnosticRemediationRequest={ctx.handleCreateDiagnosticRemediationRequest}
      onUpdateDiagnosticRemediationRequest={ctx.handleUpdateDiagnosticRemediationRequest}
      onDownloadDiagnosticRemediationRequest={ctx.handleDownloadDiagnosticRemediationRequest}
      onCreateDiagnosticRemediationUpdatePlan={ctx.handleCreateDiagnosticRemediationUpdatePlan}
      onCreateLocalBackup={ctx.handleCreateLocalBackup}
      onVerifyLocalBackup={ctx.handleVerifyLocalBackup}
      onCreateLocalBackupRestoreDryRun={ctx.handleCreateLocalBackupRestoreDryRun}
      onPreflightSignedUpdatePackage={ctx.handlePreflightSignedUpdatePackage}
      onStageSignedUpdatePackage={ctx.handleStageSignedUpdatePackage}
      onApplySignedUpdatePackage={ctx.handleApplySignedUpdatePackage}
      onCreateProgramUpdateDryRun={ctx.handleCreateProgramUpdateDryRun}
      onRollbackSignedUpdatePackage={ctx.handleRollbackSignedUpdatePackage}
      onRefresh={() => {
        if (ctx.auth.token && ctx.canManageAccounts(ctx.auth.user)) void ctx.refreshAccountManagement(ctx.auth.user.tenant.id, ctx.auth.token);
        if (ctx.auth.token && ctx.canReadOpsMetrics(ctx.auth.user)) {
          void ctx.refreshDiagnosticIntakes(ctx.auth.user.tenant.id, ctx.auth.token);
          void ctx.refreshDiagnosticRemediations(ctx.auth.user.tenant.id, ctx.auth.token);
        }
        if (ctx.auth.token && ctx.canManageSignedUpdates(ctx.auth.user)) {
          void ctx.refreshLocalMaintenanceReadiness(ctx.auth.user.tenant.id, ctx.auth.token);
          void ctx.refreshSignedUpdatePackages(ctx.auth.user.tenant.id, ctx.auth.token);
          void ctx.refreshLocalBackups(ctx.auth.user.tenant.id, ctx.auth.token);
        }
      }}
    />
  );
}
