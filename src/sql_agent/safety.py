"""
Shared SQL safety layer for the agent.

Used by BOTH `validatesql.py` (graph node) and `execute_sql.py` (run_sql tool),
so the rules live in exactly one place instead of two copies that can drift
out of sync.

Defense in depth, in this order:
  1. Statement-shape check (AST-based, via sqlglot): only a single SELECT-
     family statement is allowed per call. Stacked statements ("...; DROP
     TABLE ...") and any DML/DDL statement are rejected before they ever
     reach the database - this is checked by *parsing*, not by guessing
     keywords, so it isn't fooled by string concatenation tricks like
     EXEC('DEL'+'ETE FROM x') (which, as it happens, doesn't even parse as
     valid T-SQL and gets rejected for that reason too).
  2. Dangerous call/function check: blocks xp_cmdshell, sp_executesql,
     OPENROWSET, OPENQUERY, etc. even when they appear nested inside
     something sqlglot still classifies as a SELECT (e.g. a table-valued
     function call in the FROM clause).
  3. A cheap word-boundary keyword pre-filter as a fast first line of
     defense. Word-boundaried so it does NOT false-positive on real columns
     like UpdatedAt / DeletedFlag / InsertedBy.

IMPORTANT: this is the application-layer backstop, not the primary control.
The primary control is a read-only SQL Server login (GRANT SELECT only, no
INSERT/UPDATE/DELETE/DDL) for whatever account `db.py` connects with. Even a
perfect validator here is one bug away from a gap; a read-only DB principal
makes the dangerous statements physically impossible regardless of what
string reaches the database.
"""

import re

import sqlglot
from sqlglot import exp

# --- tunables -----------------------------------------------------------

MAX_ROWS = 500              # hard cap on rows returned to the LLM/user
QUERY_TIMEOUT_SECONDS = 30  # pyodbc query timeout

# --- statement-shape allowlist -------------------------------------------

# sqlglot folds CTEs (WITH ...) into the Select node itself rather than
# wrapping it, but we allow exp.With too in case that ever changes across
# sqlglot versions.
_ALLOWED_ROOT_TYPES = (exp.Select, exp.Union, exp.Intersect, exp.Except, exp.With)

# Procedures / table-valued functions that must never appear, even inside
# an otherwise read-only-looking SELECT.
_DANGEROUS_CALL_NAMES = {
    "xp_cmdshell", "sp_executesql", "sp_oacreate", "sp_configure",
    "sp_addextendedproc", "openrowset", "openquery", "opendatasource",
    "openxml", "bulk", "bcp",
}

# Fast pre-filter. \b word boundaries mean "UpdatedAt" does NOT match
# "UPDATE" (no word boundary between the 'E' and the following 'd').
_DANGEROUS_KEYWORD_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|"
    r"DENY|EXEC|EXECUTE|BACKUP|RESTORE|SHUTDOWN|RECONFIGURE)\b",
    re.IGNORECASE,
)


def clean_sql(sql: str) -> str:
    """Strip markdown fences and translate a trailing MySQL-style LIMIT into
    a T-SQL TOP clause.

    The previous version of this function deleted LIMIT n outright, which
    silently turned a row-limited query into an unbounded full-table scan.
    This translates it instead. Native T-SQL OFFSET/FETCH is left alone -
    it's valid syntax (as long as the query has an ORDER BY, which SQL
    Server already requires for it), so there's nothing to fix there.
    """
    sql = re.sub(r"```sql|```", "", sql, flags=re.IGNORECASE).strip()

    limit_match = re.search(r"\bLIMIT\s+(\d+)\s*;?\s*$", sql, re.IGNORECASE)
    if limit_match:
        n = limit_match.group(1)
        sql = sql[: limit_match.start()].rstrip()
        sql = re.sub(
            r"^(\s*SELECT\s+)(DISTINCT\s+)?",
            lambda m: f"{m.group(1)}{m.group(2) or ''}TOP {n} ",
            sql,
            count=1,
            flags=re.IGNORECASE,
        )

    return sql.strip().rstrip(";")


def validate_sql(sql: str) -> tuple[bool, str]:
    """Single source of truth for SQL safety checks.

    Returns (is_valid, error_message). error_message is "" when valid.
    """
    if not sql or not sql.strip():
        return False, "Empty query."

    # 1. Fast keyword pre-filter (cheap, catches the obvious cases early).
    keyword_hit = _DANGEROUS_KEYWORD_RE.search(sql)
    if keyword_hit:
        return False, f"Forbidden keyword: {keyword_hit.group(0).upper()}"

    # 2. Parse and check statement shape. tsql dialect so TOP/IDENTITY/etc.
    #    parse correctly instead of erroring on valid SQL Server syntax.
    try:
        statements = [s for s in sqlglot.parse(sql, read="tsql") if s is not None]
    except Exception as e:
        return False, f"SQL did not parse: {e}"

    if len(statements) != 1:
        return False, "Only a single statement is allowed (no stacked queries)."

    root = statements[0]
    if not isinstance(root, _ALLOWED_ROOT_TYPES):
        return False, f"Only SELECT statements are allowed, got: {type(root).__name__}"

    # 3. Walk the full AST for dangerous calls hiding inside an otherwise
    #    SELECT-shaped statement (e.g. OPENROWSET in a FROM clause).
    for node in root.walk():
        if isinstance(node, exp.Command):
            return False, f"Disallowed SQL construct: {node.sql(dialect='tsql')[:80]}"
        if isinstance(node, (exp.Anonymous, exp.Func)):
            name = (node.name or "").lower()
            if name in _DANGEROUS_CALL_NAMES:
                return False, f"Disallowed function/procedure call: {name}"

    return True, ""