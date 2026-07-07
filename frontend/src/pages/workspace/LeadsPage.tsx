import type { WorkspacePageProps } from "./types";

export default function LeadsPage({ ctx }: WorkspacePageProps) {
  const { SalesLeadPanel } = ctx.Components;
  return (
    <SalesLeadPanel
      state={ctx.salesLeads}
      conversationState={ctx.conversationInbox}
      listView={ctx.salesLeadListView}
      filters={ctx.salesLeadFilters}
      hasToken={Boolean(ctx.auth.token)}
      currentUserId={ctx.auth.mode === "token" ? Number(ctx.auth.user.id) : null}
      canManageLeads={ctx.canManageLead}
      onListViewChange={ctx.handleSalesLeadListViewChange}
      onFiltersChange={ctx.handleSalesLeadFiltersChange}
      onRefresh={() => {
        if (ctx.auth.token && ctx.canReadLeads(ctx.auth.user)) {
          void ctx.refreshSalesLeads(ctx.auth.user.tenant.id, ctx.auth.token, ctx.salesLeadListView, ctx.salesLeadFilters);
        }
      }}
      onCreateFromConversation={(item: any) => void ctx.handleCreateSalesLead(item)}
      onUpdateStage={(lead: any, stage: any) => void ctx.handleUpdateSalesLeadStage(lead, stage)}
    />
  );
}
