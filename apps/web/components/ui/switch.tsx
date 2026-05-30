"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export function Switch({
  checked,
  onCheckedChange,
  className,
  ...props
}: {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  className?: string;
} & Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "onChange">) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onCheckedChange(!checked)}
      className={cn(
        "relative inline-flex h-5 w-9 shrink-0 rounded-full border border-transparent bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        checked && "bg-primary",
        className
      )}
      {...props}
    >
      <span
        className={cn(
          "pointer-events-none block size-4 translate-x-0 rounded-full bg-background shadow transition-transform",
          checked && "translate-x-4"
        )}
      />
    </button>
  );
}
