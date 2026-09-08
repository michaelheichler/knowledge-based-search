# Changelog

## 0.4.1 (2026-09-08)

- Codex sessions can load the search skill by reading its full SKILL.md with cat. The gate checks the matching successful tool result and still rejects failed reads and unrelated commands.
- Python 3.12 is the minimum supported version, matching the existing NumPy dependency.
- CI runs the test suite on Python 3.12, 3.13 and 3.14.
