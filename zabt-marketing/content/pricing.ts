// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import type { PricingTier, FeatureCategory, FaqItem } from "./types";

export const tiers: PricingTier[] = [
  {
    name: "Basic",
    price: { monthly: 0, yearly: 0 },
    description: "For individuals getting started",
    cta: { label: "Get Started Free", href: "https://app.zabt.ai/register" },
    highlighted: false,
    features: [
      "5 hours of transcription / month",
      "Basic summaries",
      "YouTube URL ingestion",
      "PDF export",
    ],
  },
  {
    name: "Pro",
    price: { monthly: 16, yearly: 12 },
    description: "For professionals who need more",
    cta: { label: "Start Free Trial", href: "https://app.zabt.ai/register" },
    highlighted: true,
    features: [
      "25 hours of transcription / month",
      "Custom summary templates",
      "Medical transcription",
      "Email sharing",
      "Priority processing",
    ],
  },
  {
    name: "Business",
    price: { monthly: 30, yearly: 24 },
    description: "For teams that collaborate",
    cta: { label: "Start Free Trial", href: "https://app.zabt.ai/register" },
    highlighted: false,
    features: [
      "100 hours of transcription / month",
      "Microsoft Teams integration",
      "Calendar sync",
      "Team workspace",
      "Admin controls",
    ],
  },
  {
    name: "Enterprise",
    price: { monthly: null, yearly: null },
    description: "For organizations with custom needs",
    cta: { label: "Contact Sales", href: "mailto:hello@zabt.ai" },
    highlighted: false,
    features: [
      "Unlimited transcription",
      "SSO / SAML",
      "Custom integrations",
      "Dedicated support",
      "SLA guarantee",
    ],
  },
];

export const featureMatrix: FeatureCategory[] = [
  {
    name: "Transcription",
    rows: [
      { name: "Monthly hours", values: { Basic: "5", Pro: "25", Business: "100", Enterprise: "Unlimited" } },
      { name: "Speaker diarization", values: { Basic: true, Pro: true, Business: true, Enterprise: true } },
      { name: "Medical transcription (MedASR)", values: { Basic: false, Pro: true, Business: true, Enterprise: true } },
      { name: "YouTube URL ingestion", values: { Basic: true, Pro: true, Business: true, Enterprise: true } },
    ],
  },
  {
    name: "Summaries",
    rows: [
      { name: "AI summaries", values: { Basic: true, Pro: true, Business: true, Enterprise: true } },
      { name: "Custom templates", values: { Basic: false, Pro: true, Business: true, Enterprise: true } },
      { name: "Action items & highlights", values: { Basic: false, Pro: true, Business: true, Enterprise: true } },
      { name: "Chapter breakdown", values: { Basic: false, Pro: true, Business: true, Enterprise: true } },
    ],
  },
  {
    name: "Integrations",
    rows: [
      { name: "Microsoft Teams bot", values: { Basic: false, Pro: false, Business: true, Enterprise: true } },
      { name: "Outlook calendar sync", values: { Basic: false, Pro: false, Business: true, Enterprise: true } },
      { name: "OneDrive recording pickup", values: { Basic: false, Pro: false, Business: true, Enterprise: true } },
      { name: "Email summary sharing", values: { Basic: false, Pro: true, Business: true, Enterprise: true } },
    ],
  },
  {
    name: "Export & Storage",
    rows: [
      { name: "PDF export", values: { Basic: true, Pro: true, Business: true, Enterprise: true } },
      { name: "Editable summaries", values: { Basic: false, Pro: true, Business: true, Enterprise: true } },
      { name: "Audio storage", values: { Basic: "7 days", Pro: "30 days", Business: "90 days", Enterprise: "Unlimited" } },
    ],
  },
  {
    name: "Support",
    rows: [
      { name: "Community support", values: { Basic: true, Pro: true, Business: true, Enterprise: true } },
      { name: "Priority support", values: { Basic: false, Pro: true, Business: true, Enterprise: true } },
      { name: "Dedicated account manager", values: { Basic: false, Pro: false, Business: false, Enterprise: true } },
      { name: "SLA guarantee", values: { Basic: false, Pro: false, Business: false, Enterprise: true } },
    ],
  },
];

export const faqItems: FaqItem[] = [
  {
    question: "What audio formats do you support?",
    answer: "We support MP3, WAV, M4A, FLAC, OGG, and WebM. You can also paste a YouTube URL and we'll extract the audio automatically.",
  },
  {
    question: "How accurate is the transcription?",
    answer: "Our transcription is powered by WhisperX, which delivers over 95% accuracy for clear audio in English. Accuracy may vary for other languages and noisy recordings.",
  },
  {
    question: "What is medical transcription?",
    answer: "Medical transcription uses Google's MedASR model, which is trained specifically on medical vocabulary. It recognizes clinical terms, drug names, and medical procedures more accurately than general-purpose models.",
  },
  {
    question: "Can I try before I buy?",
    answer: "Yes! The Basic plan is free forever with 5 hours of transcription per month. Pro and Business plans also offer a free trial period.",
  },
  {
    question: "How does the Microsoft Teams integration work?",
    answer: "On the Business plan, our AI notetaker bot joins your Teams meetings automatically via your Outlook calendar. It records the audio and generates transcripts and summaries after the meeting ends.",
  },
  {
    question: "Is my data secure?",
    answer: "Yes. Audio files are encrypted in transit and at rest. Transcripts are stored in our secure database. We do not use your data to train AI models. Enterprise plans include SSO and additional security controls.",
  },
];
