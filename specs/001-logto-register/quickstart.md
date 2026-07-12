# Quickstart: Logto-Based User Registration

**Feature**: 001-logto-register
**Date**: 2026-02-20

---

## Prerequisites

1. Docker stack running: `docker compose up -d`
2. Logto admin console accessible at `http://localhost:3002`
3. Backend accessible at `http://localhost:8000`
4. Frontend accessible at `http://localhost:3000`

---

## Step 1: Configure Logto Console (one-time setup)

### 1a — Backend M2M Application (for Management API + ROPC)

1. Open Logto admin console: `http://localhost:3002`
2. Go to **Applications → Create application → Machine-to-Machine**
3. Name it "Meetily Backend"
4. Note the **App ID** and **App Secret** → these become `LOGTO_M2M_APP_ID` / `LOGTO_M2M_APP_SECRET`
5. Under **API Resources**, add access to `Logto Management API`
6. Enable the **Resource Owner Password Credentials (ROPC)** grant:
   - Go to **Security → Advanced → Allow ROPC** (or search for "password grant" in settings)
   - If not available at the app level, check Logto Console's global Security settings

### 1b — Frontend Application (for social OIDC authorize URL)

1. Go to **Applications → Create application → Single Page App** (or use an existing one)
2. Name it "Meetily Frontend"
3. Set **Redirect URIs**: `http://localhost:3000/auth/callback`
4. Note the **App ID** → this becomes `NEXT_PUBLIC_LOGTO_APP_ID`

### 1c — Social Connectors

1. Go to **Connectors → Social connectors**
2. Set up **Google Universal** connector (note connector ID: usually `google-universal`)
3. Set up **Microsoft** connector (connector ID: usually `azure-ad`)
4. Set up **Apple** connector (connector ID: usually `apple-universal`)

### 1d — Sign-in Experience

1. Go to **Sign-in experience**
2. Enable **Email/Password** sign-in method
3. Enable all three social connectors added above

---

## Step 2: Configure Backend Environment Variables

Add to `backend/.env` (or docker-compose environment):

```env
LOGTO_M2M_APP_ID=<App ID from Step 1a>
LOGTO_M2M_APP_SECRET=<App Secret from Step 1a>
```

---

## Step 3: Configure Frontend Environment Variables

Add to `frontend-2/.env.local`:

```env
# Backend API (already present)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Logto — public (safe to expose to browser)
NEXT_PUBLIC_LOGTO_ENDPOINT=http://localhost:3001
NEXT_PUBLIC_LOGTO_APP_ID=<App ID from Step 1b>
```

---

## Test Scenario 1: Email/Password Registration — Happy Path (P1)

**Goal**: New user creates a Meetily account via the custom form.

1. Navigate to `http://localhost:3000/register`
2. Verify the page shows: Meetily wordmark, social sign-up buttons, separator, Full Name + Email + Password fields, "Sign up" button
3. Enter: Full Name = "Jane Smith", a fresh email (never registered before), password = "testpass123"
4. Click **Sign up**
5. Verify: **redirected to `http://localhost:3000/`** — no `/login` redirect, no error
6. Verify: dashboard loads (meeting list or empty state), not the login page
7. **Expected**: Account created in Logto, JWT stored in localStorage, user signed in

---

## Test Scenario 2: Duplicate Email Rejection (P1 — error case)

1. Register successfully with email `test@example.com` (Scenario 1)
2. Sign out and navigate to `http://localhost:3000/register`
3. Enter the same email `test@example.com` with any password
4. Click **Sign up**
5. **Expected**: Error message "This email is already registered. Try signing in instead." visible on the register page; user NOT redirected; no new account created

---

## Test Scenario 3: Service Unavailable Error (P1 — error discrimination)

1. Stop the Logto container: `docker compose stop logto`
2. Navigate to `http://localhost:3000/register`
3. Fill the form and click **Sign up**
4. **Expected**: Error message appears but does NOT say "email already registered" — should say something like "Registration service unavailable. Please try again later."
5. Restart Logto: `docker compose start logto`

---

## Test Scenario 4: Google Social Sign-up (P1 — social buttons)

1. Navigate to `http://localhost:3000/register`
2. Click **"Sign up with Google"**
3. Verify: browser redirected **directly to Google's OAuth consent page** (NOT to Logto's hosted page first)
4. Complete Google authentication
5. Verify: redirected back to `http://localhost:3000/` signed in
6. **Expected**: Local User record created with `logto_id` set to Google sub

---

## Test Scenario 5: Microsoft Social Sign-up (P2 — regression check)

1. Navigate to `http://localhost:3000/register`
2. Click **"Sign up with Microsoft"**
3. Complete Microsoft OAuth
4. **Expected**: Redirected to `/`, signed in, User record exists in PostgreSQL

---

## Test Scenario 6: Apple Social Sign-up (P2 — regression check)

1. Navigate to `http://localhost:3000/register`
2. Click **"Sign up with Apple"**
3. Complete Apple OAuth
4. **Expected**: Redirected to `/`, signed in, User record exists in PostgreSQL

---

## Environment Variables Reference

| Variable | Where | Required | Description |
|----------|-------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | frontend | Yes (existing) | Backend base URL |
| `NEXT_PUBLIC_LOGTO_ENDPOINT` | frontend | Yes (new) | Logto OIDC endpoint (public, safe for browser) |
| `NEXT_PUBLIC_LOGTO_APP_ID` | frontend | Yes (new) | Logto frontend app ID (public, safe for browser) |
| `LOGTO_ENDPOINT` | backend | Yes (existing) | Logto endpoint for JWKS validation |
| `LOGTO_APP_ID` | backend | Yes (existing) | Logto app ID for JWKS audience validation |
| `LOGTO_AUDIENCE` | backend | Yes (existing) | Backend API resource identifier |
| `LOGTO_M2M_APP_ID` | backend | Yes (new) | Logto M2M app Client ID for Management API |
| `LOGTO_M2M_APP_SECRET` | backend | Yes (new) | Logto M2M app Client Secret (server-side only) |
