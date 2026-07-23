# Spot Fleet Setup — Cheap Ephemeral Instances for Running Locally-Built Binaries

**Last updated:** 2026-07-23

Purpose: spin up a **throwaway fleet of storage-optimized spot instances** quickly and
cheaply, deploy a **locally-built executable** (a `scylla` binary or, more often, a perf
test), run it against the instance's **local NVMe**, collect results, and terminate.

This is the "many cheap boxes on demand" counterpart to the single long-lived instances
documented in `arm-instance-setup.md` and `x86-instance-setup.md`. Reuse those files for
the credential/SSH-key machinery; this file only documents what differs for a spot fleet.

---

## 0. TL;DR

```bash
# 1. Refresh creds (ask user for TOTP first — see arm-instance-setup.md §4)
refresh-aws-creds <6-digit-code>

# 2. Find the current Fedora AMI for the target arch (§2)
# 3. Launch N spot instances of the chosen family, tagged for bulk cleanup (§3)
# 4. Wait for running, collect public IPs by tag (§4)
# 5. On each instance: mount NVMe at /mnt/data (§5)
# 6. Deploy the binary + run it (§6, §7)
# 7. Terminate the whole fleet by tag when done (§8)
```

Shared constants (same as the other instance docs):

| Field | Value |
|-------|-------|
| **AWS profile** | `797456418907-DevOpsAccessRole` |
| **Region** | `us-east-1` (N. Virginia) |
| **SSH key** | `~/.ssh/ernest.pem` (key-pair name in AWS: verify with `describe-key-pairs`) |
| **Cred refresh** | `refresh-aws-creds <TOTP>` (STS, ~6h lifetime) |

Export once per shell to avoid repeating `--profile`/`--region`:

```bash
export AWS_PROFILE=797456418907-DevOpsAccessRole
export AWS_DEFAULT_REGION=us-east-1
```

---

## 1. Why Fedora AMI (not Ubuntu)

The binary is built on the local **Fedora** machine with the native toolchain, so it links
against Fedora library versions (`libicu*.so.76`, `libjsoncpp.so.26`, …). On Ubuntu those
don't exist and you have to `scp` libs and juggle `LD_LIBRARY_PATH` (see
`x86-instance-setup.md §4`). Booting a **Fedora Cloud AMI** whose release matches the
build toolchain (Fedora 43) eliminates that entirely — the binary just runs.

**Default login user on Fedora Cloud AMIs is `fedora`, not `ubuntu`.**

---

## 2. Choosing the AMI (per architecture)

⚠️ **Architecture must match the binary.** A binary built on the x86_64 Fedora box runs
only on the Intel families (`i4i`, `i7i`). To run on ARM (`Im4gn`) you need an **aarch64
build** of the binary — build it on an aarch64 host (see `arm-instance-setup.md §6` for the
`dbuild` cross-build) or it will not execute.

Fedora publishes Cloud AMIs under AWS account `125523088429`. Don't hardcode an AMI ID —
Fedora ships new images regularly. Look up the current one:

```bash
# arch: x86_64 (for i4i / i7i)  OR  arm64 (for Im4gn)
ARCH=x86_64
aws ec2 describe-images \
  --owners 125523088429 \
  --filters "Name=name,Values=Fedora-Cloud-Base-*" "Name=architecture,Values=$ARCH" \
  --query 'reverse(sort_by(Images,&CreationDate))[:5].[ImageId,Name,CreationDate]' \
  --output text
```

Pick the newest whose name matches the Fedora release you built against (e.g. `43`).

---

## 3. Storage-Optimized Families

All have local **NVMe instance store** (ephemeral — wiped on stop/terminate). Sizes below
are per-node; larger sizes expose **multiple** NVMe drives (see §5 for handling >1 drive).

| Family | Arch | Build needed | Notes |
|--------|------|--------------|-------|
| `i4i`  | x86_64 (Intel Ice Lake) | x86_64 | Baseline storage-optimized; well-trodden in the existing x86 doc. |
| `i7i`  | x86_64 (Intel newer gen) | x86_64 | Newer/faster NVMe; slightly pricier on-demand, but spot often cheap. |
| `Im4gn`| aarch64 (Graviton2) | **aarch64** | ARM counterpart to `i4i`; best price/perf, but needs an ARM build. |

`Is4gen` (Graviton2, denser storage / fewer vCPUs) is an option if you want max disk per
dollar rather than compute.

Pick a size to taste, e.g. `i4i.4xlarge` (16 vCPU / 128 GB / 1×~3.75 TB NVMe) matching the
existing x86 box.

---

## 4. Launching a Spot Fleet

### Prerequisites (one-time, verify they exist)

```bash
# Key pair (should already exist as the counterpart to ernest.pem)
aws ec2 describe-key-pairs --query 'KeyPairs[].KeyName' --output text

# A security group allowing inbound SSH (22) from your IP. Find or create one:
aws ec2 describe-security-groups \
  --query 'SecurityGroups[?contains(GroupName,`ssh`)].[GroupId,GroupName]' --output text
```

If none suitable exists, create one (uses the default VPC):

```bash
MYIP=$(curl -s https://checkip.amazonaws.com)
SG=$(aws ec2 create-security-group --group-name spot-fleet-ssh \
      --description "SSH for ephemeral spot fleet" --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id "$SG" \
  --protocol tcp --port 22 --cidr "${MYIP}/32"
echo "SG=$SG"
```

### Launch N spot instances (simple `run-instances` loop)

`MarketType=spot` with no `MaxPrice` caps at the on-demand price and takes the cheapest
available spot capacity. `SpotInstanceType=one-time` (the default) means a terminated
instance is not automatically replaced — correct for throwaway work.

```bash
AMI=ami-xxxxxxxxxxxxxxxxx        # from §2, matching arch
TYPE=i4i.4xlarge
COUNT=3
KEY=ernest                       # key-pair name (verify — §4 prereqs)
SG=sg-xxxxxxxxxxxxxxxxx
FLEET=perf-fleet                 # tag used for discovery + bulk teardown

aws ec2 run-instances \
  --image-id "$AMI" \
  --instance-type "$TYPE" \
  --count "$COUNT" \
  --key-name "$KEY" \
  --security-group-ids "$SG" \
  --instance-market-options 'MarketType=spot' \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$FLEET},{Key=owner,Value=ernest}]" \
  --query 'Instances[].InstanceId' --output text
```

**Cheaper-capacity note:** for mixing families/AZs and letting AWS pick the cheapest
capacity automatically, an EC2 **launch template + `create-fleet`** is the cleaner tool.
The `run-instances` loop above is simpler and enough for a handful of identical nodes;
reach for `create-fleet` only when spot capacity for one type/AZ is scarce.

---

## 5. Preparing the NVMe (per instance)

The local NVMe is **not** mounted automatically. The root EBS volume is `/dev/nvme0n1`;
instance-store drives start at `/dev/nvme1n1`. Format and mount at `/mnt/data`:

```bash
# Single NVMe drive (simple case)
echo -e "g\nn\n\n\n\nw" | sudo fdisk /dev/nvme1n1   # GPT + one partition (optional)
sudo mkfs.ext4 /dev/nvme1n1
sudo mkdir -p /mnt/data
sudo mount /dev/nvme1n1 /mnt/data
sudo chown "$USER":"$USER" /mnt/data/
```

> Note: the `fdisk` step writes a partition table but the `mkfs.ext4 /dev/nvme1n1` then
> formats the **whole device**, ignoring it. You can drop the `fdisk` line entirely and
> just `mkfs.ext4` the raw device — that's what actually gets mounted here.

**Multiple NVMe drives** (larger sizes): either pick one, or RAID-0 them for full
bandwidth. Detect the instance-store drives (everything except the root disk):

```bash
# List NVMe block devices; root is the one carrying the mounted / filesystem
lsblk -dno NAME,SIZE,MOUNTPOINT | grep '^nvme'
```

RAID-0 all instance-store drives:

```bash
DRIVES=$(lsblk -dno NAME | grep '^nvme' | grep -v nvme0n1 | sed 's|^|/dev/|')
N=$(echo "$DRIVES" | wc -l)
sudo mdadm --create /dev/md0 --level=0 --raid-devices="$N" $DRIVES
sudo mkfs.ext4 /dev/md0
sudo mkdir -p /mnt/data && sudo mount /dev/md0 /mnt/data
sudo chown "$USER":"$USER" /mnt/data/
```

(`mdadm` is preinstalled on Fedora Cloud; if not, `sudo dnf install -y mdadm`.)

> For a *real* ScyllaDB data path you'd normally run `scylla_setup`/`io_setup` (XFS, tuned
> I/O properties) rather than a hand-mounted ext4. This ext4-at-`/mnt/data` recipe is for
> ad-hoc perf/test binaries that just need a fast scratch filesystem.

---

## 6. Deploying the Binary

Fedora AMI ⇒ **no `LD_LIBRARY_PATH` gymnastics** (arch must still match — §2).

### Few instances — direct `scp`

```bash
BIN=~/Development/scylladb/build/release/test/perf/<binary>   # or build/release/scylla
scp -i ~/.ssh/ernest.pem "$BIN" fedora@<IP>:/mnt/data/<binary>
ssh -i ~/.ssh/ernest.pem fedora@<IP> 'chmod +x /mnt/data/<binary>'
```

### Many instances — stage in S3 once, pull with a presigned URL

Uploading a ~500 MB binary N times over your uplink is the bottleneck. Upload once, then
each instance pulls from S3 in-region (fast, and a **presigned URL needs no credentials on
the instance**):

```bash
# Local: upload once + mint a 1h presigned URL
aws s3 cp "$BIN" s3://<your-bucket>/spot-fleet/<binary>
URL=$(aws s3 presign s3://<your-bucket>/spot-fleet/<binary> --expires-in 3600)

# Per instance: pull it
ssh -i ~/.ssh/ernest.pem fedora@<IP> \
  "curl -fsSL '$URL' -o /mnt/data/<binary> && chmod +x /mnt/data/<binary>"
```

---

## 7. Running the Binary

Set the FD limit high before any high-connection workload (Fedora default is also low
enough to bite S3-heavy tests — see `x86-instance-setup.md §6`). Run under `nohup` so it
survives SSH disconnects.

```bash
ssh -i ~/.ssh/ernest.pem fedora@<IP> \
  'ulimit -n 1000000; cd /mnt/data; nohup ./<binary> [args...] > /mnt/data/out.txt 2>&1 & echo "PID: $!"'
```

If the binary needs **AWS credentials** (e.g. S3 access from within the test), do **not**
inline them in the SSH string — the session token contains `+`/`/`/`=`. Generate a run
script with `shlex.quote()`d values and `scp` it over; see `x86-instance-setup.md §5` for
the exact pattern.

### Monitoring

```bash
ssh -i ~/.ssh/ernest.pem fedora@<IP> 'tail -30 /mnt/data/out.txt'
ssh -i ~/.ssh/ernest.pem fedora@<IP> 'ps -p <PID> -o etime= 2>/dev/null || echo DONE'
```

---

## 8. Teardown (spot ⇒ terminate, not stop)

Spot instances can't be stopped and restarted the usual way — **terminate** them when done.
Their NVMe (and anything in `/mnt/data`) is wiped, so pull results off first.

Bulk-terminate the whole fleet by tag:

```bash
IDS=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=$FLEET" "Name=instance-state-name,Values=pending,running" \
  --query 'Reservations[].Instances[].InstanceId' --output text)
echo "Terminating: $IDS"
aws ec2 terminate-instances --instance-ids $IDS
```

**Cost hygiene:** always tag on launch and terminate on finish. A forgotten storage-optimized
fleet is expensive. Consider a local watcher that terminates once the run finishes (adapt the
auto-shutdown watcher in `arm-instance-setup.md §7`, swapping `stop-instances` →
`terminate-instances`).

---

## 9. Notes carried over from the sibling docs

- **Public IP changes** on every launch; SSH host-key warnings are expected — accept the new
  key or use `-o StrictHostKeyChecking=no` for these ephemeral boxes.
- **Instance clock is UTC**; local is IDT (UTC+3).
- **STS creds expire ~6h** — a long run can outlast them; refresh before launching a fleet.

---

## 10. Lessons Learned

_(none yet — append dated entries as the workflow is exercised)_
