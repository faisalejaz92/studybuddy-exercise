"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function AdminPage() {
  return (
    <div className="flex h-dvh flex-col">
      <header className="flex items-center gap-4 border-b border-border px-4 py-3">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Chat
        </Link>
        <h1 className="text-lg font-semibold">Admin</h1>
      </header>

      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-foreground">
            Admin Panel
          </h2>
          <p className="mt-2 text-sm text-muted-foreground max-w-md">
            This page is a placeholder for the admin interface. Support needs
            visibility into conversation threads to help users who report issues.
          </p>
        </div>
      </div>
    </div>
  );
}
