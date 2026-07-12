"use client";

import { useState } from "react";
import { shareMeetingViaEmail } from "@/app/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/app/components/ui/dialog";
import { Button } from "@/app/components/ui/button";
import { Mail, Check, Plus, X, Loader2 } from "lucide-react";

interface ShareEmailDialogProps {
  meetingId: number;
  attendees: { email: string; name: string }[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ShareEmailDialog({
  meetingId,
  attendees,
  open,
  onOpenChange,
}: ShareEmailDialogProps) {
  const [selectedEmails, setSelectedEmails] = useState<Set<string>>(
    () => new Set(attendees.map((a) => a.email))
  );
  const [customRecipients, setCustomRecipients] = useState<
    { email: string; name: string }[]
  >([]);
  const [newEmail, setNewEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allRecipients = [...attendees, ...customRecipients];
  const allSelected =
    allRecipients.length > 0 &&
    allRecipients.every((r) => selectedEmails.has(r.email));

  const toggleEmail = (email: string) => {
    setSelectedEmails((prev) => {
      const next = new Set(prev);
      if (next.has(email)) {
        next.delete(email);
      } else {
        next.add(email);
      }
      return next;
    });
  };

  const toggleAll = () => {
    if (allSelected) {
      setSelectedEmails(new Set());
    } else {
      setSelectedEmails(new Set(allRecipients.map((r) => r.email)));
    }
  };

  const addCustomEmail = () => {
    const email = newEmail.trim().toLowerCase();
    if (!email) return;
    // Basic email validation
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return;
    // Prevent duplicates
    if (allRecipients.some((r) => r.email === email)) {
      setNewEmail("");
      return;
    }
    setCustomRecipients((prev) => [...prev, { email, name: email }]);
    setSelectedEmails((prev) => new Set([...prev, email]));
    setNewEmail("");
  };

  const removeCustomEmail = (email: string) => {
    setCustomRecipients((prev) => prev.filter((r) => r.email !== email));
    setSelectedEmails((prev) => {
      const next = new Set(prev);
      next.delete(email);
      return next;
    });
  };

  const handleSend = async () => {
    const emails = Array.from(selectedEmails);
    if (emails.length === 0) return;

    setSending(true);
    setError(null);

    try {
      await shareMeetingViaEmail(meetingId, emails);
      setSent(true);
      setTimeout(() => {
        setSent(false);
        onOpenChange(false);
        // Reset state for next open
        setCustomRecipients([]);
        setSelectedEmails(new Set(attendees.map((a) => a.email)));
        setNewEmail("");
        setError(null);
      }, 1500);
    } catch {
      setError("Failed to send email. Please try again.");
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addCustomEmail();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="size-5" />
            Share via Email
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Attendee list */}
          {allRecipients.length > 0 && (
            <div className="space-y-2">
              {/* Select all */}
              <label className="flex items-center gap-2 text-sm font-medium text-stone-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={toggleAll}
                  className="rounded border-stone-300 text-stone-900 focus:ring-stone-500"
                />
                Select all ({allRecipients.length})
              </label>

              <div className="max-h-48 overflow-y-auto space-y-1 border border-stone-200 rounded-lg p-2">
                {allRecipients.map((recipient) => (
                  <label
                    key={recipient.email}
                    className="flex items-center gap-2 text-sm text-stone-700 cursor-pointer hover:bg-stone-50 rounded px-2 py-1.5"
                  >
                    <input
                      type="checkbox"
                      checked={selectedEmails.has(recipient.email)}
                      onChange={() => toggleEmail(recipient.email)}
                      className="rounded border-stone-300 text-stone-900 focus:ring-stone-500"
                    />
                    <span className="flex-1 truncate">
                      {recipient.name !== recipient.email && (
                        <span className="font-medium">{recipient.name} </span>
                      )}
                      <span className="text-stone-500">{recipient.email}</span>
                    </span>
                    {/* Show remove button for custom recipients only */}
                    {customRecipients.some((c) => c.email === recipient.email) && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault();
                          removeCustomEmail(recipient.email);
                        }}
                        className="text-stone-400 hover:text-stone-600"
                      >
                        <X className="size-3.5" />
                      </button>
                    )}
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Add custom email */}
          <div className="flex items-center gap-2">
            <input
              type="email"
              placeholder="Add email address"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 rounded-lg border border-input px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addCustomEmail}
              disabled={!newEmail.trim()}
            >
              <Plus className="size-4" />
              Add
            </Button>
          </div>

          {/* Error message */}
          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={sending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSend}
            disabled={selectedEmails.size === 0 || sending || sent}
          >
            {sending ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Sending...
              </>
            ) : sent ? (
              <>
                <Check className="size-4" />
                Sent!
              </>
            ) : (
              <>
                <Mail className="size-4" />
                Send ({selectedEmails.size})
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
