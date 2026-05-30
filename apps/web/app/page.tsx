import { ChatConsole } from "@/components/chat/chat-console";
import { AppShell } from "@/components/layout/app-shell";

export default function HomePage() {
  return (
    <AppShell>
      <ChatConsole />
    </AppShell>
  );
}
