# SEO Tooling

## DataForSEO (plan of record — NOT yet activated)
Provision in an interactive session (this agent session is non-interactive and
cannot run the MCP auth flow):

    claude mcp add dataforseo -- npx -y dataforseo-mcp-server
    # then set DATAFORSEO_USERNAME / DATAFORSEO_PASSWORD in the MCP env

Endpoints we will use:
- Keywords Data (search volume, CPC)
- SERP (live results, PAA, featured snippets)
- DataForSEO Labs (ranked_keywords / competitors_domain for keyword-gap)
- Backlinks (referring domains)

Cost model: pay-as-you-go, ~$0.05–0.10 per live SERP call, keyword data cheap,
~$50 minimum deposit. Batch queries; cache results into `keywords.md`.

## Free layer (use until DataForSEO is live)
WebSearch, firecrawl / `/scrape`, Google autocomplete, `/browse` for live SERP.

## First-party (free)
Google Search Console + Bing Webmaster. Verify via meta tags added in Phase 1
(`metadata.verification` in `app/layout.tsx`). Bing matters — it powers ChatGPT search.
