from prometheus_client import Counter, Histogram

FLAG_LIST_REQUESTS = Counter(
    "configserver_flag_list_requests_total",
    "Total number of flag list requests",
    ["app", "env"],
)

FLAGS_RETURNED = Histogram(
    "configserver_flags_returned",
    "Number of flags returned per list request",
    ["app", "env"],
    buckets=[1, 5, 10, 25, 50, 100, 200, 500],
)

FLAG_LIST_AT_LIMIT = Counter(
    "configserver_flag_list_at_limit_total",
    "List requests that returned exactly the requested limit (possible truncation)",
    ["app", "env"],
)

FLAG_WRITES = Counter(
    "configserver_flag_writes_total",
    "Total flag write operations",
    ["operation"],
)

FLAG_VALUE_CHANGES = Counter(
    "configserver_flag_value_changes_total",
    "Flag value toggle events",
    ["app", "env", "direction"],
)

VERSION_CONFLICTS = Counter(
    "configserver_version_conflicts_total",
    "Optimistic concurrency conflicts (409) on flag updates",
)

AUTH_FAILURES = Counter(
    "configserver_auth_failures_total",
    "Authentication failures by reason",
    ["reason"],
)
