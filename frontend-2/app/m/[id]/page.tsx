// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";

/**
 * Shortlink route — used by Universal Links and iMessage/email shares.
 * Users with the mobile app installed deep-link straight to the app (iOS + Android
 * handle this before Next.js even renders). Users without the app land here and
 * get redirected to the full meeting view.
 */
export default function MeetingShortLink() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  useEffect(() => {
    const id = params?.id;
    if (id) router.replace(`/meetings/${id}`);
  }, [params, router]);

  return (
    <main className="min-h-screen flex items-center justify-center bg-stone-50">
      <p className="text-sm text-stone-500">Opening meeting…</p>
    </main>
  );
}
