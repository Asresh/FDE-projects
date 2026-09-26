# Runbook · Search indexing backlog

1. Inspect queue depth and oldest-message age.
2. Check worker health, error count, and the last successful checkpoint.
3. Compare the backlog start time with the most recent worker deploy.
4. Avoid replaying the whole queue until duplicate and idempotency behavior is understood.
5. Escalate to Catalog Systems if the backlog continues to grow.

This sample text contains no production instructions.
