# Bug and reliability list

Found during the post-build debug sweep on 2026-06-27. Verified live unless marked otherwise.

## Open

### B1. MCP tools do not surface mid-session
`claude mcp list` shows `knowledge-based-search ✔ Connected`, but the tools are absent from the running session because Claude loads MCP tools at session start and the server was registered after this session began. Not a code defect. Verify the in-Claude tool path from a fresh session. The server logic works (direct `quick_web_search` call returned ranked results live).

### B2. Single flaky SearXNG source, fixed by direct engines
endianness.de is a public instance, rate-limited and intermittent. One probe returned only google plus startpage, a later probe had every backend time out or get suspended. The kindly MCP rides the same SearXNG and returned garbage (Google homepage, an unrelated blog) for an API-pricing query, confirming the instance is the weak link. Fixed: direct google, bing, duckduckgo scrapers added so SearXNG is one source among several. Live result on "openai news": duckduckgo lite returned 5 hits, merged total 9 with searxng. DuckDuckGo plus SearXNG is the working keyless stack.

### B4. Google and Bing keyless scraping is blocked
Verified live 2026-06-27. Google returns an enablejs plus challenge page (requires JavaScript, no header tweak recovers it). Bing returns a captcha challenge regardless of headers. So keyless google and bing return [] right now. Google works only through the optional Custom Search key path (`google_api_key` plus `google_cx`). Bing has no key option (API retired). The scrapers stay in, they soft-fail fast and may catch an occasional unblocked response. Playwright would render the JS but the owner ruled it out.

## Resolved or closed

### B3. Codex health "Unsupported" is not a failure
The "Unsupported" label is the Auth column in `codex mcp list`, not Status. Status is `enabled`, identical to all 9 Codex servers (serena, lad, kindly, etc.). It means no OAuth or bearer auth, correct for a stdio server. No action.

## Engine API landscape (verified live 2026-06-27)

- Bing Search API retired August 11 2025, all instances decommissioned, no new keys. Only Microsoft path is Grounding with Bing Search in Azure AI Foundry (full Azure lock-in). Keyless HTML scraping is the only option for bing.
- Google Custom Search JSON API still exists, free tier about 100 queries per day then paid. Reliable keyed path. Optional config keys `google_api_key` plus `google_cx` enable it, else scrape google.com. (Free-tier number from prior knowledge, not re-verified this session.)
- DuckDuckGo has no web-results API, only the Instant Answer API which returns no result lists. Keyless scraping of the html or lite endpoint is the only option.
