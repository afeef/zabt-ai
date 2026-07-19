# GEO Citation Monitor

Tracks whether LLMs recommend/cite zabt.ai for buyer questions.

## Setup
    cp .env.example .env   # fill at least one key
## Run
    cd zabt-marketing
    node --env-file=scripts/geo-monitor/.env node_modules/.bin/tsx scripts/geo-monitor/run.ts
    # or, if vars are exported in your shell:
    npm run geo:monitor
    npm run geo:summary

Results append to `results/YYYY-MM-DD.jsonl`. Edit `questions.json` to change the
prompt bank (keep it in sync with `docs/seo/geo-questions.md`).
