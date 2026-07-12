# Zabt Mobile

React Native + Expo mobile app. See [design spec](../docs/superpowers/specs/2026-04-16-zabt-mobile-mvp-design.md) and [implementation plan](../docs/superpowers/plans/2026-04-16-mobile-app-mvp.md).

## Local development

Requires the root `.env` to define `EXPO_PUBLIC_API_URL`, `EXPO_PUBLIC_SUPABASE_URL`, `EXPO_PUBLIC_SUPABASE_ANON_KEY` (and optionally `EXPO_PUBLIC_SENTRY_DSN`, `EXPO_PUBLIC_POSTHOG_KEY`). Load them into your shell however you prefer — the project doesn't auto-inject.

```bash
# From the repo root
npm install

# Terminal 1: watch the shared package
npm run dev:shared

# Terminal 2: start Expo
cd zabt-mobile
source ../.env && npx expo start --tunnel
```

Scan the QR with Expo Go for quick UI iteration. Note that Expo Go has limits:

- `expo-secure-store` falls back to AsyncStorage (unencrypted in Expo Go).
- `expo-audio` background mode doesn't work (needs a dev client).
- `expo-notifications` push tokens don't issue (needs a dev client).

For full recording, push, and deep-linking, use an EAS dev client (below).

## Tests

Pure TypeScript unit tests for the upload pipeline:

```bash
npm test
```

Currently 19 tests across `chunker`, `queue`, and the multipart state machine.

## EAS Build (dev client + TestFlight/Play Internal)

First-time setup once per developer:

```bash
npx eas-cli@latest login
```

The project ID (`90eecb1a-3fb7-4c02-b97d-3c634e83fdcc`, owner `skajtech`) is already baked into `app.json`.

### Configure environment variables

EAS reads `EXPO_PUBLIC_*` vars from its own env, not from your local `.env`. Set them once for each build profile:

```bash
# From zabt-mobile/
npx eas-cli env:create --name EXPO_PUBLIC_API_URL --value "https://api.zabt.ai/api/v1" --environment production
npx eas-cli env:create --name EXPO_PUBLIC_SUPABASE_URL --value "<supabase url>" --environment production
npx eas-cli env:create --name EXPO_PUBLIC_SUPABASE_ANON_KEY --value "<anon key>" --environment production
npx eas-cli env:create --name EXPO_PUBLIC_SENTRY_DSN --value "<sentry dsn>" --environment production
# repeat with --environment preview and --environment development for the other profiles
```

### Build

```bash
# Dev client (iOS) — needed for real recording + push testing
npx eas-cli build --profile development --platform ios

# Dev client (Android)
npx eas-cli build --profile development --platform android

# Production iOS (TestFlight)
npx eas-cli build --profile production --platform ios

# Production Android (Play Internal)
npx eas-cli build --profile production --platform android
```

### Submit

```bash
# Edit eas.json submit.production.ios fields first:
#   - appleId (your Apple ID email)
#   - ascAppId (App Store Connect app ID — created after first TestFlight submission)
#   - appleTeamId (visible in Apple Developer portal)

npx eas-cli submit --profile production --platform ios --latest
npx eas-cli submit --profile production --platform android --latest
```

First Android submit requires a Google Play service account JSON at `./secrets/play-service-account.json` (gitignored).

## After first Android build

Retrieve the SHA-256 fingerprint:

```bash
npx eas-cli credentials
```

Update `frontend-2/public/.well-known/assetlinks.json` — replace `REPLACE_AFTER_FIRST_EAS_ANDROID_BUILD` with the real fingerprint. Commit and deploy frontend-2 before expecting Android App Links to work.

## After first iOS build

Retrieve the Apple Team ID (visible in the EAS build output or at developer.apple.com → Membership). Update `frontend-2/public/.well-known/apple-app-site-association` — replace `TEAMID` with the real team ID. Commit and deploy frontend-2.

## Known issues

- **OAuth redirects to `app.zabt.ai`** instead of back to the app (Expo Go only). Expected to resolve in a dev client because `zabt://` scheme registers with the OS at install time. Revisit after first EAS dev client build.

## Architecture

- `app/` — file-based routes (expo-router)
- `components/` — UI primitives and feature-specific components
- `lib/` — business logic (auth, api, queries, recording, upload pipeline, push, analytics)
- `lib/upload/` — chunker + queue + state machine for S3 multipart uploads
- `__tests__/` — Jest tests (node env, no jest-expo — see `jest.config.js`)

Types and the axios client factory come from `@zabt/shared` (the monorepo's `packages/shared`).
