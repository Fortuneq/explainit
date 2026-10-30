# explainit — "explain it simply" Telegram bot

A Telegram bot that takes a piece of complex text and explains the hard terms in plain language, as if to a friend — with simple examples, no jargon, and a strict format. It logs every generation and collects user feedback.

## Architecture

```mermaid
flowchart LR
    U([User]) <--> BOT["bot/<br/>python-telegram-bot"]
    BOT -->|"POST /explain"| APP["app/<br/>Flask API"]
    APP -->|"prompt"| G4F["g4f client<br/>provider fallback"]
    G4F --> P1[Provider 1] & P2[Provider 2] & P3[Provider 3]
    BOT --> DB[("PostgreSQL<br/>generation_log · feedback")]
```

## Request flow

```mermaid
sequenceDiagram
    participant U as User
    participant B as Bot
    participant A as Flask API
    participant L as LLM providers
    participant DB as PostgreSQL
    U->>B: complex text
    B->>A: POST /explain {text}
    A->>A: rate limit (1 req/s) + build prompt
    loop until a provider answers
        A->>L: chat completion
    end
    L-->>A: plain-language explanation
    A-->>B: explanation
    B->>DB: save generation log
    B-->>U: "Explanation: …"
```

## Features

- Plain-language explanations with a fixed output format
- LLM access through g4f with automatic fallback between providers
- Rate limiting and request locking on the API
- Menu: premium, podcast, feedback, donation
- Generation logs and user feedback stored in PostgreSQL (SQLAlchemy)

## Run

```bash
cp .env.example .env             # BOT_TOKEN and POSTGRES_PASSWORD
docker compose up -d --build     # PostgreSQL, API and bot
```

## Stack

Python, python-telegram-bot, Flask, g4f, PostgreSQL, SQLAlchemy, Docker Compose.
