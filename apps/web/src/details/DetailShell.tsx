"use client";

import Link from "next/link";
import React, { ReactNode } from "react";

import { AuthStatus } from "../auth/AuthStatus";

export function DetailShell({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="border-b border-black/10 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <Link href="/" className="w-fit">
            <div className="text-xl font-bold">DealMoa</div>
            <p className="text-xs font-semibold text-signal">검색 중심 커머스</p>
          </Link>
          <AuthStatus />
        </div>
      </header>
      {children}
    </main>
  );
}

export function formatCurrency(value: number, currency: string) {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency,
    maximumFractionDigits: 0
  }).format(value);
}

export function statusLabel(status: string) {
  return `상태 ${status}`;
}

export function specsEntries(specs: Record<string, unknown> | null) {
  if (!specs) {
    return [];
  }
  return Object.entries(specs).map(([key, value]) => `${key}: ${String(value)}`);
}
