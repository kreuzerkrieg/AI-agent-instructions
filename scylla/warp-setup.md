# Cloudflare WARP — ScyllaDB Zero Trust Setup (Fedora)

This doc captures what actually works on Fedora for installing Cloudflare WARP and
enrolling into the ScyllaDB Zero Trust org, plus the `warp-login` automation script
that wraps the painful parts.

> Confluence source of truth (may be out of date for Fedora):
> https://scylladb.atlassian.net/wiki/spaces/c01ea74eb147474597e6340deeeeab1b/pages/45975023

---

## TL;DR — daily use

```bash
warp-login                       # opens browser, polls clipboard for token, registers, connects, picks VNet
warp-cli status                  # verify
warp-cli disconnect              # turn it off
warp-cli connect                 # turn it back on
```

After SSO completes in the browser, **right-click the blue "Open Cloudflare WARP"
button → "Copy Link"**. `warp-login` watches the clipboard and finishes the rest
automatically.

If you prefer not to use clipboard polling:
```bash
warp-login --token "com.cloudflare.warp://scylladb.cloudflareaccess.com/auth?token=eyJ..."
```
(any of: full URL, `com.cloudflare.warp://...` scheme URL, raw token, or full
`<button onclick=...>` HTML pasted from devtools — the script extracts the token.)

---

## One-time install (Fedora)

The official RPM declares a hard dep on `webkit2gtk3`, which is **not available on
Fedora 44+**. The headless `warp-cli` does not actually need WebKit, so install
with `--nodeps`:

```bash
sudo curl -fsSL https://pkg.cloudflareclient.com/cloudflare-warp-ascii.repo \
     -o /etc/yum.repos.d/cloudflare-warp.repo
sudo dnf -y install --downloadonly --destdir=/tmp cloudflare-warp || true
sudo rpm -ivh --nodeps /tmp/cloudflare-warp-*.x86_64.rpm
sudo systemctl enable --now warp-svc
```

Install the Cloudflare root CA so internal HTTPS endpoints validate cleanly:

```bash
sudo curl -fsSL https://developers.cloudflare.com/cloudflare-one/static/Cloudflare_CA.crt \
     -o /etc/pki/ca-trust/source/anchors/Cloudflare_CA.crt
sudo update-ca-trust
```

Install the automation script and the browser-button handler (one-time):

```bash
mkdir -p ~/.local/bin ~/.local/share/applications
ln -sf ~/.config/github-copilot/intellij/scylla/bin/warp-login          ~/.local/bin/warp-login
ln -sf ~/.config/github-copilot/intellij/scylla/bin/warp-login-handler  ~/.local/bin/warp-login-handler
# Override the system desktop file so the button calls our automation:
cat > ~/.local/share/applications/com.cloudflare.warp.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Cloudflare WARP (warp-login)
Comment=Handle com.cloudflare.warp:// deep links via warp-login automation
Exec=/home/CHANGE_ME/.local/bin/warp-login-handler %u
Icon=zero-trust-orange
Terminal=false
NoDisplay=true
StartupNotify=false
MimeType=x-scheme-handler/com.cloudflare.warp;
EOF
sed -i "s|CHANGE_ME|$USER|" ~/.local/share/applications/com.cloudflare.warp.desktop
xdg-mime default com.cloudflare.warp.desktop x-scheme-handler/com.cloudflare.warp
update-desktop-database ~/.local/share/applications
```

---

## What `warp-login` does

1. Ensures `warp-svc` is running (starts it via `sudo systemctl start` if needed).
2. Optionally (default on) disconnects and deletes any existing registration so
   you get a clean enrollment — pass `--no-reset` to skip.
3. Opens `https://scylladb.cloudflareaccess.com/warp` in your default browser
   via `xdg-open`.
4. Polls the clipboard (`wl-paste` on Wayland, `xclip`/`xsel` on X11) for any
   string containing `token=<base64-jwt>`. Recognizes:
   - the `com.cloudflare.warp://…?token=…` URL from "Copy Link" on the button,
   - a plain `https://…?token=…` URL,
   - the raw JWT token string,
   - the entire `<button onclick="…">…</button>` HTML.
5. Normalizes to `https://<org>.cloudflareaccess.com/auth?token=<jwt>` and runs
   `warp-cli registration token <url>`.
6. `warp-cli connect`, waits for `Connected`, then selects the
   `scylla-cloud-prod` VNet (`6666a685-9b3b-4f0c-bd18-36e0ae1c987d`).
7. Smoke-tests `argowkf.app.int.scylla.cloud:443` via `nc -zv`.

Tokens expire in **~60 seconds**, so don't let the page sit. If you see
`registration failed` it's almost always an expired token — rerun and grab a
fresh one.

---

## Button-click path (preferred, after one-time browser approval)

A user-level desktop file is installed at
`~/.local/share/applications/com.cloudflare.warp.desktop` that **overrides**
the system one and points the `com.cloudflare.warp://` scheme at
`warp-login-handler %u` instead of raw `warp-cli`. The handler runs
`warp-login --token <url>`, logs everything to
`~/.local/state/warp-login.log`, and pops a desktop notification on success or
failure.

So in practice the button **does** work — but only after you teach the browser
to launch external apps for this scheme **once**:

- **Firefox.** First time you click the button, Firefox shows
  *"This link needs to be opened with an application"* with a list. Pick
  *"Cloudflare WARP (warp-login)"* and tick *"Always use this application…"*.
  If you previously clicked "Cancel" with the "remember" box ticked, reset it
  in `about:preferences#general` → *Applications* → search `com.cloudflare.warp`
  → set the action to *"Use Cloudflare WARP (warp-login)"*.
- **Chrome/Chromium.** First click shows *"Open Cloudflare WARP (warp-login)?"*
  — accept and tick *"Always allow scylladb.cloudflareaccess.com…"*. To reset,
  delete `~/.config/google-chrome/Default/Preferences` entry under
  `protocol_handler.excluded_schemes`.

Once approved, clicking the blue "Open Cloudflare WARP" button calls
`warp-login-handler` directly — zero terminal needed. The clipboard-polling
path in `warp-login` is the fallback for when the browser still refuses
(corporate policy, Snap/Flatpak sandbox, etc.).

To verify the handler is wired:
```bash
xdg-mime query default x-scheme-handler/com.cloudflare.warp
# expected: com.cloudflare.warp.desktop  (resolves to ~/.local/share/applications/...)
grep ^Exec ~/.local/share/applications/com.cloudflare.warp.desktop
# expected: Exec=/home/<you>/.local/bin/warp-login-handler %u
```

To watch the handler in action:
```bash
tail -f ~/.local/state/warp-login.log
```

---

## Useful one-liners

```bash
# Status and which org I'm in
warp-cli status
warp-cli registration organization

# Switch VNet (e.g. to prod)
warp-cli vnet 6666a685-9b3b-4f0c-bd18-36e0ae1c987d

# Verify internal endpoint
nc -zv argowkf.app.int.scylla.cloud 443
nc -zv thanos.app.int.scylla.cloud 443

# Tail the service log if something is off
journalctl -u warp-svc -f
```

---

## Lessons learned (summary of the painful first attempt)

| Symptom | Real cause | Fix |
| --- | --- | --- |
| `dnf install cloudflare-warp` fails on missing `webkit2gtk3` | RPM has GUI dep that Fedora 44 dropped | `rpm -ivh --nodeps` the downloaded RPM; headless `warp-cli` is enough |
| Blue "Open Cloudflare WARP" button does nothing | Browser silently blocks `com.cloudflare.warp://` scheme | Use `warp-login`, which extracts the token from the clipboard / pasted HTML |
| `warp-cli registration token …` returns 401 within ~1 min | JWT in the enrollment URL is short-lived (~60s) | Get a fresh token and rerun immediately |
| Internal HTTPS endpoints fail TLS | Cloudflare root CA not trusted by system | Install `Cloudflare_CA.crt` into `/etc/pki/ca-trust/source/anchors/`, then `update-ca-trust` |
| Connectivity drops after IPv6 attempt | Some sites try IPv6 first, then time-out and fall back | Normal — IPv4 eventually connects, ignore the warnings |


