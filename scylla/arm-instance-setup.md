# ARM Test Instance — Full Setup Reference

**Last updated:** 2026-05-20

---

## 1. Instance Details

| Field | Value |
|-------|-------|
| **Instance ID** | `i-05ccc6ae22cf5bc94` |
| **Region** | `us-east-1` (N. Virginia) |
| **Instance type** | `c6g.8xlarge` (32 vCPUs, 64 GB RAM, AWS Graviton2, aarch64) |
| **OS** | Ubuntu 24.04 LTS (aarch64) |
| **Current public IP** | `52.201.215.77` ⚠️ *changes on stop/start — always re-check after starting* |
| **User** | `ubuntu` |

---

## 2. SSH Access

### Connect
```bash
ssh -i ~/Downloads/ernest.pem ubuntu@3.91.29.41
```

### PEM file: current location
`~/Downloads/ernest.pem` — **not ideal**. See section 5 for proper placement.

### After starting the instance (IP will change!), get the new IP:
```bash
aws --profile 797456418907-DevOpsAccessRole ec2 describe-instances \
  --instance-ids i-05ccc6ae22cf5bc94 --region us-east-1 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text
```

---

## 3. AWS CLI — Managing the Instance

### Active profile
```bash
export AWS_PROFILE=797456418907-DevOpsAccessRole
# or pass --profile to every command
```

Verify credentials work:
```bash
aws --profile 797456418907-DevOpsAccessRole sts get-caller-identity
# Expected: {"Account": "797456418907", "Arn": "...assumed-role/DevOpsAccessRole/<your-email>@scylladb.com", ...}
```

### Start the instance
```bash
aws --profile 797456418907-DevOpsAccessRole ec2 start-instances \
  --instance-ids i-05ccc6ae22cf5bc94 --region us-east-1
```

### Stop the instance (save money when not using)
```bash
aws --profile 797456418907-DevOpsAccessRole ec2 stop-instances \
  --instance-ids i-05ccc6ae22cf5bc94 --region us-east-1
```

### Wait until running + get new public IP in one shot
```bash
aws --profile 797456418907-DevOpsAccessRole ec2 wait instance-running \
  --instance-ids i-05ccc6ae22cf5bc94 --region us-east-1 && \
aws --profile 797456418907-DevOpsAccessRole ec2 describe-instances \
  --instance-ids i-05ccc6ae22cf5bc94 --region us-east-1 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
```

### Check instance state
```bash
aws --profile 797456418907-DevOpsAccessRole ec2 describe-instances \
  --instance-ids i-05ccc6ae22cf5bc94 --region us-east-1 \
  --query 'Reservations[0].Instances[0].{State:State.Name,IP:PublicIpAddress,Type:InstanceType}'
```

---

## 4. AWS Credentials — How to Refresh

Credentials are **temporary STS tokens** that expire every ~6 hours. The tool is
**`gimme-aws-creds`** (Okta TOTP → STS), installed in the scylladb venv.

**Check current expiry:**
```bash
grep x_security_token_expires ~/.aws/credentials
# look at the entry below [797456418907-DevOpsAccessRole]
```

### Automated refresh (standard workflow for the AI agent)

A wrapper script handles everything automatically. **The only input needed from the user
is the 6-digit Google Authenticator code.**

**Step 1** — Agent asks the user for the TOTP code via `ask_questions`.

**Step 2** — Agent runs immediately (the code expires in ~30s so don't delay):
```bash
refresh-aws-creds <6-digit-code>
```

The script (`~/.local/bin/refresh-aws-creds`) handles all other prompts:
- Password → read from `~/.config/gimme-aws-creds-pass` (chmod 600)
- "Save password in keyring?" → `y`
- Factor selection → `0` (Google TOTP, always)
- Role selection → `0` (DevOpsAccessRole, always)

**Config file:** `~/.okta_aws_login_config`
- Okta org: `https://scylladb.okta.com`
- Username: `<your-email>@scylladb.com`
- `remember_device = True`, `aws_default_duration = 21600` (6 hours)

**Verify credentials are valid:**
```bash
aws --profile 797456418907-DevOpsAccessRole sts get-caller-identity
```

### Dependencies
- `gimme-aws-creds` — in `~/Development/scylladb/venv/bin/`
- `pexpect` — installed in system venv (`pip install pexpect`)
- `~/.config/gimme-aws-creds-pass` — Okta password, chmod 600 (local only, not in git)

### New machine setup (run once per machine — laptop, desktop, etc.)

The `refresh-aws-creds` script lives in the instructions repo at `scylla/bin/refresh-aws-creds`.
After `git pull --rebase`, run this to install it:

```bash
# 1. Install pexpect into the system Python (needed by the script's shebang /usr/bin/env python3)
pip install pexpect

# 2. Install the script
mkdir -p ~/.local/bin
cp ~/.config/github-copilot/intellij/scylla/bin/refresh-aws-creds ~/.local/bin/refresh-aws-creds
chmod +x ~/.local/bin/refresh-aws-creds

# 3. Create the Okta config (if not already present)
#    Copy from this machine: ~/.okta_aws_login_config
#    Or create it — content is in arm-instance-setup.md section below.

# 4. Create the password file — ask the user for their Okta password
printf '<okta-password>\n' > ~/.config/gimme-aws-creds-pass
chmod 600 ~/.config/gimme-aws-creds-pass

# 5. Verify
refresh-aws-creds --help 2>/dev/null || python3 ~/.local/bin/refresh-aws-creds --help
```

### `~/.okta_aws_login_config` content (for new machine setup)

```ini
[DEFAULT]
okta_org_url = https://scylladb.okta.com
okta_auth_server =
client_id = 0oab7271m7nRkKmlw5d7
gimme_creds_server = appurl
aws_appname =
write_aws_creds = True
cred_profile = acc-role
okta_username = <your-email>@scylladb.com
app_url = https://scylladb.okta.com/home/amazon_aws/0oa2uxps59d96E5Cj5d7/272
resolve_aws_alias = False
include_path = False
remember_device = True
preferred_mfa_type = Okta
aws_default_duration = 21600
output_format =

[tests]
inherits = DEFAULT
aws_rolename = arn:aws:iam::797456418907:role/DeveloperAccessRole
```

---

## 5. PEM File — Multi-Machine Setup

The SSH key `ernest.pem` is needed on both **laptop** and **desktop** to SSH into the ARM instance.

### Immediate fix: move to the standard SSH directory
```bash
# On each machine:
cp ~/Downloads/ernest.pem ~/.ssh/ernest.pem
chmod 600 ~/.ssh/ernest.pem
# Now connect with:
ssh -i ~/.ssh/ernest.pem ubuntu@<IP>
```

### Cross-machine strategy options

**Option 1: 1Password (recommended if ScyllaDB uses it)**  
Store the PEM as an SSH key in 1Password. 1Password's SSH agent serves it to all machines
automatically — no file to sync.
- macOS/Windows: 1Password app integrates with OS SSH agent
- Linux: `eval $(op agent)` or configure `~/.ssh/config` to use 1Password agent socket
- Benefit: key never stored on disk unencrypted; works on any machine where you're signed in to 1Password

**Option 2: Bitwarden / other password manager**  
Store as a secure note or SSH key. Pull to each machine manually:
```bash
# After pulling from vault:
echo "<key content>" > ~/.ssh/ernest.pem && chmod 600 ~/.ssh/ernest.pem
```

**Option 3: Encrypted file in a private git repo or secure sync**  
```bash
gpg --symmetric --cipher-algo AES256 ~/.ssh/ernest.pem  # produces ernest.pem.gpg
# Store ernest.pem.gpg in a private git repo or secure cloud storage
# On each machine: gpg -d ernest.pem.gpg > ~/.ssh/ernest.pem && chmod 600 ~/.ssh/ernest.pem
```

**Option 4: AWS Systems Manager Session Manager (no PEM needed at all)**  
If the instance has the SSM agent installed and the IAM role allows it:
```bash
aws --profile 797456418907-DevOpsAccessRole ssm start-session \
  --target i-05ccc6ae22cf5bc94 --region us-east-1
# No PEM needed! Auth via AWS credentials only.
```
⚠️ *Requires SSM agent on instance + instance profile with ssm permissions — check if set up.*

### Recommended `.ssh/config` entry (once PEM is in ~/.ssh/)
```
Host arm-scylla
    HostName 3.91.29.41       # update IP after each start
    User ubuntu
    IdentityFile ~/.ssh/ernest.pem
    ServerAliveInterval 60
    ServerAliveCountMax 3
```
Then simply: `ssh arm-scylla`

---

## 6. Software Setup on the ARM Instance

The instance was set up to run ScyllaDB integration tests with a Fedora-toolchain-built binary
on Ubuntu. All fixes are already applied — this section is for reference if the instance is
ever rebuilt.

### Repository
```
~/Development/scylladb   (git clone of scylladb/scylladb)
```

### Scylla binary
Built with the Fedora toolchain container on this Ubuntu host:
```bash
cd ~/Development/scylladb
tools/toolchain/dbuild ninja build/release/scylla
```

### Fedora runtime libraries
Extracted from the toolchain container into `/usr/local/lib/scylla-toolchain/` to satisfy
shared library dependencies (Fedora builds need Fedora runtime versions of `libcares`,
`libfmt`, `libprotobuf`, `libicuXX`, etc.):
```bash
# One-time setup (already done):
sudo mkdir -p /usr/local/lib/scylla-toolchain
docker run --rm docker.io/scylladb/scylla-toolchain:fedora-43-20260304 \
  tar -chf - /usr/lib64/libcares.so* /usr/lib64/libfmt.so* ... | \
  sudo tar -xhf - -C /usr/local/lib/scylla-toolchain --strip-components=3
echo '/usr/local/lib/scylla-toolchain' | sudo tee /etc/ld.so.conf.d/scylla-toolchain.conf
sudo ldconfig
```

⚠️ **`LD_LIBRARY_PATH` is required** — Ubuntu's `libcares.so.2` (2.12.0) is too old; despite
being registered in ldconfig, Ubuntu's system lib takes precedence. Always run tests with:
```bash
LD_LIBRARY_PATH=/usr/local/lib/scylla-toolchain ./test.py ...
```

### Python virtual environment
```bash
python3 -m venv ~/scylla-test-venv
source ~/scylla-test-venv/bin/activate
pip install -r test/requirements.txt   # or install packages manually
```

### Ubuntu-specific patches applied to the codebase
These are **local changes on the instance** (not pushed upstream yet):

#### 1. `test/resource/slapd.conf` — Added `moduleload back_mdb.so`
Ubuntu packages `back_mdb.so` as a loadable module (unlike Fedora where it's compiled in).
Without this, slapd fails with `Unrecognized database type (mdb)`.
```
# Added after rootdn line:
modulepath /usr/lib/ldap
moduleload back_mdb.so
```

#### 2. `test/pylib/ldap_server.py` — Strip CRC32 checksums after sed
Ubuntu's `sed` invalidates embedded CRC32 checksums in LDIF config files. Without this fix,
slapd fails with `ldif_read_file: checksum error`.
```python
# After the olcPidFile sed substitution:
subprocess.check_output(
    ['find', instance_path, '-type', 'f', '-name', '*.ldif', '-exec',
     'sed', '-i', '/^# CRC32/d', '{}', ';'],
    stderr=subprocess.STDOUT
)
```

#### 3. `/etc/openldap` → `/etc/ldap` symlink
Ubuntu puts the LDAP schemas at `/etc/ldap/` while tests reference `/etc/openldap/`:
```bash
sudo ln -sfn /etc/ldap /etc/openldap
```

#### 4. AppArmor disabled for slapd
Ubuntu's AppArmor restricts slapd to specific paths incompatible with the test's temp dirs:
```bash
sudo ln -s /etc/apparmor.d/usr.sbin.slapd /etc/apparmor.d/disable/usr.sbin.slapd
sudo apparmor_parser -R /etc/apparmor.d/usr.sbin.slapd
```

#### 5. Additional Ubuntu packages required
These are not present on Ubuntu by default but needed by tests:
```bash
# saslauthd — required by SASL/LDAP tests
sudo apt-get install -y sasl2-bin

# toxiproxy-server (aarch64 build) — required by network fault injection tests
# Ubuntu apt doesn't have toxiproxy; install arm64 binary from GitHub releases
TOXI_VER=2.9.0
curl -sL "https://github.com/Shopify/toxiproxy/releases/download/v${TOXI_VER}/toxiproxy-server-linux-arm64" \
  -o /tmp/toxiproxy-server
sudo install -m755 /tmp/toxiproxy-server /usr/local/bin/toxiproxy-server
sudo install -m755 /tmp/toxiproxy-cli /usr/local/bin/toxiproxy-cli || true
# Verify:
toxiproxy-server --version
```

#### 6. pytest version — must be 9.0.3+
Ubuntu's default `pytest` (or older pip installs) will be 7.x or 8.x and fail with
`AttributeError: '_StoreTrueAction' object has no attribute 'deprecated'`
or similar. Always install the required version:
```bash
source ~/scylla-test-venv/bin/activate
pip install --ignore-installed "pytest==9.0.3"
# Verify:
pytest --version  # should show 9.0.3
```

---

## 7. Running Tests

### Full test run command
```bash
source ~/scylla-test-venv/bin/activate
cd ~/Development/scylladb
LD_LIBRARY_PATH=/usr/local/lib/scylla-toolchain ./test.py \
  --no-gather-metrics --mode release \
  test/cluster/object_store/test_backup.py::test_restore_tablets[gs-topology1]
```

### Multi-phase flaky-test reproduction loop

When investigating a flaky/intermittent bug, use a multi-phase reproduction loop that
escalates from faster builds (release) to more debuggable ones (debug, dev). This loop:
- Runs N×100 repetitions per phase
- Stops immediately on first failure and archives artifacts
- Automatically moves to the next phase if no failure found
- Logs all results to `~/test-repro-logs/summary.log`

**Template script** (save as `~/repro-loop.sh` on the ARM instance):
```bash
#!/bin/bash
VENV=~/scylla-test-venv
SCYLLA_DIR=~/Development/scylladb
export LD_LIBRARY_PATH=/usr/local/lib/scylla-toolchain

TEST="test/cluster/object_store/test_backup.py::test_restore_tablets[gs-topology1]"
LOGDIR=~/test-repro-logs
RELEASE_ATTEMPTS=10
DEBUG_ATTEMPTS=50
DEV_ATTEMPTS=50
REPS=100

source "$VENV/bin/activate"
cd "$SCYLLA_DIR"
mkdir -p "$LOGDIR"

run_phase() {
    local MODE=$1 ATTEMPTS=$2
    echo "=== Phase: $MODE — $ATTEMPTS attempts × $REPS reps ===" | tee -a "$LOGDIR/summary.log"
    for i in $(seq 1 "$ATTEMPTS"); do
        echo "[$MODE] Attempt $i/$ATTEMPTS — $(date)" | tee -a "$LOGDIR/summary.log"
        if ./test.py --no-gather-metrics --mode "$MODE" --repeat "$REPS" --max-failures 1 "$TEST" \
              >> "$LOGDIR/${MODE}-attempt-${i}.log" 2>&1; then
            echo "[$MODE] Attempt $i PASSED" | tee -a "$LOGDIR/summary.log"
        else
            echo "[$MODE] Attempt $i FAILED — archiving logs" | tee -a "$LOGDIR/summary.log"
            cp -r testlog "$LOGDIR/${MODE}-failure-${i}-testlog" 2>/dev/null || true
            echo "REPRODUCTION FOUND in $MODE attempt $i" | tee -a "$LOGDIR/summary.log"
            exit 0
        fi
    done
    echo "[$MODE] No failure in $ATTEMPTS attempts" | tee -a "$LOGDIR/summary.log"
}

run_phase release "$RELEASE_ATTEMPTS"
run_phase debug   "$DEBUG_ATTEMPTS"
run_phase dev     "$DEV_ATTEMPTS"

echo "=== All phases complete — no reproduction ===" | tee -a "$LOGDIR/summary.log"
```

**Launch it in the background (survives SSH disconnects):**
```bash
chmod +x ~/repro-loop.sh
nohup ~/repro-loop.sh > ~/repro-loop-stdout.log 2>&1 &
echo "PID: $!"
```

**Monitor progress from local machine:**
```bash
ssh arm-scylla 'tail -20 ~/test-repro-logs/summary.log'
```

### Local auto-shutdown watcher

Run this on the **local machine** to monitor the ARM instance and stop it once the repro
loop finishes (so it doesn't sit running and billing after the test):

```bash
#!/bin/bash
# /tmp/watch-and-shutdown.sh
SCRATCH=~/.config/JetBrains/CLion2026.1/scratches/GitHubCopilot/scylladb-repro-results.md
INSTANCE_ID=i-05ccc6ae22cf5bc94
REGION=us-east-1
AWS_PROFILE=797456418907-DevOpsAccessRole

echo "Watcher started $(date)" > /tmp/watch-and-shutdown.log

while ssh arm-scylla 'pgrep -f repro-loop.sh > /dev/null' 2>/dev/null; do
    echo "$(date): repro loop still running" >> /tmp/watch-and-shutdown.log
    sleep 60
done

echo "$(date): repro loop finished — collecting results" >> /tmp/watch-and-shutdown.log
mkdir -p "$(dirname "$SCRATCH")"
ssh arm-scylla 'cat ~/test-repro-logs/summary.log' > "$SCRATCH"

echo "$(date): stopping instance $INSTANCE_ID" >> /tmp/watch-and-shutdown.log
aws --profile "$AWS_PROFILE" ec2 stop-instances --instance-ids "$INSTANCE_ID" --region "$REGION"
echo "$(date): done" >> /tmp/watch-and-shutdown.log
```

```bash
chmod +x /tmp/watch-and-shutdown.sh
nohup /tmp/watch-and-shutdown.sh > /tmp/watch-and-shutdown.log 2>&1 &
echo "Watcher PID: $!"
```

⚠️ **AWS credentials expire every ~6 hours.** If the watcher runs longer than that, the
`ec2 stop-instances` call will fail. Check `/tmp/watch-and-shutdown.log` and stop manually
if needed:
```bash
aws --profile 797456418907-DevOpsAccessRole ec2 stop-instances \
  --instance-ids i-05ccc6ae22cf5bc94 --region us-east-1
```

---

## 8. Repro Loop — Lessons Learned

### toxiproxy leftover causes false positives (2026-05-20)

When running `test.py --repeat N` in a loop, the toxiproxy-server started by one run may not
be fully cleaned up before the next run's session startup. The next run then fails with:

```
toxiproxy-cli failed: Command 'toxiproxy-cli ... create ... p5000' returned non-zero exit status 1.
Failed to create proxy: Create: HTTP 409: proxy already exists
```

This manifests as a pytest `INTERNALERROR` (due to the exception during `pytest_sessionstart`)
and the loop counts it as a test failure — a **false positive**.

**Fix:** Call `pkill -9 toxiproxy-server || true && sleep 1` before each attempt in the loop.

### ldap_server.py format string typo (2026-05-20)

Line 178 of `test/pylib/ldap_server.py` had `"s%"` instead of `"%s"`, turning any
toxiproxy startup error into a double-exception (`ValueError: incomplete format`) that:
1. Made the diagnostic message unreadable
2. Turned the INTERNALERROR more severe (hard to distinguish from a real pytest bug)

**Fix applied on ARM instance:** `s%` → `%s`. This should also be submitted as a standalone PR.

---

## 9. Why CI Uses Fedora (not Ubuntu)

ScyllaDB CI nodes run **Fedora exclusively**, including on ARM. The Ansible playbooks in
`scylla-pkg` (repo: `scylladb/scylla-pkg`) only contain `ansible/roles/jenkins-node/tasks/fedora-setup.yml`.
This means all test infrastructure (slapd config paths, dynamic module loading, lib versions)
assumes Fedora conventions. All Ubuntu-specific issues encountered during setup are
Fedora/Ubuntu divergence problems.

