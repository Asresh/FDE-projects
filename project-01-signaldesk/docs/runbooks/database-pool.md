# Runbook · Database connection pool saturation

1. Confirm connection saturation on the service dashboard.
2. Compare active, idle, and waiting connections with the configured limits.
3. Review recent configuration changes and application deploys.
4. Check database health and whether connection close events are delayed.
5. Escalate to the database on-call owner before changing pool limits or restarting workers.

**Do not** increase limits without checking database capacity. This demo file is an example only.
