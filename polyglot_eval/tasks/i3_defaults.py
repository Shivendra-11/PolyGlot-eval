"""Self-contained default change for I3 when no operator input is provided."""

DEFAULT_I3_CHANGE = """\
**Change (self-contained):** Add input validation to the primary data-handling module
so invalid or empty inputs fail fast with a clear error instead of raising an unhandled
exception downstream.

**Steps:**
1. Identify the main store/service module (grep for `class`, `def`, or exported handlers).
2. Add a guard at the public API boundary (reject `None`, empty strings, or invalid types).
3. Add or extend a unit test that proves invalid input is rejected.
4. Run the repo test suite (`pytest`, `npm test`, or equivalent) and include full output in the report.

**Constraints:** Minimal diff only. Do not refactor unrelated code. Do not commit or push.
"""
