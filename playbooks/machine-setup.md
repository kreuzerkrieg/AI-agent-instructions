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

Large C++ projects (ScyllaDB ~62k files, ClickHouse ~714k files) crash the Copilot language server via V8 heap exhaustion. Every workspace with >50k files needs a `.copilotignore` at the repo root.

**Full documentation:** `~/.config/github-copilot/intellij/copilot-oom-prevention.md`

Quick reference — the global `NODE_OPTIONS=--max-old-space-size=8192` is set in `~/.config/environment.d/copilot.conf`. When opening any new large project, run the assessment commands from the doc to identify heavy directories and create a `.copilotignore`.

---
