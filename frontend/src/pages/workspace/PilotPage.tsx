import type { WorkspacePageProps } from "./types";

export default function PilotPage({ ctx }: WorkspacePageProps) {
  const { PilotPreparationPanel } = ctx.Components;
  return (
    <PilotPreparationPanel
      pilotReadiness={ctx.pilotReadiness}
      localMaintenanceReadiness={ctx.localMaintenanceReadiness}
      monthlyOpsReport={ctx.monthlyOpsReport}
      knowledgeConfirmationImport={ctx.knowledgeConfirmationImport}
      customerMaterialPrecheck={ctx.customerMaterialPrecheck}
      customerMaterialBatches={ctx.customerMaterialBatches}
      customerMaterialTemplatePackage={ctx.customerMaterialTemplatePackage}
      customerMaterialHandoffBundle={ctx.customerMaterialHandoffBundle}
      canImportConfirmation={ctx.hasKnowledgeManagePermission(ctx.auth.user)}
      onRefresh={() => {
        if (ctx.auth.token && ctx.canReadOpsMetrics(ctx.auth.user)) void ctx.refreshPilotReadiness(ctx.auth.user.tenant.id, ctx.auth.token);
        if (ctx.auth.token && ctx.hasKnowledgeManagePermission(ctx.auth.user)) void ctx.refreshCustomerMaterialBatches(ctx.auth.user.tenant.id, ctx.auth.token);
      }}
      onImportKnowledgeConfirmation={(filename: string, csvText: string) => void ctx.handleImportKnowledgeConfirmation(filename, csvText)}
      onPrecheckCustomerMaterials={(materialsCsv: string, questionsCsv: string, manifestJson: string) =>
        void ctx.handlePrecheckCustomerMaterials(materialsCsv, questionsCsv, manifestJson)
      }
      onLoadCustomerMaterialBatches={() => {
        if (ctx.auth.token && ctx.hasKnowledgeManagePermission(ctx.auth.user)) {
          void ctx.refreshCustomerMaterialBatches(ctx.auth.user.tenant.id, ctx.auth.token);
        }
      }}
      onLoadCustomerMaterialTemplatePackage={() => void ctx.handleLoadCustomerMaterialTemplatePackage()}
      onDownloadCustomerMaterialHandoffBundle={() => void ctx.handleDownloadCustomerMaterialHandoffBundle()}
    />
  );
}
