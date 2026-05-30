"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bot, Brain, Database, Menu, Moon, Settings, Shield, Sparkles, Sun } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Chat", icon: Bot },
  { href: "/knowledge", label: "Knowledge", icon: Database },
  { href: "/settings", label: "Settings", icon: Settings }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = React.useState(false);
  const [dark, setDark] = React.useState(true);

  React.useEffect(() => {
    const stored = localStorage.getItem("aegis-theme");
    const enabled = stored ? stored === "dark" : true;
    setDark(enabled);
    document.documentElement.classList.toggle("dark", enabled);
  }, []);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    localStorage.setItem("aegis-theme", next ? "dark" : "light");
    document.documentElement.classList.toggle("dark", next);
  }

  return (
    <div className="min-h-screen bg-background">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 border-r bg-card transition-transform lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center gap-3 px-4">
          <div className="flex size-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Shield className="size-5" />
          </div>
          <div>
            <p className="text-sm font-semibold">Aegis AI</p>
            <p className="text-xs text-muted-foreground">Local command center</p>
          </div>
        </div>
        <Separator />
        <nav className="space-y-1 p-3">
          {navItems.map((item) => {
            const active = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex h-10 items-center gap-3 rounded-md px-3 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                  active && "bg-muted text-foreground"
                )}
              >
                <Icon className="size-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="absolute bottom-0 left-0 right-0 border-t p-3">
          <div className="rounded-md bg-muted p-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Brain className="size-4 text-primary" />
              Memory sync
            </div>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              Short-term context, semantic recall, and user preferences are wired into the API.
            </p>
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur md:px-6">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setOpen((value) => !value)}>
              <Menu className="size-5" />
              <span className="sr-only">Toggle navigation</span>
            </Button>
            <div>
              <p className="text-sm font-semibold">Private AI workspace</p>
              <p className="text-xs text-muted-foreground">FastAPI, ChromaDB, local model runtime</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden items-center gap-2 rounded-md border px-2.5 py-1.5 text-xs text-muted-foreground md:flex">
              <Sparkles className="size-3.5 text-accent" />
              Mistral / Qwen ready
            </div>
            <Button variant="outline" size="icon" onClick={toggleTheme}>
              {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
              <span className="sr-only">Toggle theme</span>
            </Button>
          </div>
        </header>
        <main className="min-h-[calc(100vh-4rem)]">{children}</main>
      </div>
    </div>
  );
}
