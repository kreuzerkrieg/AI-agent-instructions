<!-- Playbook. Not loaded at session start. Load it when the trigger in the
     Playbooks table of global-agents.instructions.md fires. -->

# Playbook: Jira, Confluence, and MCP Servers

Load when working with Jira or Confluence, or when evaluating whether a new MCP server is worth adding.

---

## Jira Integration (Atlassian MCP)

Jira access is available via the **Atlassian MCP server** configured in `~/.config/github-copilot/intellij/mcp.json`:

```json
"atlassian": {
  "type": "http",
  "url": "https://mcp.atlassian.com/v1/mcp"
}
```

### How it works
- The MCP server uses **OAuth via browser** — no API token needed. Authentication goes through the org's Okta SSO.
- On first use in a session, Copilot connects to the MCP server which handles auth transparently.
- The Jira instance is `https://scylladb.atlassian.net`.

### Capabilities
Once connected, the agent can:
- Search Jira issues (JQL queries)
- Create issues (tasks, subtasks, bugs, stories)
- Update issues (status, assignee, description, labels)
- Add comments
- Read Confluence pages

### Usage notes
- The user may need to say "use Atlassian MCP" or similar in their prompt to hint that Jira tools should be used.
- **An empty tool list is not proof the server is down.** In Claude Code the Atlassian tools are
  deferred: they never appear in the visible tool list, only as names in a `<system-reminder>`, and
  the schema loads on `ToolSearch("select:mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql")`.
  Probe with that exact call first. Only if it also fails may the server be disconnected — then ask
  the user to check MCP server status in CLion settings. See *Deferred tools load through ToolSearch*
  in the core instructions for what reading this wrong once cost.

### `contentFormat` decides the markup language — do not mix them
`addCommentToJiraIssue` and `editJiraIssue` take a `contentFormat` of `markdown` or `adf`. There is
**no wiki-markup option**, so Jira's own syntax reaches the page verbatim:

- `markdown` means real Markdown: `###` headings, `` `code` ``, `_italics_`, `*` bullets.
- Jira wiki markup — `h3.`, `{{monospace}}`, `{color}` — is **not** converted. It renders as
  literal text.

On 2026-09-03 a design comment on SCYLLADB-3961 went up with `contentFormat: markdown` but written
in wiki markup. Every `h3.` printed as text and every `{{symbol}}` kept its braces; Ernest fixed the
headings by hand before pointing it out. When correcting a posted comment, pass its `commentId` to
update in place rather than adding a second one — and read the current body first, since the user
may already have edited it.

### Query notes
- The Jira `cloudId` is `scylladb.atlassian.net`.
- Search with `searchJiraIssuesUsingJql`, and pass a **narrow `fields` list**. The default pulls
  `description`, which overflows the result on any query wide enough to be useful.

### Alternative: API token via ~/.netrc
If MCP is unavailable, Jira can also be accessed via REST API with an API token stored in `~/.netrc`:
```
machine scylladb.atlassian.net
  login your.email@scylladb.com
  password YOUR_JIRA_API_TOKEN
```
Generate tokens at: https://id.atlassian.com/manage-profile/security/api-tokens (requires admin permission).

---

## MCP Discovery — Opportunistic Search for New Tools

When you encounter a **tool, service, or platform** during the session that is:
1. mentioned in the codebase, instructions, or by the user, **and**
2. not already configured as an MCP server (check `~/.config/github-copilot/intellij/mcp.json`), **and**
3. a persistent service (not ephemeral infrastructure that only exists during test runs)

…then **once per session**, do a background search for an MCP server:
```
search GitHub: "mcp server <tool-name>" sorted by stars
```
Also check **[cursor.directory](https://cursor.directory/)** — a community-curated directory of MCP servers. It aggregates servers across categories and can surface options that GitHub search misses.

**Evaluation criteria** (all must be met to recommend):
- ≥100 stars (maturity signal)
- Official or well-maintained (recent commits, not archived)
- The user actually interacts with the tool regularly (not just referenced in docs)
- The tool has a stable, persistent endpoint the agent can connect to

**If a good candidate is found**, briefly mention it to the user: *"Found an MCP server for X (N stars, official). Want me to add it?"* — do not add it without asking.

**If nothing qualifies**, silently move on. Do not mention failed searches.

**Track searched tools** in memory for the session to avoid redundant searches. Only search once per tool per session.

**Never use `--prerelease allow` in an MCP `uvx` config** unless an alpha is specifically needed. It once resolved pydantic to `2.14.0a1`, which dropped a symbol the `mcp` SDK imports, crashing the server on startup. Pin the transitive constraint to the latest stable major instead: `--with 'pydantic>=2.10,<2.14'`. To debug an MCP startup `ImportError`: read the traceback, find the resolved archive under `~/.cache/uv/archive-v0/<hash>/lib/python*/site-packages/`, check the installed version, then tighten the constraint in `mcp.json`.

---
