---
phase: 4
round: 1
plan: R01
title: Phase 04 known-issues disposition (zero code changes)
type: remediation
autonomous: true
effort_override: balanced
skills_used: []
files_modified: []
forbidden_commands: []
fail_classifications: []
known_issues_input:
  - '{"test":"pyright server/","file":"server/fetch.py","error":"192: str or int passed where str is required by _forbidden_address. 199: HTTPRedirectHandler.redirect_request override returns object instead of Request or None."}'
  - '{"test":"pyright server/","file":"server/fetch.py","error":"192: str | int passed where str is required by _forbidden_address. 199: HTTPRedirectHandler.redirect_request returns object instead of Request | None."}'
  - '{"test":"pyright server/","file":"server/fetch.py","error":"2 errors: line 192 passes str | int where str is required, line 199 has an incompatible redirect_request override return type"}'
  - '{"test":"pyright server/","file":"server/tests/test_fetch.py","error":"182: None passed where redirect_request requires Request and IO[bytes]. dict passed where redirect_request requires HTTPMessage."}'
  - '{"test":"pyright server/","file":"server/tests/test_fetch.py","error":"182: None passed where redirect_request requires Request and IO[bytes]\u003b dict passed where HTTPMessage is required."}'
  - '{"test":"pyright server/","file":"server/tests/test_fetch.py","error":"3 errors at line 182: None is passed where Request and IO[bytes] are required, and dict is passed where HTTPMessage is required"}'
  - '{"test":"pyright server/","file":"server/tests/test_rag_host_memory.py","error":"3 errors: line 46 accesses unknown Server.ref_dir, lines 56 and 57 assign unknown ModuleType attributes"}'
  - '{"test":"pyright server/","file":"server/tests/test_rag_host_memory.py","error":"46: Server.ref_dir is unknown. 56 and 57: rag_host._IDLE_SECS and rag_host._IDLE_POLL_SECS are unknown ModuleType attributes."}'
  - '{"test":"pyright server/","file":"server/tests/test_rag_host_memory.py","error":"46: Server.ref_dir is unknown. 56: rag_host._IDLE_SECS is unknown. 57: rag_host._IDLE_POLL_SECS is unknown."}'
  - '{"test":"pyright server/","file":"server/tests/test_search_api.py","error":"1 error at line 55: object has no known append attribute"}'
  - '{"test":"pyright server/","file":"server/tests/test_search_api.py","error":"55: object has no known append attribute."}'
known_issue_resolutions:
  - '{"test":"pyright server/","file":"server/fetch.py","error":"192: str or int passed where str is required by _forbidden_address. 199: HTTPRedirectHandler.redirect_request override returns object instead of Request or None.","disposition":"accepted-process-exception","rationale":"Pre-existing pyright finding in a file phase 04 never modified. Unrelated to REQ-04 terminology alternatives. Already promoted to STATE.md Todos for separate remediation."}'
  - '{"test":"pyright server/","file":"server/fetch.py","error":"192: str | int passed where str is required by _forbidden_address. 199: HTTPRedirectHandler.redirect_request returns object instead of Request | None.","disposition":"accepted-process-exception","rationale":"Duplicate wording of the same pre-existing server/fetch.py pyright finding. File untouched by phase 04. Tracked in STATE.md Todos."}'
  - '{"test":"pyright server/","file":"server/fetch.py","error":"2 errors: line 192 passes str | int where str is required, line 199 has an incompatible redirect_request override return type","disposition":"accepted-process-exception","rationale":"Duplicate wording of the same pre-existing server/fetch.py pyright finding. File untouched by phase 04. Tracked in STATE.md Todos."}'
  - '{"test":"pyright server/","file":"server/tests/test_fetch.py","error":"182: None passed where redirect_request requires Request and IO[bytes]. dict passed where redirect_request requires HTTPMessage.","disposition":"accepted-process-exception","rationale":"Pre-existing pyright finding in a test file phase 04 never modified. Unrelated to REQ-04 scope. Tracked in STATE.md Todos. Covers all backlog wordings for this test and file pair."}'
  - '{"test":"pyright server/","file":"server/tests/test_fetch.py","error":"182: None passed where redirect_request requires Request and IO[bytes]\u003b dict passed where HTTPMessage is required.","disposition":"accepted-process-exception","rationale":"Duplicate wording of the same pre-existing server/tests/test_fetch.py finding. File untouched by phase 04. Tracked in STATE.md Todos."}'
  - '{"test":"pyright server/","file":"server/tests/test_fetch.py","error":"3 errors at line 182: None is passed where Request and IO[bytes] are required, and dict is passed where HTTPMessage is required","disposition":"accepted-process-exception","rationale":"Duplicate wording of the same pre-existing server/tests/test_fetch.py finding. File untouched by phase 04. Tracked in STATE.md Todos."}'
  - '{"test":"pyright server/","file":"server/tests/test_rag_host_memory.py","error":"3 errors: line 46 accesses unknown Server.ref_dir, lines 56 and 57 assign unknown ModuleType attributes","disposition":"accepted-process-exception","rationale":"Pre-existing pyright finding in a test file phase 04 never modified. Unrelated to REQ-04 scope. Tracked in STATE.md Todos."}'
  - '{"test":"pyright server/","file":"server/tests/test_rag_host_memory.py","error":"46: Server.ref_dir is unknown. 56 and 57: rag_host._IDLE_SECS and rag_host._IDLE_POLL_SECS are unknown ModuleType attributes.","disposition":"accepted-process-exception","rationale":"Duplicate wording of the same pre-existing server/tests/test_rag_host_memory.py finding. File untouched by phase 04. Tracked in STATE.md Todos."}'
  - '{"test":"pyright server/","file":"server/tests/test_rag_host_memory.py","error":"46: Server.ref_dir is unknown. 56: rag_host._IDLE_SECS is unknown. 57: rag_host._IDLE_POLL_SECS is unknown.","disposition":"accepted-process-exception","rationale":"Duplicate wording of the same pre-existing server/tests/test_rag_host_memory.py finding. File untouched by phase 04. Tracked in STATE.md Todos."}'
  - '{"test":"pyright server/","file":"server/tests/test_search_api.py","error":"1 error at line 55: object has no known append attribute","disposition":"accepted-process-exception","rationale":"Pre-existing pyright finding in a test file phase 04 never modified. Unrelated to REQ-04 scope. Tracked in STATE.md Todos."}'
  - '{"test":"pyright server/","file":"server/tests/test_search_api.py","error":"55: object has no known append attribute.","disposition":"accepted-process-exception","rationale":"Duplicate wording of the same pre-existing server/tests/test_search_api.py finding. File untouched by phase 04. Tracked in STATE.md Todos."}'
must_haves:
  truths:
    - "Every test and file pair in R01-KNOWN-ISSUES.json is covered by a known_issues_input entry with a verbatim backlog error wording"
    - "Each known_issues_input entry has a matching known_issue_resolutions entry with disposition accepted-process-exception"
    - "No product code file changes in this round: git diff against the round start is empty for server/"
    - "server/fetch.py, server/tests/test_fetch.py, server/tests/test_rag_host_memory.py, and server/tests/test_search_api.py are not modified"
  artifacts:
    - {path: ".vbw-planning/phases/04-terminology-alternatives/remediation/qa/round-01/R01-PLAN.md", provides: "disposition record covering all carried known issues", contains: "accepted-process-exception"}
    - {path: ".vbw-planning/phases/04-terminology-alternatives/remediation/qa/round-01/R01-SUMMARY.md", provides: "round outcome summary confirming zero code changes", contains: "accepted-process-exception"}
  key_links:
    - {from: "R01-KNOWN-ISSUES.json", to: "R01-PLAN.md known_issue_resolutions", via: "per test and file pair coverage with verbatim error wording, one resolution per input entry"}
---
<objective>
Disposition the carried known-issues backlog for phase 04. QA passed 29/29 with zero FAIL checks, so this round exists only to record that all carried issues are accepted process exceptions. The backlog's 11 entries are reworded duplicates of 4 pre-existing pyright findings in files phase 04 never touched. 04-VERIFICATION.md confirmed this via git diff against the declared files_modified. The findings predate the phase and sit outside REQ-04 scope. They are already promoted to STATE.md Todos. No product code changes in this round.
</objective>
<context>
@.vbw-planning/phases/04-terminology-alternatives/remediation/qa/round-01/R01-KNOWN-ISSUES.json
@.vbw-planning/phases/04-terminology-alternatives/04-VERIFICATION.md
@.vbw-planning/STATE.md
</context>
<tasks>
<task type="auto">
  <name>Verify known-issue disposition coverage and zero code changes</name>
  <files>
    .vbw-planning/phases/04-terminology-alternatives/remediation/qa/round-01/R01-PLAN.md
  </files>
  <action>
Confirm the disposition record is complete and the round touches no product code. Parse R01-KNOWN-ISSUES.json and this plan's frontmatter. Check that every test and file pair in the backlog is covered by a known_issues_input entry whose error text matches one of that pair's backlog wordings verbatim. Check that each input entry has a known_issue_resolutions entry with identical test, file, and error. Check that every disposition is accepted-process-exception. Run a read-only git status and git diff over server/fetch.py, server/tests/test_fetch.py, server/tests/test_rag_host_memory.py, and server/tests/test_search_api.py. Confirm all four are unmodified. Do not edit any product code. Do not attempt to fix the pyright findings. Record matching known_issue_outcomes in R01-SUMMARY.md frontmatter. Use the same test, file, error, and disposition values as the resolutions.
  </action>
  <verify>
All 4 test and file pairs from R01-KNOWN-ISSUES.json are covered in known_issues_input with verbatim error wordings, each input entry has a matching resolution, and git diff shows no changes under server/.
  </verify>
  <done>
Coverage confirmed for all pairs, working tree clean for server/, and R01-SUMMARY.md records known_issue_outcomes mirroring the resolutions.
  </done>
</task>
</tasks>
<verification>
1. known_issues_input covers all 4 test and file pairs from R01-KNOWN-ISSUES.json, each entry a verbatim backlog wording in {test,file,error} shape.
2. known_issue_resolutions has one entry per input entry, each disposition accepted-process-exception with a rationale naming out-of-scope pre-existence and STATE.md tracking.
3. fail_classifications is empty and files_modified is empty.
4. git diff confirms zero product code changes for the round, including the 4 named pre-existing-issue files.
</verification>
<success_criteria>
- Every carried known issue is dispositioned as accepted-process-exception with a scope-based rationale.
- The deterministic known-issue gate finds full coverage for every test and file pair in the backlog.
- No product code files change in this round.
</success_criteria>
<known_issue_workflow>
- Always include `known_issues_input` and `known_issue_resolutions` in frontmatter. If there are no carried known issues, set both to empty arrays: `known_issues_input: []` and `known_issue_resolutions: []`.
- Copy every carried known issue from the remediation input backlog into `known_issues_input` using the canonical `{test,file,error}` shape.
- Add a matching `known_issue_resolutions` entry for every carried known issue. Use `resolved` when this round fixes it, `accepted-process-exception` when QA should treat it as a verified non-blocking carryover for this phase, and `unresolved` only when the issue is intentionally carried into the next round.
- Do not omit a carried known issue from these arrays. The deterministic gate treats missing coverage as a failed remediation round.
</known_issue_workflow>
<output>
R01-SUMMARY.md
</output>
