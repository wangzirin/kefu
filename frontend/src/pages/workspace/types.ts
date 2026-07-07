import type { ComponentType } from "react";

export type WorkspacePageProps = {
  ctx: Record<string, any>;
};

export type WorkspacePageComponent = ComponentType<WorkspacePageProps>;
