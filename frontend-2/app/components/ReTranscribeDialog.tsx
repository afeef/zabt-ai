"use client";

import { useState } from "react";
import { LanguagePicker } from "./LanguagePicker";
import { reTranscribeMeeting } from "@/app/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/app/components/ui/dialog";
import { Button } from "@/app/components/ui/button";
import { Loader2 } from "lucide-react";

type Props = {
  meetingId: number;
  currentLanguage: string | null;
  open: boolean;
  onClose: () => void;
  onDispatched: (newLanguage: string) => void;
};

export function ReTranscribeDialog({
  meetingId,
  currentLanguage,
  open,
  onClose,
  onDispatched,
}: Props) {
  const [lang, setLang] = useState<string | null>(currentLanguage);
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    if (!lang) return;
    setSubmitting(true);
    try {
      await reTranscribeMeeting(meetingId, lang);
      onDispatched(lang);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose(); }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Re-transcribe in different language</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <p className="text-sm text-stone-600">
            Pick the language to use. The meeting will be queued and transcribed again.
          </p>
          <LanguagePicker
            value={lang}
            onChange={setLang}
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={!lang || submitting}>
            {submitting ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Starting…
              </>
            ) : (
              "Re-transcribe"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
