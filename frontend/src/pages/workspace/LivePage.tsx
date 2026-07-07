import type { WorkspacePageProps } from "./types";

export default function LivePage({ ctx }: WorkspacePageProps) {
  const { ConversationWorkbenchPanel, LiveColleagueProfilePanel } = ctx.Components;
  if (ctx.dialogueScope === "colleagues" && ctx.selectedLiveColleague) {
    return <LiveColleagueProfilePanel colleague={ctx.selectedLiveColleague} />;
  }
  return (
    <ConversationWorkbenchPanel
      state={ctx.conversationInbox}
      reviewItems={ctx.reviewItems}
      replyDecisions={ctx.replyDecisions}
      replyDecisionStatus={ctx.replyDecisionState.status}
      outboxDrafts={ctx.outboxDrafts}
      failureReviews={ctx.failureReviewItems}
      deliveryJobs={ctx.deliveryJobs}
      selectedConversationId={ctx.selectedLiveConversationId}
      conversationDetail={ctx.conversationDetail.data?.id === ctx.selectedLiveConversationId ? ctx.conversationDetail.data : null}
      conversationDetailStatus={ctx.conversationDetail.status}
      conversationDetailMessage={ctx.conversationDetail.message}
      localReplyState={ctx.localReplyState}
      hasToken={Boolean(ctx.auth.token) || ctx.auth.mode === "demo"}
      currentUserId={Number(ctx.auth.user.id)}
      canManageConversations={ctx.canManageConversation}
      targetQueue={ctx.overviewTaskContext?.targetSection === "live" ? ctx.overviewTaskContext.queue : undefined}
      targetChannelId={ctx.overviewTaskContext?.targetSection === "live" ? ctx.overviewTaskContext.channelId : null}
      channelIdentities={ctx.channelIdentities}
      colleagues={ctx.liveColleagueSummaries}
      onRefresh={ctx.refreshLiveWorkspaceResources}
      onCreateSafeTestConversation={() => void ctx.handleCreateSafeTestConversation()}
      onSelectConversation={ctx.setSelectedLiveConversationId}
      onSendLocalReply={(item: any, content: string) => void ctx.handleSendLocalConversationReply(item, content)}
      canApproveReviewDraft={ctx.canManageConversation && ctx.canManageOutboxDraft}
      canConfirmOutboxDraft={ctx.canManageOutboxDraft}
      onWorkflowAction={(item: any, action: any, note: string, targetUserId: any, targetTeamId: any) =>
        void ctx.handleConversationWorkflowAction(item, action, note, targetUserId, targetTeamId)
      }
      onApproveReviewDraft={(item: any, finalReply: string, resolutionNote: string) =>
        void ctx.handleReviewApprove(item, { finalReply, resolutionNote })
      }
      onConfirmOutboxDraft={(draftId: number) => void ctx.handleConfirmDraft(draftId)}
    />
  );
}
