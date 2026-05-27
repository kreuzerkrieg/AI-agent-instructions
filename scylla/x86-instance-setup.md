# x86 Test Instance — Setup Reference

**Last updated:** 2026-05-27

---

## 1. Instance Details

| Field | Value |
|-------|-------|
| **Instance ID** | `i-0da6fa0524a674d54` |
| **Region** | `us-east-1` (N. Virginia) |
| **Instance type** | `i4i.4xlarge` (16 vCPUs, 128 GB RAM, NVMe local storage) |
| **OS** | Ubuntu (x86_64) |
| **User** | `ubuntu` |
| **Current public IP** | ⚠️ *changes on stop/start — always re-check after starting* |

---

## 2. SSH Access

### Connect
```bash
ssh -i ~/Downloads/ernest.pem ubuntu@<IP>
```

### After starting the instance (IP will change!), get the new IP:
```bash
aws --profile 797456418907-DevOpsAccessRole ec2 describe-instances \
  --instance-ids i-0da6fa0524a674d54 --region us-east-1 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text
```

---

## 3. AWS CLI — Managing the Instance

### Start the instance
```bash
aws --profile 797456418907-DevOpsAccessRole ec2 start-instances \
  --instance-ids i-0da6fa0524a674d54 --region us-east-1
```

### Stop the instance
```bash
aws --profile 797456418907-DevOpsAccessRole ec2 stop-instances \
  --instance-ids i-0da6fa0524a674d54 --region us-east-1
```

### Wait until running + get new public IP
```bash
aws --profile 797456418907-DevOpsAccessRole ec2 wait instance-running \
  --instance-ids i-0da6fa0524a674d54 --region us-east-1 && \
aws --profile 797456418907-DevOpsAccessRole ec2 describe-instances \
  --instance-ids i-0da6fa0524a674d54 --region us-east-1 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
```

---

## 4. Running Fedora-Built Binaries on Ubuntu

### The Problem
Binaries built locally on Fedora with the native toolchain link against Fedora-specific
shared library versions that don't exist on Ubuntu. The binary will fail with "not found"
errors from `ldd`.

### Typical Missing Libraries
```
libicui18n.so.76
libicuuc.so.76
libicudata.so.76
libjsoncpp.so.26
```

### Solution: Copy from Local Fedora Machine
```bash
# 1. Find the libraries locally
find /usr/lib64 -name 'libicui18n.so.76*' -o -name 'libicuuc.so.76*' \
  -o -name 'libicudata.so.76*' -o -name 'libjsoncpp.so.26*' 2>/dev/null

# 2. Copy to instance (use /tmp — simple and doesn't require root)
scp -i ~/Downloads/ernest.pem \
  /usr/lib64/libicui18n.so.76 \
  /usr/lib64/libicuuc.so.76 \
  /usr/lib64/libicudata.so.76 \
  /usr/lib64/libjsoncpp.so.26 \
  ubuntu@<IP>:/tmp/

# 3. Verify on the instance
ssh -i ~/Downloads/ernest.pem ubuntu@<IP> \
  'LD_LIBRARY_PATH=/tmp ldd /tmp/<binary> | grep "not found"'
# Should show no "not found" entries
```

### Running with LD_LIBRARY_PATH
Always set `LD_LIBRARY_PATH=/tmp` (or wherever you placed the libs) when running:
```bash
LD_LIBRARY_PATH=/tmp ./<binary> [args...]
```

### Check What's Missing (diagnostic)
```bash
ssh -i ~/Downloads/ernest.pem ubuntu@<IP> 'ldd /tmp/<binary> 2>&1 | grep "not found"'
```

---

## 5. Passing AWS Credentials to the Instance

### The Problem
The test binary needs AWS credentials (access key, secret, session token) as environment
variables. The instance may have its own IAM role, but we often need to use specific
credentials from the local machine's SSO session.

### Credential Environment Variables Expected
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN`
- `AWS_DEFAULT_REGION`

### Approach: Generate a Run Script with Properly Quoted Credentials
Shell quoting of `AWS_SESSION_TOKEN` is tricky — it contains `+`, `/`, and `=` characters.
**Never pass credentials directly in SSH command strings** — use a script file instead.

```python
# Local — generate the script
import configparser, shlex

c = configparser.ConfigParser()
c.read('/home/ernest.zaslavsky/.aws/credentials')
p = '797456418907-DevOpsAccessRole'
key = c.get(p, 'aws_access_key_id')
secret = c.get(p, 'aws_secret_access_key')
token = c.get(p, 'aws_session_token')

script = f'''#!/bin/bash
export AWS_ACCESS_KEY_ID={shlex.quote(key)}
export AWS_SECRET_ACCESS_KEY={shlex.quote(secret)}
export AWS_SESSION_TOKEN={shlex.quote(token)}
export AWS_DEFAULT_REGION=us-east-1
export LD_LIBRARY_PATH=/tmp
ulimit -n 1000000
cd /tmp
chmod +x ./<binary>
./<binary> [args...]
'''
with open('/tmp/run_test.sh', 'w') as f:
    f.write(script)
```

Then upload and run:
```bash
scp -i ~/Downloads/ernest.pem /tmp/run_test.sh ubuntu@<IP>:/tmp/run_test.sh
ssh -i ~/Downloads/ernest.pem ubuntu@<IP> \
  'chmod +x /tmp/run_test.sh && nohup /tmp/run_test.sh > /tmp/output.txt 2>&1 & echo "PID: $!"'
```

### Why shlex.quote() Is Critical
The session token contains characters that break shell expansion. Previous attempts to
pass bare tokens via SSH env vars or inline `export` commands failed silently — the S3
client would fall back to instance profile credentials instead of reporting an auth error.

### Important: Credentials Expire
STS credentials from `gimme-aws-creds` expire after ~6 hours. If a long-running test
outlasts the credential lifetime, S3 requests will start failing with auth errors.
Plan accordingly — the test binary itself handles this gracefully (reports errors and continues).

---

## 6. OS Limits

### File Descriptor Limit (CRITICAL)
Ubuntu's default `ulimit -n` is 1024 — far too low for high-connection S3 tests.
At 64+ connections/shard × 16 shards, you'll hit EMFILE and the process will crash
(segfault due to a bug in Seastar's TLS layer when socket creation fails).

**Always set before running:**
```bash
ulimit -n 1000000
```

Or include it in the run script (see section 5).

### Kernel File Max
If `ulimit -n 1000000` fails with "Operation not permitted", increase the system limit:
```bash
sudo sysctl -w fs.file-max=2097152
# Then retry ulimit
```

---

## 7. Copying Binaries

### From local to instance
```bash
scp -i ~/Downloads/ernest.pem \
  /home/ernest.zaslavsky/Development/scylladb/build/release/test/perf/<binary> \
  ubuntu@<IP>:/tmp/<binary>
```

### Important Notes
- `/tmp` on the instance is cleared on reboot/stop-start — you must re-upload the binary
  and libraries each time the instance is restarted
- The binary is large (~500MB for release builds) — upload takes ~40s on decent connection
- Always `chmod +x` the binary after uploading

---

## 8. Running Tests in Background (Survives SSH Disconnect)

```bash
ssh -i ~/Downloads/ernest.pem ubuntu@<IP> \
  'nohup /tmp/run_test.sh > /tmp/output.txt 2>&1 & echo "PID: $!"'
```

### Monitoring
```bash
# Check if still running
ssh -i ~/Downloads/ernest.pem ubuntu@<IP> 'ps -p <PID> -o etime= 2>/dev/null || echo "DONE"'

# Check output tail
ssh -i ~/Downloads/ernest.pem ubuntu@<IP> 'tail -30 /tmp/output.txt'

# Check output growth rate
ssh -i ~/Downloads/ernest.pem ubuntu@<IP> \
  'L1=$(wc -l < /tmp/output.txt); sleep 10; L2=$(wc -l < /tmp/output.txt); echo "$((L2-L1)) lines in 10s"'
```

---

## 9. Time Zone

The instance clock is in **UTC**. Local machine is **IDT (UTC+3)**.
When correlating timestamps, add 3 hours to UTC to get local time.

---

## 10. SSH Known Hosts

The instance IP changes on every stop/start. You'll get "host key verification failed"
or "ECDSA host key has changed" warnings. Options:
- Accept the new key when prompted (`yes`)
- Or use `ssh -o StrictHostKeyChecking=no` (less secure but convenient for ephemeral instances)

---

## 11. Lessons Learned

### Massive Backtrace Flood at High Concurrency (2026-05-27)
When running S3 download stress test with `_connections * 10` concurrency (10,240 per shard),
the abort/timeout phase generates millions of backtrace lines as each in-flight request
aborts and logs its stack. This causes:
- The round to take 10-30+ minutes to drain even after the timeout fires
- Output file growing at ~16K lines/min of pure backtrace noise
- The reactor to be saturated processing error handling

**Mitigation ideas for future runs:**
- Use `--default-log-level warn` to suppress INFO-level backtraces
- Reduce the concurrency multiplier (e.g., `_connections * 2` instead of `* 10`)
- Or set a shorter round timeout to reduce the total number of in-flight requests at abort time

### Instance Profile Overrides Environment Credentials
See section 5 — the run script approach with `shlex.quote()` was the fix.

### /tmp Is Ephemeral
Everything in `/tmp` is lost on instance stop/start. Always re-upload binary + libraries.

