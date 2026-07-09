---
description: Keyless web search via kbs CLI
argument-hint: "<query>"
platform: pi
---

Search the web for: $ARGUMENTS

Load the knowledge-based-search skill, then run the right `kbs` command for this query. Start cheap:

- `kbs quick "$ARGUMENTS"` for one fast fact, version, date, or name.
- `kbs search "$ARGUMENTS"` for a cited summary that reads sources.
- `kbs deep "$ARGUMENTS"` for a bounded multi-round investigation.
- `kbs get <url>` to drill into one source from a prior search.

Escalate only when the cheaper command leaves the question open.

Answer with the finding first, then cite every claim with its URL. Mark what you could not verify.
