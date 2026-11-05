"use client";

import { AlertCircle, Clock, Loader2, RefreshCw, Zap } from "lucide-react";
import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { checkServerHealth, fetchDailyQuota } from "@/lib/api";
import type { QuotaInfo } from "@/types/api";

export function ServerStatusGuard() {
  const [status, setStatus] = React.useState<"connected" | "spinning_up" | "disconnected">("spinning_up");
  const [quota, setQuota] = React.useState<QuotaInfo | null>(null);
  const [retryCount, setRetryCount] = React.useState(0);
  const [checking, setChecking] = React.useState(false);

  const check = React.useCallback(async () => {
    setChecking(true);
    const [healthRes, quotaRes] = await Promise.all([
      checkServerHealth(6000),
      fetchDailyQuota(),
    ]);

    if (healthRes.ok) {
      setStatus("connected");
    } else {
      setStatus("spinning_up");
      setRetryCount((prev) => prev + 1);
    }

    if (quotaRes) {
      setQuota(quotaRes);
    }
    setChecking(false);
  }, []);

  React.useEffect(() => {
    void check();
    // Poll every 5s while spinning up, or every 30s when connected
    const interval = setInterval(
      () => {
        void check();
      },
      status === "spinning_up" ? 5000 : 30000
    );
    return () => clearInterval(interval);
  }, [check, status]);

  if (status === "spinning_up") {
    return (
      <div className="border-b bg-amber-500/10 px-4 py-3 text-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 text-sm">
          <div className="flex items-center gap-3">
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75"></span>
              <span className="relative inline-flex h-3 w-3 rounded-full bg-amber-500"></span>
            </span>
            <div className="flex flex-col sm:flex-row sm:items-center sm:gap-2">
              <span className="font-semibold flex items-center gap-1.5">
                <Loader2 className="h-4 w-4 animate-spin text-amber-600 dark:text-amber-400" />
                Server is spinning up, please wait till the server is connected...
              </span>
              <span className="text-xs text-amber-700 dark:text-amber-300">
                (T4 GPU cold start in progress • 2m idle shutdown • 10m hard session cutoff)
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              Attempt #{retryCount + 1}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={checking}
              onClick={() => void check()}
              className="h-7 text-xs gap-1 border-amber-300 dark:border-amber-700"
            >
              <RefreshCw className={`h-3 w-3 ${checking ? "animate-spin" : ""}`} />
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="border-b bg-muted/40 px-4 py-1.5 text-xs">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Server Connected (T4 GPU Ready)</span>
          </div>
          <span className="text-muted-foreground hidden sm:inline">•</span>
          <span className="text-muted-foreground hidden sm:flex items-center gap-1">
            <Clock className="h-3 w-3" /> Auto-sleep: 2m idle • Max 10m hard cutoff
          </span>
        </div>

        <div className="flex items-center gap-2">
          {quota && (
            <Badge
              variant={quota.remaining === 0 ? "destructive" : "secondary"}
              className="text-[11px] font-normal gap-1"
            >
              <Zap className="h-3 w-3" />
              Daily Quota: {quota.used_today}/{quota.limit} used ({quota.remaining} left)
            </Badge>
          )}
          {quota?.is_exceeded && (
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] text-destructive font-semibold flex items-center gap-1">
                <AlertCircle className="h-3 w-3" /> Limit reached
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  try {
                    await fetch(buildApiUrl("/quota/reset"), { method: "POST" });
                    void check();
                  } catch {}
                }}
                className="h-5 px-1.5 text-[10px] text-destructive hover:bg-destructive/10 border-destructive/30"
                title="Reset quota to 0/5"
              >
                Reset
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
