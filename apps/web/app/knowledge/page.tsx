import { KnowledgeDashboard } from "@/components/knowledge/knowledge-dashboard";
import { AppShell } from "@/components/layout/app-shell";

export default function KnowledgePage() {
  return (
    <AppShell>
      <KnowledgeDashboard />
    </AppShell>
  );
}
