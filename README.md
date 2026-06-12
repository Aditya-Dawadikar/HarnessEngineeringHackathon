# Agentic Negotiation & Procurement Platform (Hackathon POC)

Two LLM agents — a `VendorAgent` and a `BuyerAgent` — negotiate a deal
inside a LangGraph state graph, backed by a FastAPI service and a React
(Vite) UI. See `INSTRUCTIONS.md` for the full spec and `TICKETS.md` for
the build plan.

## Quickstart

```bash
./startup.sh
```

This starts the FastAPI backend on `:8000` and the Vite UI dev server on
`:5173` — open the printed URL (e.g. http://localhost:5173) and click
**Start Negotiation**. Stop both with `Ctrl+C`.

- `Backend/README.md` — backend setup, environment variables, tests.
- `UI/README.md` — UI setup, mock mode, API mapping.
- `PIONEER_SETUP.md` — Pioneer.ai LLM integration notes, including the
  model currently used by the agents.
