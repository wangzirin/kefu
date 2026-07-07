import type { WorkspacePageProps } from "./types";

export default function QualityPage({ ctx }: WorkspacePageProps) {
  const { QualityReviewPanel } = ctx.Components;
  return (
    <QualityReviewPanel
      conversationInbox={ctx.conversationInbox}
      reviewItems={ctx.reviewItems}
      outboxDrafts={ctx.outboxDrafts}
      failureReviews={ctx.failureReviewItems}
      deliveryJobs={ctx.deliveryJobs}
      knowledgeEvaluation={ctx.knowledgeEvaluation}
      monthlyQualityReview={ctx.monthlyQualityReview}
      monthlyOpsReport={ctx.monthlyOpsReport}
      onlineReceiptQuality={ctx.onlineReceiptQuality}
      customerQualityReport={ctx.customerQualityReport}
      customerQualityReportArchives={ctx.customerQualityReportArchives}
      customerQualityReportSignoffs={ctx.customerQualityReportSignoffs}
      knowledgeGaps={ctx.knowledgeGaps}
      onExportCustomerQualityReport={(format: any) => void ctx.handleExportCustomerQualityReport(format)}
      onDownloadCustomerQualityReportArchive={(archiveEventId: number) => void ctx.handleDownloadCustomerQualityReportArchive(archiveEventId)}
      onRecordCustomerQualityReportSignoff={(payload: any) => void ctx.handleRecordCustomerQualityReportSignoff(payload)}
      canRecordCustomerQualityReportSignoff={ctx.canManageAccounts(ctx.auth.user)}
    />
  );
}
