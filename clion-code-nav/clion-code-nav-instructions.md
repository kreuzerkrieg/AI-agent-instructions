# clion-code-nav — Project Instructions

Load when the active workspace is `clion-code-nav` (the CLion MCP code-navigation plugin).

## Versioning convention

The plugin uses a strict three-part version `MAJOR.MINOR.BUILD` defined by the
`pluginVersion` property in `gradle.properties`:

- **MAJOR** — bump on breaking protocol/API changes that older AI agents/clients can't tolerate.
- **MINOR** — bump on new tools, new request/response fields, or other backward-compatible feature additions.
- **BUILD** — the last component is a **monotonically increasing build number**. Bump it on
  **every iteration** that produces a new artifact — bug fixes, doc tweaks, internal refactors,
  or anything the user might install. Never reuse a build number.

### Mandatory bump procedure (every deploy)

Before any `./gradlew buildPlugin` that will be deployed:

1. Open `gradle.properties` and increment the BUILD component of `pluginVersion`
   (e.g., `1.2.34` → `1.2.35`). Never deploy two artifacts with the same version.
2. MAJOR/MINOR are bumped only when justified per the rules above; when MINOR is bumped, BUILD
   resets to `0`.
3. The version is propagated automatically — `plugin.xml` (`<version>`), the generated
   `version.txt` resource consumed by `SERVER_VERSION`, and the `/api/status` + MCP `serverInfo`
   responses — so callers can always read it back via `clion_codenav_status`.
4. Commit the version bump together with the changes it ships (do not split into a separate
   "bump version" commit unless that's all the iteration contains).

### Why this matters

When the user reports feedback from the deployed plugin, the response to
`clion_codenav_status` includes the version field. Tying every report to a specific build
number is the only reliable way to distinguish "already fixed but you're testing a stale
build" from "still broken in the latest build".

