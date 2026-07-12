// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import type {
  HeroContent,
  Feature,
  UseCase,
  Step,
  Integration,
  Testimonial,
} from "./types";

export const hero: HeroContent = {
  headline: "Turn meetings into actionable notes",
  subheadline:
    "Upload any recording. Get transcripts, summaries, and action items in minutes.",
  primaryCta: { label: "Get Started Free", href: "https://app.zabt.ai/register" },
  secondaryCta: { label: "See How It Works", href: "#how-it-works" },
  image: "/screenshots/homepage-meeting-list.png",
};

export const features: Feature[] = [
  {
    title: "Accurate speaker-labeled transcription",
    description:
      "Powered by WhisperX with automatic speaker detection and word-level timestamps. Upload audio files or paste a YouTube link.",
    bullets: [
      "Automatic speaker diarization",
      "Word-level timestamps",
      "YouTube URL ingestion",
    ],
    image: "/screenshots/transcript-page.png",
    align: "right",
  },
  {
    title: "AI-powered summaries",
    description:
      "Customizable summary templates generate action items, key decisions, highlights, and chapter breakdowns automatically.",
    bullets: [
      "Editable with rich text editor",
      "Multiple summary templates",
      "Export to PDF",
    ],
    image: "/screenshots/ai-powered-summary.png",
    align: "left",
  },
  {
    title: "Medical transcription",
    description:
      "Specialized medical speech recognition via Google MedASR for clinical documentation and medical meetings.",
    bullets: [
      "Medical vocabulary support",
      "Clinical note formatting",
      "HIPAA-aware processing",
    ],
    image: "/screenshots/transcription-page.gif",
    align: "right",
  },
];

export const useCases: UseCase[] = [
  {
    tab: "Team Standup",
    title: "Never miss a standup update",
    description:
      "Record your daily standups and get structured notes with action items assigned to each team member.",
    image: "/screenshots/homepage-meeting-list.png",
  },
  {
    tab: "Client Call",
    title: "Capture every client detail",
    description:
      "Focus on the conversation while Zabt captures requirements, decisions, and follow-ups automatically.",
    image: "/screenshots/ai-powered-summary.png",
  },
  {
    tab: "Medical Consult",
    title: "Clinical documentation made easy",
    description:
      "Medical-grade transcription with specialized vocabulary recognition for patient consultations.",
    image: "/screenshots/transcript-page.png",
  },
  {
    tab: "Lecture",
    title: "Study smarter, not harder",
    description:
      "Record lectures and get chapter-organized notes with key concepts highlighted.",
    image: "/screenshots/new-transcription-progress.png",
  },
];

export const steps: Step[] = [
  {
    icon: "Upload",
    title: "Upload",
    description: "Drop any audio file or paste a YouTube link.",
  },
  {
    icon: "AudioLines",
    title: "Transcribe",
    description: "AI transcribes with speaker labels in minutes.",
  },
  {
    icon: "FileText",
    title: "Summarize",
    description: "Get summaries, action items, and highlights.",
  },
];

export const integrations: Integration[] = [
  { name: "Microsoft Teams", logo: "/logos/microsoftteams.svg", available: true },
  { name: "Outlook Calendar", logo: "/logos/microsoftoutlook.svg", available: true },
  { name: "YouTube", logo: "/logos/youtube.svg", available: true },
  { name: "Google Meet", logo: "/logos/googlemeet.svg", available: false },
  { name: "Zoom", logo: "/logos/zoom.svg", available: false },
  { name: "Slack", logo: "/logos/slack.svg", available: false },
  { name: "Notion", logo: "/logos/notion.svg", available: false },
];

export const testimonials: Testimonial[] = [
  {
    quote:
      "Zabt saves me hours every week. I just upload my meeting recordings and get perfect notes.",
    name: "Jane D.",
    title: "Product Manager",
  },
  {
    quote:
      "The medical transcription feature is a game-changer for our clinic's documentation.",
    name: "Dr. John S.",
    title: "Family Medicine",
  },
  {
    quote:
      "Finally, a transcription tool that actually gets speaker names right.",
    name: "Sarah K.",
    title: "Engineering Lead",
  },
];
