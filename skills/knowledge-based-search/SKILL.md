---
name: knowledge-based-search
description: Search the web and verify current facts, research questions, claims, people, companies, domains, identities, emails, and usernames. Use for requests such as latest, current, look up, research, verify, fact-check, who is, trace, version, or year-specific questions, even when the user does not say search. Drives the keyless kbs CLI and routes to distilled OSINT and research tradecraft.
---

# Knowledge-Based Search

Search and investigation are skills, not a single tool call. This skill picks the
right tool, crafts the query, drills down, verifies, and cites. The deep tradecraft
lives in `references/`, loaded on demand.

## Standing principle

Verify any fact that can change since training before you state it. Versions, APIs,
prices, releases, events, people, and current status all drift. Answering them from
memory is how stale answers slip through. When unsure whether a fact is current, run
`kbs quick` rather than guess.

For stable knowledge about research and investigation method, check the notes in
`references/` first. Also check the book library if `mcp__library` is available. For
anything current or external, search the web first. The best answers draw on both.

When this skill is invoked, run a search before answering any current or external question, the skill exists to search, not to answer from memory.

## Choosing a command

Five commands, a depth ladder from cheap to thorough:

- `kbs plan <query>` - returns a method route, reference notes, and ready
  `kbs search` commands. Run this first for OSINT, fact-checking, source
  evaluation, and entity tracing, then search with the recipes it returns.
- `kbs quick <query>` - fast lookup, ranked links and snippets. Use to confirm
  one current fact, a version, a date, or a name.
- `kbs search <query>` - full pipeline (fetch, embed, rerank, summarize). Returns a
  cited summary plus result refs. Use when the answer needs reading sources, not
  just a link.
- `kbs deep <query>` - bounded multi-round investigation. Decomposes the
  question, searches across sub-queries, returns a structured cited report. Use for
  thorough investigation, comparison across many sources, or an OSINT profile.
- `kbs context <query> --context <text> --session <id>` - context-aware multi-round
  search with session memory. Use when you need broad recall across engines and
  want already-seen URLs suppressed in later calls.
- `kbs get <url-or-ref>` - open one source in full. Use to read one result
  from a prior search without running a whole `kbs deep`.

Start cheap. Escalate only when the cheaper command leaves the question open.

## Query craft

- Search the terms an expert source would use, not the user's casual phrasing.
- Put one idea in each query. Run several narrow queries instead of one broad query.
- Add a year or "latest" when recency matters. Add a site or filetype when you know
  the source shape (`site:`, `filetype:`).
- For dorking and advanced operators, read
  `references/exposingtheinvisible/google-dorking.md`.

## Enforced search contract

`kbs quick`, `search`, `deep`, and `context` enforce the same book-backed query
rules before dispatch. KBS quotes exact identifiers and multi-word names, expands
`filetype:` into sibling formats, preserves advanced operators, and compresses
agent question framing to keywords. The `corrections` trail records every
attempt in human and JSON output, including attempts whose results were discarded.

When results are empty or noisy, KBS may issue at most two corrective retries.
It can relax quotes, reorder operators, add a phrase wildcard after zero or
one hit, or exclude a frequent irrelevant snippet term. This budget is separate
from the documented `deep` and `context` research rounds. Use `--raw` or set
`KBS_NO_ENFORCE=1` when the exact literal query matters. Deep and context still
generate their bounded subqueries in raw mode, but each generated query is sent
verbatim without enforcement.

Results and citations always expose provider provenance in an `engines` list,
even when one provider supplied the item. Citations include a transparent
source-tier `confidence` label. The quality block reports an approximate distinct root-domain count and labels the answer
`corroborated` only when overlapping evidence appears on at least two root
domains. Otherwise it is `single-source`. Low diversity means the top results collapse to one or two
root domains and needs further verification.

## Verify before you trust

- Cross-check a claim against at least two independent sources. One source is a lead,
  not a fact.
- Prefer primary sources (official docs, filings, the original post) over secondary
  reporting.
- Check the date on every source. Stale pages read as current.
- For the full method, read `references/exposingtheinvisible/fact-checking.md` and
  `references/exposingtheinvisible/evaluate-evidence.md`.

## Investigation and OSINT

When the task is to find who, trace an entity, or build a profile, route to the
tradecraft notes by topic. The index lists all 120 notes with a "use when" line each:

**Read `references/README.md` first**, then open the matching note. Common routes:

- People, usernames, emails: `references/osint-techniques/` (search the index for
  username, email, breach, people).
- Domains, websites, infrastructure: `references/exposingtheinvisible/web.md`,
  `references/osint-techniques/` (domain, IP, DNS).
- Companies and ownership: `references/exposingtheinvisible/companies.md`.
- Archiving evidence: `references/exposingtheinvisible/web-archive.md`.
- Geolocation of images: `references/exposingtheinvisible/geolocation.md`.

## Output

Answer with the finding first, then the sources. Cite every claim that came from a
search with its URL. Mark what you could not verify. Keep the answer tight, the
sources complete.
