import type { WorkspacePageProps } from "./types";

export default function ConversationPage({ ctx }: WorkspacePageProps) {
  const { ConversationInboxPanel } = ctx.Components;
  return (
    <ConversationInboxPanel
      state={ctx.conversationInbox}
      listView={ctx.conversationInboxView}
      filters={ctx.conversationInboxFilters}
      hasToken={Boolean(ctx.auth.token)}
      currentUserId={ctx.auth.mode === "token" ? Number(ctx.auth.user.id) : null}
      canManageConversations={ctx.canManageConversation}
      onListViewChange={ctx.handleConversationInboxViewChange}
      onFiltersChange={ctx.handleConversationInboxFiltersChange}
      onRefresh={() => {
        if (ctx.auth.token && ctx.canReadConversations(ctx.auth.user)) {
          void ctx.refreshConversationInbox(ctx.auth.user.tenant.id, ctx.auth.token);
        }
      }}
      onWorkflowAction={(item: any, action: any) => void ctx.handleConversationWorkflowAction(item, action)}
    />
  );
}
