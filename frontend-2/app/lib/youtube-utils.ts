// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
/**
 * Client-side YouTube URL validation utilities.
 */

const YOUTUBE_URL_REGEX =
  /^https?:\/\/(?:www\.|m\.)?(?:youtube\.com\/(?:watch\?.*v=|live\/|shorts\/|embed\/)|youtu\.be\/)[\w-]+/i;

const PLAYLIST_URL_REGEX = /[?&]list=/i;

/** Check if the URL matches a known YouTube video URL pattern. */
export function isValidYoutubeUrl(url: string): boolean {
  return YOUTUBE_URL_REGEX.test(url.trim());
}

/** Check if the URL is a YouTube playlist URL. */
export function isPlaylistUrl(url: string): boolean {
  return PLAYLIST_URL_REGEX.test(url.trim());
}
