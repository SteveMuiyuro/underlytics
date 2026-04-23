import * as React from "react";

import { cn } from "@/lib/utils";

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-5 rounded-[28px] border border-white/70 bg-white/78 px-6 py-6 shadow-[0_24px_80px_-48px_rgba(15,23,42,0.28)] backdrop-blur-xl md:flex-row md:items-end md:justify-between md:px-8",
        className
      )}
    >
      <div className="max-w-3xl space-y-3">
        {eyebrow ? <span className="section-label">{eyebrow}</span> : null}
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950 md:text-4xl">
            {title}
          </h1>
          {description ? (
            <p className="max-w-2xl text-sm leading-7 text-slate-600 md:text-base">
              {description}
            </p>
          ) : null}
        </div>
      </div>

      {actions ? (
        <div className="flex flex-wrap items-center gap-3">{actions}</div>
      ) : null}
    </div>
  );
}
