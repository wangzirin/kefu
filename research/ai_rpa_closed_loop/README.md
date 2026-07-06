# AI+RPA Closed Loop Research Harness

This folder is an isolated research harness. It does not connect to any real
platform account, browser session, cookie, private WebSocket, or external model.

## Purpose

- Model the safe AI+RPA customer-service loop.
- Prove the sequence from inbound message to knowledge hit, draft, guardrail,
  and dry-run UI action.
- Keep `external_write=false` by default and in all current actions.

## Run

```bash
python3 research/ai_rpa_closed_loop/run_research_loop.py
```

Output is written to:

```text
output/ai_rpa_closed_loop_research/latest_run.json
```

## Current Boundary

- No real platform login.
- No cookies or tokens.
- No private protocol or WebSocket replay.
- No automatic send.
- No browser automation.
- No customer data.

