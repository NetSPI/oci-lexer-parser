# Expected Changes / Future Improvements

This file tracks likely future enhancements so consumers can plan for potential breaking or additive changes.

## Planned Ideas

- Add `tenancy_ocid` (or `tenancy_id`) as a first-class input for policy parsing, so `IN TENANCY` can be resolved directly to an OCID without DEFINE.
- Extend `include_spans` to include line text for each span (useful for UIs and debugging).
- Expand diagnostics with standardized error codes and stable machine‑readable fields.
- Add optional per‑statement IDs in parse outputs to aid diffing and UI mapping.
- Allow explicit control over rule splitting (for tuple/list inputs) without relying on newline heuristics.
- Add optional binary releases for the CLI (e.g., PyInstaller builds for common OS targets).
- Publish docs to the GitHub wiki (or other hosted docs) from the `docs/` folder.
- Add optional span metadata on condition nodes within policy statements (not just statement-level spans).
- Allow passing a list of OCID+Name pairs to enrich outputs with resolved names alongside OCIDs.

## Suggested Contributions

If you plan to implement any of the above, please open an issue or PR so we can coordinate output schema changes.
