import type { WorkspacePageProps } from "./types";

export default function ContactsPage({ ctx }: WorkspacePageProps) {
  const { ContactProfilesPanel } = ctx.Components;
  return (
    <ContactProfilesPanel
      state={ctx.contactProfiles}
      listView={ctx.contactProfileListView}
      hasToken={Boolean(ctx.auth.token)}
      onListViewChange={ctx.handleContactProfileListViewChange}
      onRefresh={() => {
        if (ctx.auth.token && ctx.canReadCustomers(ctx.auth.user)) {
          void ctx.refreshContactProfiles(ctx.auth.user.tenant.id, ctx.auth.token, ctx.contactProfileListView);
        }
      }}
      onSelect={(contactId: number) => void ctx.handleSelectContactProfile(contactId)}
    />
  );
}
