# explainit — "explain it simply" Telegram bot

A Telegram bot that takes a piece of complex text and explains the hard terms in plain language, as if to a friend — with simple examples and no jargon.

## Architecture

```
bot/   — Telegram bot (python-telegram-bot): requests, premium, podcast and donation menus, feedback collection
app/   — Flask API (`POST /explain`) that builds the prompt and queries an LLM through g4f with provider fallback
db     — PostgreSQL: generation logs and user feedback (SQLAlchemy models)
```

The API is rate-limited and tries several LLM providers in turn until one answers.

## Run

```bash
cp .env.example .env             # BOT_TOKEN and POSTGRES_PASSWORD
docker compose up -d --build     # PostgreSQL, API and bot
```

## Stack

Python, python-telegram-bot, Flask, g4f, PostgreSQL, SQLAlchemy, Docker Compose.
