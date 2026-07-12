"use client";

import { useState } from "react";
import { Badge } from "@/app/components/ui/badge";
import { CalendarEventRead, updateCalendarEvent } from "@/app/lib/api";
import { Calendar, Video, Users } from "lucide-react";

const PLATFORM_LABELS: Record<string, string> = {
  teams: "Teams",
  meet: "Google Meet",
  zoom: "Zoom",
};

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  if (d.toDateString() === today.toDateString()) return "Today";
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  if (d.toDateString() === tomorrow.toDateString()) return "Tomorrow";
  return d.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
}

interface CalendarEventListProps {
  events: CalendarEventRead[];
  onEventUpdated: () => void;
}

export function CalendarEventList({ events, onEventUpdated }: CalendarEventListProps) {
  if (events.length === 0) {
    return (
      <div className="text-center py-12 text-stone-500">
        <Calendar className="w-8 h-8 mx-auto mb-3 text-stone-300" />
        <p className="font-medium">No upcoming meetings</p>
        <p className="text-sm mt-1">Connect a calendar to see your meetings here.</p>
      </div>
    );
  }

  const grouped: Record<string, CalendarEventRead[]> = {};
  for (const event of events) {
    const dateKey = formatDate(event.start_time);
    if (!grouped[dateKey]) grouped[dateKey] = [];
    grouped[dateKey].push(event);
  }

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([date, dateEvents]) => (
        <div key={date}>
          <h3 className="text-sm font-medium text-stone-500 mb-3">{date}</h3>
          <div className="space-y-2">
            {dateEvents.map((event) => (
              <CalendarEventRow key={event.id} event={event} onUpdated={onEventUpdated} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function CalendarEventRow({ event, onUpdated }: { event: CalendarEventRead; onUpdated: () => void }) {
  const [toggling, setToggling] = useState(false);

  const handleToggleAutoJoin = async () => {
    setToggling(true);
    try {
      await updateCalendarEvent(event.id, { auto_join: !event.auto_join });
      onUpdated();
    } finally {
      setToggling(false);
    }
  };

  return (
    <div className="flex items-center justify-between border border-stone-200 rounded-lg p-4 bg-white">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="font-medium text-stone-900 truncate">{event.title}</h4>
          {event.conferencing_platform && (
            <Badge variant="outline" className="text-xs shrink-0">
              <Video className="w-3 h-3 mr-1" />
              {PLATFORM_LABELS[event.conferencing_platform] || event.conferencing_platform}
            </Badge>
          )}
          {!event.join_url && (
            <Badge variant="outline" className="text-xs text-stone-400 shrink-0">
              No conferencing link
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-4 mt-1 text-sm text-stone-500">
          <span>{formatTime(event.start_time)} - {formatTime(event.end_time)}</span>
          {event.attendees.length > 0 && (
            <span className="flex items-center gap-1">
              <Users className="w-3 h-3" />
              {event.attendees.length}
            </span>
          )}
          {event.organizer_email && (
            <span className="truncate">{event.organizer_email}</span>
          )}
        </div>
      </div>
      {event.join_url && (
        <label className="flex items-center gap-2 shrink-0 ml-4 cursor-pointer">
          <span className="text-sm text-stone-600">Auto-join</span>
          <button
            role="switch"
            aria-checked={event.auto_join}
            disabled={toggling}
            onClick={handleToggleAutoJoin}
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
              event.auto_join ? "bg-stone-900" : "bg-stone-200"
            } ${toggling ? "opacity-50" : ""}`}
          >
            <span
              className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                event.auto_join ? "translate-x-4" : "translate-x-0.5"
              }`}
            />
          </button>
        </label>
      )}
    </div>
  );
}
