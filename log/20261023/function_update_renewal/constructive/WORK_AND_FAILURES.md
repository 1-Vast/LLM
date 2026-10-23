# Work and failures

2026-10-23: Read full user objective and three required historical decisions; additionally read update_value_qualification/DECISION.md to avoid repeating the task-value-selector route. Required objective terminal output was truncated on two broad reads; parent has full objective context and this report preserves its relevant requirements rather than claiming a new full objective audit.

Four concurrent OpenAlex discovery requests completed HTTP200. Five primary arXiv HTML requests completed HTTP200, including parent-supplied TDAL lead. Two biorxiv API HTTP200 responses are 79-byte error documents, not authenticated primary article content. No retry/access circumvention was performed.

First text extraction command failed ModuleNotFoundError: bs4. Switched to standard-library HTMLParser; code and derived texts retained. HTML extracted text includes site script/style text; paper-specific claims were read after the License/Abstract marker. A runpy extraction invocation reprinted already derived texts; it did not download those sources again or run training.

One synthetic operator-equivalence/nullspace check executed once and passed. Zero biological inputs, zero protected/dev numerical reads, zero model fits, zero API-model calls, zero wet experiments. Source scalar errors and the simplest model's equivalence invalidate promotion of the current operator before biological training.
