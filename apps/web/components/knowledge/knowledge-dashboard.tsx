"use client";

import { Database, FileText, Filter, Loader2, Plus, Search, Upload } from "lucide-react";
import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { api, buildApiUrl } from "@/lib/api";
import type { Collection } from "@/types/api";

export function KnowledgeDashboard() {
  const [collections, setCollections] = React.useState<Collection[]>([]);
  const [activeId, setActiveId] = React.useState<string | null>(null);
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [query, setQuery] = React.useState("");
  const [results, setResults] = React.useState<Array<Record<string, unknown>>>([]);
  const [busy, setBusy] = React.useState(false);
  const fileRef = React.useRef<HTMLInputElement | null>(null);

  const active = collections.find((collection) => collection.id === activeId) ?? collections[0];

  React.useEffect(() => {
    void refresh();
  }, []);

  async function refresh() {
    const data = await api.listCollections();
    setCollections(data);
    setActiveId((current) => current ?? data[0]?.id ?? null);
  }

  async function createCollection() {
    if (!name.trim()) return;
    setBusy(true);
    try {
      const collection = await api.createCollection({
        name: name.trim(),
        description: description.trim(),
        tags: ["local", "rag"]
      });
      setCollections((items) => [collection, ...items]);
      setActiveId(collection.id);
      setName("");
      setDescription("");
    } finally {
      setBusy(false);
    }
  }

  async function upload() {
    const file = fileRef.current?.files?.[0];
    if (!file || !active) return;
    setBusy(true);
    const form = new FormData();
    form.append("file", file);
    form.append("tags", active.tags.join(","));
    try {
      const response = await fetch(buildApiUrl(`/knowledge/collections/${active.id}/upload`), {
        method: "POST",
        body: form
      });
      if (!response.ok) throw new Error(await response.text());
      await refresh();
      if (fileRef.current) fileRef.current.value = "";
    } finally {
      setBusy(false);
    }
  }

  async function search() {
    if (!query.trim() || !active) return;
    setBusy(true);
    try {
      const response = await api.searchKnowledge(query, [active.id]);
      setResults(response.results as Array<Record<string, unknown>>);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="container grid gap-5 py-5 lg:grid-cols-[320px_minmax(0,1fr)]">
      <div className="space-y-5">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="size-4 text-primary" />
              Collection
            </CardTitle>
            <CardDescription>Group documents by project, source, or workflow.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Name" />
            <Textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Description"
              className="min-h-20"
            />
            <Button onClick={createCollection} disabled={busy || !name.trim()} className="w-full">
              {busy ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
              Create
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="size-4 text-primary" />
              Collections
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {collections.map((collection) => (
              <button
                type="button"
                key={collection.id}
                onClick={() => setActiveId(collection.id)}
                className={`w-full rounded-md border p-3 text-left transition-colors hover:bg-muted ${
                  active?.id === collection.id ? "bg-muted" : ""
                }`}
              >
                <p className="truncate text-sm font-medium">{collection.name}</p>
                <p className="mt-1 text-xs text-muted-foreground">{collection.documents.length} documents</p>
              </button>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="space-y-5">
        <div className="flex flex-col justify-between gap-3 border-b pb-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-xl font-semibold">Knowledge Management</h1>
            <p className="text-sm text-muted-foreground">PDF, DOCX, Markdown, TXT, CSV, and HTML ingestion.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">
              <Filter className="mr-1 size-3" />
              Metadata filters
            </Badge>
            <Badge variant="accent">Re-ranking</Badge>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{active?.name ?? "No collection selected"}</CardTitle>
            <CardDescription>{active?.description ?? "Create a collection to start indexing documents."}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-[1fr_auto]">
            <Input ref={fileRef} type="file" accept=".pdf,.docx,.md,.markdown,.txt,.csv,.html,.htm" />
            <Button onClick={upload} disabled={!active || busy}>
              {busy ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
              Upload
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="size-4 text-primary" />
              Semantic Search
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search the active collection" />
              <Button onClick={search} disabled={!active || busy || !query.trim()}>
                <Search className="size-4" />
                Search
              </Button>
            </div>
            <div className="grid gap-3">
              {results.map((result) => (
                <div key={String(result.chunk_id)} className="rounded-lg border bg-card p-4">
                  <div className="flex items-center gap-2">
                    <FileText className="size-4 text-primary" />
                    <p className="text-sm font-medium">{String(result.filename)}</p>
                    <Badge variant="outline">{Math.round(Number(result.score) * 100)}%</Badge>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{String(result.excerpt)}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
