<!-- Playbook. Not loaded at session start. Load it when the trigger in the
     Playbooks table of global-agents.instructions.md fires. -->

# Playbook: Machine and Repo Provisioning

Load when setting up a new machine, provisioning a new clone, or when Copilot starts crashing. One-time work — not needed during normal development.

---

## Secret Scanning — Git Hooks

Every machine and repo must have **gitleaks** pre-commit/pre-push hooks installed. These hooks
stop credentials from ever being committed or pushed.

### New-machine setup (run once per machine)

```bash
# 1. Install gitleaks
sudo dnf install gitleaks          # Fedora/RHEL
# brew install gitleaks             # macOS

# 2. Install the custom config (catches Jenkins tokens, netrc patterns, etc.)
cp ~/.config/github-copilot/intellij/scylla/gitleaks.toml ~/.gitleaks.toml

# 3. Install hooks into any repo you work with
bash ~/.config/github-copilot/intellij/scylla/bin/install-secret-hooks ~/Development/scylladb
bash ~/.config/github-copilot/intellij/scylla/bin/install-secret-hooks ~/.config/github-copilot/intellij
# Run for any other repos as needed
```

### What the hooks catch
- **pre-commit**: scans the staged diff before every commit — blocks the commit if a secret is found
- **pre-push**: scans all unpushed commits before push — last-chance safety net
- Custom rules cover: Jenkins API tokens (hex 32-40 chars), netrc `password` lines, high-entropy strings near credential keywords, GitHub PATs (`ghp_...`), AWS access keys

### pre-push on a new branch scans the whole history, not your commits

The pre-push hook resolves "unpushed commits" against the remote. A branch the remote has never seen
has no merge base there, so the range degenerates into the entire history. On a scylladb fork whose
`origin/master` trails `upstream/master`, the first push of any new branch scanned **49,658 commits**
and reported 18 leaks — every one a pre-existing upstream test fixture (`test/pylib/resources/scylla.key`,
`tests/unit/*.key`, Cassandra test-suite strings, seastar websocket constants, docs examples), all
already public in `scylladb/scylladb`.

Do not treat that as a finding, and do not reach for `--no-verify` on the strength of "it looks like
test data". Scope the scan to your own commits first and let the result decide:

```bash
 gitleaks detect --no-banner --log-opts="upstream/master..HEAD" --redact
```

`no leaks found` there plus findings confined to files you never touched is what justifies
`git push --no-verify`. Say so explicitly when reporting the push. Keeping `origin/master` fetched up
to date shrinks the range and avoids the whole situation.

### If a hook fires
1. Remove the secret from the file
2. Use a placeholder: `<JENKINS_API_TOKEN>`, `<YOUR_PASSWORD>`, etc.
3. `git add` and retry the commit
4. If it's a genuine false positive (e.g., a test vector): `git commit --no-verify` — but use this extremely rarely and only after confirming it's not a real credential

### If a secret was already committed
1. `git-filter-repo --replace-text <(echo 'SECRET==>PLACEHOLDER')` — rewrites all history
2. `git push --force`
3. **Rotate the credential immediately** — assume it's compromised

---

## Copilot OOM Prevention

Covered in full by `copilot-oom-prevention.md` (general) and `scylla/copilot-oom-provisioning.md` (ScyllaDB clones). Read those rather than a summary.

---
