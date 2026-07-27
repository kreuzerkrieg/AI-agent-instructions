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
against Fedora library versions (`libicu*.so.77`, `libjsoncpp.so.26`, …). On Ubuntu those
don't exist and you have to `scp` libs and juggle `LD_LIBRARY_PATH` (see
`x86-instance-setup.md §4`). Booting a **Fedora Cloud AMI** whose release matches the
build toolchain removes the version *mismatch*, so no `LD_LIBRARY_PATH` juggling is needed.

⚠️ It does **not** remove the need to install libraries. The Cloud Base image is minimal: it
carries base ICU but not the rest of what a Scylla binary links. Expect ~14 missing sonames
and install them in one shot (§6.1).

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

Pick the newest whose name matches the Fedora release you built against — check with
`cat /etc/fedora-release` on the build box, do not assume. Getting this wrong puts you back
into library-version juggling.

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

### Capacity fallback — expect the cheapest AZ to be full

`InsufficientInstanceCapacity` on spot is routine, and it hits the cheapest AZ first because
everyone else wants it too. On 2026-07-26 three attempts failed before one succeeded:
i7i.8xlarge/1f ($1.08), i4i.8xlarge/1d ($1.29), i4i.8xlarge/1c ($1.34) — landed on
i4i.8xlarge/1f at $1.51.

Note a cheaper *family* in another AZ often beats the pricier family, so rank candidates
across family x AZ together, not family-first. Get current prices with:

```bash
for T in i4i.8xlarge i7i.8xlarge; do
  aws ec2 describe-spot-price-history --instance-types $T \
    --product-descriptions "Linux/UNIX" --max-items 6 \
    --query 'SpotPriceHistory[].[AvailabilityZone,SpotPrice]' --output text | sort -u
done
```

Then walk the list cheapest-first and stop at the first success:

```bash
# "type:az:subnet:price", cheapest first
CANDS="i4i.8xlarge:us-east-1c:subnet-090ce5c775e0dbc19:1.341
i4i.8xlarge:us-east-1f:subnet-037920b544cddbc1b:1.510
i7i.8xlarge:us-east-1b:subnet-06604bf2840958461:1.606"
for c in $CANDS; do
  T=${c%%:*}; rest=${c#*:}; AZ=${rest%%:*}; rest=${rest#*:}; SN=${rest%%:*}
  echo "--> trying $T in $AZ"
  OUT=$(aws ec2 run-instances --image-id "$AMI" --instance-type "$T" --count 1 \
    --key-name ernest --security-group-ids "$SG" --subnet-id "$SN" \
    --instance-market-options 'MarketType=spot' \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$FLEET},{Key=owner,Value=ernest}]" \
    --query 'Instances[].InstanceId' --output text 2>&1) && { echo "LAUNCHED: $OUT"; break; }
done
```

### The SSH security group is not in the default VPC

`SCT-builder-ssh-sg` (`sg-01ab61b39746e1bb6`) lives in `vpc-0935da7392dc9d4d8`, which is
**not** the default VPC. So `--subnet-id` is mandatory — omit it and `run-instances` fails on
an SG/subnet VPC mismatch. That VPC has a public subnet (`MapPublicIpOnLaunch=true`) in every
AZ; as of 2026-07-26:

| AZ | subnet |
|----|--------|
| us-east-1a | `subnet-0a09ba4421ec6aaa8` |
| us-east-1b | `subnet-06604bf2840958461` |
| us-east-1c | `subnet-090ce5c775e0dbc19` |
| us-east-1d | `subnet-02058636b6c0cde8b` |
| us-east-1e | `subnet-08d162f7d1ef05482` |
| us-east-1f | `subnet-037920b544cddbc1b` |

The group already allows tcp/22 from `0.0.0.0/0`, so no per-IP rule is needed — convenient if
WARP changes your egress IP mid-session.

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

(`mdadm` is **not** preinstalled on Fedora Cloud Base — `sudo dnf install -y mdadm` first.)

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

### Install the runtime libraries first

The Cloud Base image lacks most of what a Scylla binary links. Check, then install in one go:

```bash
ldd /mnt/data/<binary> | grep "not found"

sudo dnf install -y libdeflate snappy cryptopp yaml-cpp boost-regex boost-program-options \
  boost-container boost-test libatomic lksctp-tools protobuf hwloc-libs liburing jsoncpp

ldd /mnt/data/<binary> | grep "not found"   # expect empty
```

That list resolved all 14 missing sonames for `perf_s3_downloader` on Fedora 44
(2026-07-26). Because the AMI release matches the build host, the repo versions match what
the binary was linked against, so no `LD_LIBRARY_PATH` is required.

---

## 7. Running the Binary

Set the FD limit high before any high-connection workload (Fedora default is also low
enough to bite S3-heavy tests — see `x86-instance-setup.md §6`). Run under `nohup` so it
survives SSH disconnects.

```bash
ssh -i ~/.ssh/ernest.pem fedora@<IP> \
  'ulimit -n 524288; cd /mnt/data; nohup ./<binary> [args...] > /mnt/data/out.txt 2>&1 & echo "PID: $!"'
```

⚠️ Use **524288**, not the 1000000 quoted in `x86-instance-setup.md §6`. On Fedora Cloud the
hard limit is 524288 (systemd `DefaultLimitNOFILE`), so asking for more fails outright with
`ulimit: open files: cannot modify limit: Operation not permitted` — and if you don't notice,
the limit silently stays at the 1024 soft default and a high-connection run dies on EMFILE.
524288 is ample: 32 shards x 128 connections is 4096 sockets.

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

### Multi-phase fleet work, and how 19 TB was destroyed (2026-07-27)

**Automatic teardown must trigger on "all work finished", never on "nothing running".** A reaper
that terminated a fleet after three consecutive idle checks destroyed 19.4 TB of accumulated
corpus, because the gap between a finished download phase and a not-yet-started upload phase is
indistinguishable from an abandoned fleet. The reaper log shows it counting `idle round 1/3`,
`2/3`, `3/3` while the corpus sat on ephemeral NVMe. Automatic teardown on completion is fine --
the bug is defining completion as one phase when the job has two.

**Chain the phases in one remote session, so completion means completion:**

```bash
ssh -n host "cd /work && screen -dmS run bash -c './run.sh --mode download ... > dl.txt 2>&1 && \
                                                  ./run.sh --mode upload   ... > ul.txt 2>&1'"
```

With this, "no process running" genuinely means every phase is done, and an idle check becomes a
correct completion test rather than a premature one.

**If a phase is not in the automation, it will not happen.** The driver's `run()` only ever issued
the download command; the upload existed solely as a manual invocation that was meant to be fired
afterwards, and never was. Grepping the driver for the second phase returned nothing. Anything
described as "and then we do X" must be *in* the script, not in the plan.

**Never pause to analyse while a fleet holds unsaved data.** The window between the download
finishing and the reaper firing was 4.5 minutes, and it was spent on instance-sizing analysis and
an unrelated bug fix. Get the data off the boxes, or start the next phase, before doing anything
else.

**Put `screen` in the dependency list.** It is required to start the workload at all, is not in
the Fedora Cloud Base image, and was being installed by hand during manual runs -- so the first
automated chained launch failed on every box with `screen: command not found`.

**Match the filesystem and RAID geometry to production, and know whether it is in the measurement
path.** For a Scylla-shaped workload the authoritative recipe is
`dist/common/scripts/scylla_raid_setup`: RAID-0 with **`-c1024`** chunks and
**`mkfs.xfs -K -m rmapbt=0 -m reflink=0`**, not ext4 on mdadm's default 512 KB chunk. This is not
cosmetic when the workload writes what it downloads: in the S3 client the disk write is the
consumer that decides whether a large object is fetched as one ranged GET or as many 5 MiB
chunks, a 19x difference in request rate. Filesystem performance therefore moves the number being
measured.

**Size instances from measurement, not from the spec sheet.** The i4i/i7i families scale
perfectly linearly in vCPU, NIC and price, so there is no sweet spot to find on paper. Measure
achieved throughput first, then pick the size where something is actually near saturation --
a bigger NIC just lowers utilisation. Beware that different phases can favour different shapes:
a download that writes to disk is drive-bound, while upload concurrency scales with shard count.

**Spot for storage-optimized families is frequently unavailable outright.** `i4i`/`i7i` 8xlarge
returned `InsufficientInstanceCapacity` for spot in every AZ tried, with placement scores of 1
region-wide. Try spot then on-demand *per candidate* and record which was used; do not abandon
spot pre-emptively, and do not expect a pricier AZ to help -- price does not predict capacity.

### Driving a real multi-instance fleet (2026-07-27)

Six attempts to run a 6-instance fleet, five of which failed. **Every failure was
orchestration plumbing, not the workload.** The lessons are mostly about resisting the urge
to build a driver.

**Use `screen`, not `nohup`, to start remote work.** This is the single most valuable item.

```bash
ssh -n host "cd /work && screen -dmS run bash -c './run.sh ARGS > /work/out.txt 2>&1'"
```

`ssh host "nohup cmd &"` does **not** reliably return: ssh keeps the channel open while the
backgrounded process holds the session's stdin, so the call blocks until the *whole job*
finishes. On a 10-minute job across 6 boxes that serialises the fleet — measured start times
were **10 min 24 s apart**, with box 1 finishing 23 s before box 2 began, so there was never
any concurrent load. Adding `ssh -n` and `< /dev/null` on the remote side did **not** fix it.
`screen -dmS` detaches properly: ssh returned in 2 s and all six binaries started **within the
same second**.

Two traps with it: keep the `> out.txt 2>&1` redirect (screen's buffer dies with the session,
taking your logs), and `dnf install -y screen` first — it is not in the Cloud Base image.

**Don't build an orchestration driver.** A `launch → setup → run → collect → teardown` script
accumulated five distinct bugs: heredoc quoting mangling `"$@"`, `pgrep` self-matching, wrong
disk detection, ssh not returning, and `wait` blocking on the watchdog. Discrete verifiable
steps run straight from your shell — scp, screen, read the file — get there far faster.

**`pgrep` for "is it still running" is a minefield.**
- `pgrep -f NAME` **self-matches**: the polling shell's own command line contains the pattern,
  so the answer is always yes. A wait loop built on it never exits.
- `pgrep -x NAME` is worse for names over 15 characters: the kernel truncates `comm` to 15, so
  it silently matches nothing and pgrep warns about it. That fails in the opposite direction —
  every wait exits immediately.
- Working form: `pgrep -f '[p]erf_s3_downloader'`. The character class stops the pattern from
  matching its own literal text.

**Identify instance-store disks by model, not by excluding the root disk.** Fedora roots on
btrfs, so `findmnt -no SOURCE /` returns `/dev/nvme0n1p3[/root]`. That subvolume suffix is not a
device path, `lsblk -no PKNAME` on it yields nothing, and a `grep -v "$(...)"` built from it then
filters out *every* disk. Under `set -e` the failing grep aborts the script before `mkdir`, so
setup dies silently. Use:

```bash
mapfile -t DRIVES < <(lsblk -dno NAME,MODEL | grep 'Instance Storage' | awk '{print "/dev/"$1}')
```

**Make setup prove success, and abort the run if it did not.** Echoing "ready" after the ssh call
regardless of its exit status meant six broken instances reported ready and the failure only
surfaced later, mid-run. Have the remote script print a sentinel (`SETUP_OK`) only after the
binary resolves its libraries *and* runs `--help`, gate on that, and refuse to start the round if
any box failed.

**Verify the binary on the instance, every time.** Twice a stale binary was deployed — once
four hours old — and the run silently exercised old behaviour. `md5sum` both sides, and grep the
binary (or run `--help`) for a string only the new build has. Note `strings` misses short
literals; `grep -a` or `--help` is more reliable.

**A driver dies with your session; use two layers of teardown.** An orphaned 6-instance fleet
billed for 32 minutes because the controlling session ended and took the driver's EXIT trap with
it. Run the driver under `setsid`, *and* arm an independent detached watchdog at launch:

```bash
setsid nohup bash -c "sleep 5400
  ids=\$(aws ec2 describe-instances --filters 'Name=tag:Name,Values=$FLEET' \
    'Name=instance-state-name,Values=pending,running,stopping,stopped' \
    --query 'Reservations[].Instances[].InstanceId' --output text)
  [ -n \"\$ids\" ] && aws ec2 terminate-instances --instance-ids \$ids" >/dev/null 2>&1 < /dev/null &
disown
```

`disown` matters: a bare `wait` elsewhere in the script will otherwise block on the watchdog's
`sleep`, which is exactly what stopped one run from ever starting.

**`kill -9` the driver when you want to keep the instances**; a normal kill runs its EXIT trap and
tears the fleet down. Conversely `pkill -f s3-fleet.sh` will match — and kill — your own shell.

**Try spot first, fall back to on-demand per candidate.** Spot is 2-3x cheaper and usually
available *somewhere*, but `InsufficientInstanceCapacity` in the cheapest AZ is routine and
storage-optimized families can score 1 (worst) on
`aws ec2 get-spot-placement-scores` across every AZ. Do not conclude "use on-demand" from that
alone, and do not chase a pricier AZ either — price does not predict interruption. Walk
family x AZ cheapest-first, attempting spot then on-demand for each, and tag the market on the
instance so the run record shows what it actually got. Losing 2 of 6 to reclaim mid-run (observed
here, 9 minutes in) invalidates the measurement, so tag and check the survivor count before
recording a result.

**Pick one instance type for the whole experiment.** Switching families between phases makes
results unrelatable. Check what *every* phase needs first: a download-only run has no use for
local NVMe, but if a later phase reads that data back, an EBS-only box would measure a 125 MB/s
gp3 volume instead of the thing under test.

### First exercise of this runbook (2026-07-26)

Launched one i4i.8xlarge spot in us-east-1f to run `perf_s3_downloader` against a real S3
backup. Everything above that is marked ⚠️ came from this run. Beyond those:

- **Two instance-store NVMe on i4i.8xlarge** (`nvme1n1`, `nvme2n1`, 3.4 TB each). The RAID-0
  recipe in §5 works as written and yields 6.8 TB at `/mnt/data`. Root is `nvme0n1` (5 GB EBS).
- **`timeout` alone will not kill a wedged Seastar app.** It sends SIGTERM, which a stuck
  reactor ignores, and then `timeout` waits forever. Always `timeout -s KILL <n>` when driving
  these binaries from a script, or you lose the output along with the process.
- **Redirect to a file, don't pipe to `tail`.** If the run is killed, a pipeline's buffer is
  lost and you get nothing. `> out.txt 2>&1` then read the file.
- **`--default-log-level warn` also silences your own test's INFO output.** Pair it with
  `--logger-log-level <logger>=info` — e.g. `--default-log-level warn --logger-log-level
  perf=info` — to keep the test's numbers while suppressing the s3 client's per-abort
  backtrace flood (cf. `x86-instance-setup.md §11`).
- **NIC ceiling is worth knowing before blaming the network.** `i4i.8xlarge` is 18.75 Gbps
  with baseline == peak, so there are no burst credits to confuse matters. A run doing
  340 MB/s was at ~15% of the NIC, which ruled the network out immediately:
  `aws ec2 describe-instance-types --instance-types <type> --query
  'InstanceTypes[0].NetworkInfo.[NetworkPerformance,NetworkCards[0].BaselineBandwidthInGbps,NetworkCards[0].PeakBandwidthInGbps]'`
- **The credential run-script pattern from `x86-instance-setup.md §5` works unchanged** here;
  `shlex.quote()` the three AWS values into a script and `scp` it. Worth keeping the
  `mkdir -p /mnt/data/corpus` and `ulimit` inside that script so a run can't forget them.
