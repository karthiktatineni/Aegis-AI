"use client";

import { Cpu, Database, HardDrive, KeyRound, Server, ShieldCheck } from "lucide-react";
import * as React from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type { ModelStatus } from "@/types/api";

export default function SettingsPage() {
  const [modelStatus, setModelStatus] = React.useState<ModelStatus | null>(null);
  const [gpu, setGpu] = React.useState(true);
  const [sandbox, setSandbox] = React.useState(true);

  React.useEffect(() => {
    void api.modelStatus().then(setModelStatus).catch(() => setModelStatus(null));
  }, []);

  return (
    <AppShell>
      <section className="container space-y-5 py-5">
        <div className="flex flex-col justify-between gap-3 border-b pb-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-xl font-semibold">Settings</h1>
            <p className="text-sm text-muted-foreground">Runtime, storage, security, and local model configuration.</p>
          </div>
          <Badge variant="secondary">
            <ShieldCheck className="mr-1 size-3.5" />
            Authentication-ready
          </Badge>
        </div>

        <Tabs defaultValue="runtime" className="space-y-5">
          <TabsList>
            <TabsTrigger value="runtime">Runtime</TabsTrigger>
            <TabsTrigger value="storage">Storage</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
          </TabsList>

          <TabsContent value="runtime" className="grid gap-5 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="size-4 text-primary" />
                  Model Provider
                </CardTitle>
                <CardDescription>Local Mistral 7B or Qwen 2.5 7B through Transformers.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input readOnly value={modelStatus?.provider ?? "mock"} />
                <Input readOnly value={modelStatus?.local_model_id ?? "mistralai/Mistral-7B-Instruct-v0.3"} />
                <div className="flex items-center justify-between rounded-md border p-3">
                  <div>
                    <p className="text-sm font-medium">GPU acceleration</p>
                    <p className="text-xs text-muted-foreground">Device map uses auto placement when enabled.</p>
                  </div>
                  <Switch checked={gpu} onCheckedChange={setGpu} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Server className="size-4 text-primary" />
                  API
                </CardTitle>
                <CardDescription>REST and streaming endpoints are exposed by FastAPI.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input readOnly value={process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"} />
                <Button variant="outline" asChild>
                  <a href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/docs`}>
                    Open API docs
                  </a>
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="storage" className="grid gap-5 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="size-4 text-primary" />
                  Database
                </CardTitle>
                <CardDescription>SQLAlchemy repositories with SQLite for local dev and PostgreSQL for deployment.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input readOnly value="SQLite / PostgreSQL" />
                <Input readOnly value="Alembic migrations enabled" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <HardDrive className="size-4 text-primary" />
                  Vector Store
                </CardTitle>
                <CardDescription>ChromaDB persists semantic memory and knowledge chunks locally.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input readOnly value={modelStatus?.embedding_model ?? "sentence-transformers/all-MiniLM-L6-v2"} />
                <Input readOnly value="Metadata filters, tags, citations, re-ranking" />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security" className="grid gap-5 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <KeyRound className="size-4 text-primary" />
                  Access
                </CardTitle>
                <CardDescription>Local owner mode can be replaced with JWT or session auth.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input readOnly value="X-User-Id / X-User-Email dependency seam" />
                <Input readOnly value="Audit log table included" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShieldCheck className="size-4 text-primary" />
                  Tool Sandbox
                </CardTitle>
                <CardDescription>Commands are allowlisted and scoped to the configured workspace.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between rounded-md border p-3">
                  <div>
                    <p className="text-sm font-medium">Command execution</p>
                    <p className="text-xs text-muted-foreground">Timeouts and working directory isolation are enabled.</p>
                  </div>
                  <Switch checked={sandbox} onCheckedChange={setSandbox} />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </section>
    </AppShell>
  );
}
