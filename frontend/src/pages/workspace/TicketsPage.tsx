import type { WorkspacePageProps } from "./types";

export default function TicketsPage({ ctx }: WorkspacePageProps) {
  const { SupportTicketPanel } = ctx.Components;
  return (
    <SupportTicketPanel
      state={ctx.supportTickets}
      conversationState={ctx.conversationInbox}
      listView={ctx.supportTicketListView}
      filters={ctx.supportTicketFilters}
      hasToken={Boolean(ctx.auth.token)}
      currentUserId={ctx.auth.mode === "token" ? Number(ctx.auth.user.id) : null}
      canManageTickets={ctx.canManageTicket}
      onListViewChange={ctx.handleSupportTicketListViewChange}
      onFiltersChange={ctx.handleSupportTicketFiltersChange}
      onRefresh={() => {
        if (ctx.auth.token && ctx.canReadTickets(ctx.auth.user)) {
          void ctx.refreshSupportTickets(ctx.auth.user.tenant.id, ctx.auth.token, ctx.supportTicketListView, ctx.supportTicketFilters);
        }
      }}
      onCreateFromConversation={(item: any) => void ctx.handleCreateSupportTicket(item)}
      onUpdateStatus={(ticket: any, statusValue: any) => void ctx.handleUpdateSupportTicketStatus(ticket, statusValue)}
    />
  );
}
