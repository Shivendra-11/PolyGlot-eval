"""Self-contained default bug scenario for I6 when no operator input is provided."""

DEFAULT_I6_BUG = """\
**Bug (self-contained):** A core function fails on edge-case input — typically empty
collections, `None`, or zero-length strings — causing an unhandled exception or wrong result.

**Steps:**
1. Grep for the main store/service/handler module and its public functions.
2. Write a failing test that calls the function with empty/null input (reproduce first).
3. Trace root cause to exact file + line; cite the incorrect assumption.
4. Apply the minimal fix and confirm the test passes; run the broader test suite if available.

**Example pattern:** `average_*` or `divide` helpers that do not check for empty input before division.

**Constraints:** Reproduce before fixing. Minimal diff. Do not commit or push.
"""
