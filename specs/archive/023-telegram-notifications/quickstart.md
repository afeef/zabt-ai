# Quickstart: Owner Notifications via Telegram Bot

## Prerequisites

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather):
   - Send `/newbot` to BotFather
   - Choose a name (e.g., "Zabt Notifications")
   - Choose a username (e.g., `zabt_notifications_bot`)
   - Copy the **bot token** provided

2. Get your **chat ID**:
   - Send any message to your new bot
   - Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find `"chat": {"id": 123456789}` in the response — that's your chat ID

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | No | `""` | Bot token from BotFather. If empty, notifications are silently disabled. |
| `TELEGRAM_CHAT_ID` | No | `""` | Chat ID of the recipient (owner). If empty, notifications are silently disabled. |

Add to your `.env` file on the VPS:

```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=123456789
```

## Verification

After deploying, trigger any event (e.g., log in to the app) and verify a Telegram message arrives in your bot chat.

## Disabling Notifications

Remove or clear `TELEGRAM_BOT_TOKEN` from your `.env` and restart the services. No code changes needed.
