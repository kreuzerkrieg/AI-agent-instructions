# ARM Test Instance — Full Setup Reference

**Last updated:** 2026-05-20  
**Status of test run:** 1000-repeat run launched 2026-05-20, 57% complete as of writing

---

## 1. Instance Details

| Field | Value |
|-------|-------|
| **Instance ID** | `i-05ccc6ae22cf5bc94` |
| **Region** | `us-east-1` (N. Virginia) |
| **Instance type** | `c6g.8xlarge` (32 vCPUs, 64 GB RAM, AWS Graviton2, aarch64) |
| **OS** | Ubuntu 24.04 LTS (aarch64) |
| **Current public IP** | `3.91.29.41` ⚠️ *changes on stop/start — always re-check after starting* |
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
# Expected: {"Account": "797456418907", "Arn": "...assumed-role/DevOpsAccessRole/ernest.zaslavsky@scylladb.com", ...}
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

Credentials are **temporary STS tokens** that expire every ~6 hours. The tool used is
**`gimme-aws-creds`** (Okta → SAML → STS), installed in the scylladb venv.

**Check current expiry:**
```bash
grep x_security_token_expires ~/.aws/credentials
# look at the entry below [797456418907-DevOpsAccessRole]
```

### Refresh credentials (standard workflow)
```bash
~/Development/scylladb/venv/bin/gimme-aws-creds
```

Interactive prompts — what to expect:
1. **Password** — pulled from keyring automatically after the first run (no typing needed)
2. **MFA** — Okta push not available; select `[0] token:software:totp( GOOGLE )` and enter the 6-digit code from Google Authenticator
3. **Role selection** — select `[0] arn:aws:iam::797456418907:role/DevOpsAccessRole`

gimme-aws-creds writes the credentials directly to `~/.aws/credentials` under
`797456418907-DevOpsAccessRole`. No manual editing needed.

**Config file:** `~/.okta_aws_login_config`
- Okta org: `https://scylladb.okta.com`
- Username: `ernest.zaslavsky@scylladb.com`
- `remember_device = True`, `aws_default_duration = 21600` (6 hours)

**Verify credentials are valid:**
```bash
aws --profile 797456418907-DevOpsAccessRole sts get-caller-identity
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

### 1000-repeat stability run (launched 2026-05-20)
```bash
source ~/scylla-test-venv/bin/activate
cd ~/Development/scylladb
rm -rf testlog/*
nohup bash -c "LD_LIBRARY_PATH=/usr/local/lib/scylla-toolchain ./test.py \
  --no-gather-metrics --max-failures 1 --mode release --repeat 1000 \
  test/cluster/object_store/test_backup.py::test_restore_tablets[gs-topology1]" \
  > ~/test-run-1000.log 2>&1 &
echo "PID: $!"
```

Monitor:
```bash
tail -f ~/test-run-1000.log
# or from the local machine:
ssh -i ~/.ssh/ernest.pem ubuntu@<IP> 'tail -30 ~/test-run-1000.log'
```

---

## 8. Why CI Uses Fedora (not Ubuntu)

ScyllaDB CI nodes run **Fedora exclusively**, including on ARM. The Ansible playbooks in
`scylla-pkg` (repo: `scylladb/scylla-pkg`) only contain `ansible/roles/jenkins-node/tasks/fedora-setup.yml`.
This means all test infrastructure (slapd config paths, dynamic module loading, lib versions)
assumes Fedora conventions. All Ubuntu-specific issues encountered during setup are
Fedora/Ubuntu divergence problems.

