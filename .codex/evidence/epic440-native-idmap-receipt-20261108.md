# Current/disk ID-map distinction and durable initial identity

Root approved three locks from d4bdb8fe76504c14687aa00686d79b796fdf62d7:
fixture, its test, this record. Source-only, no hosts/tests/commits by worker.
Actual R7 failed INSTANCE_METADATA_DRIFT after its own start; cleanup refused.
Its initial UUID remained RAM-only and is not retroactively claimed as durable.
Root separately owns exact current-UUID recovery; historical failure remains.

| Requirement | Exact implementation/test |
|---|---|
| Disk map differs from running map | Require present current==next when running/stopped; present disk map may be typed[] OR next, retaining per-key initial receipt/one-way startup continuity and malformed/unknown rejection. |
| Realistic lifecycle DTOs | Default full transport uses running currentnext/disk[]/readyabsent/templateabsent and stopped disk[]/readyfalse/powerSTOPPED/host-veth-absent. Also test shifted disk==next and illegal map/missing/reversal/UUID cases. |
| Durable before Start | Fixed private ext4 listener-initial-RUN.json; exact10 fields schema/scope/run/source/rawGOsha/instanceNameSHA/initialUUIDSHA/bindingSHA/imageFP/orderedProfilesSHA. O_EXCL0600, trusted0700parent, nofollow fd, fsync file+directory. Existing file never adopted. Writer failure prevents Start; existing proven Stopped cleanup remains. |
| Actual approval bytes | _run_fixture requires internal approved_go_sha256 keyword; main passes digest(raw) from the actual expected-hash/validate_go checked bytes. No parsed-GO reencoding/global/GO19 expansion/operator parameter. Direct tests bind explicit synthetic approval bytes. |

PRIMARY: https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/instance/drivers/driver_lxc.go
handleIdmappedStorage1727–1800 retains [] disk mapping for idmapped storage;
startCommon1928–1935 separately updates current mapping, DiskIdmap7867–7883 is not
CurrentIdmap. Stop2899–2903 writes powerSTOPPED and readyfalse. PRIMARY
https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/device/nic_bridged.go
postStop997–1000 clears host_name. No other nullable/default relaxation follows.
Root independently reviewed and released exact sidecar/rawGO contract before edits.

## Frozen source handoff

Only the false mandatory DiskIdmap==CurrentIdmap equality was removed. Disk map
must remain present and one of the already parsed []/next values, bound by its
existing per-key receipt history; Running/Stopped current map remains present
and equal to next. UUID/image/effective-spec/unknown metadata checks are intact.
Pinned stop source confirms readyfalse/powerSTOPPED and deleted host-veth, so
those stopped-phase requirements were preserved, not made optional.

New fixed listener-initial-RUN.json writes exactly the reviewed10 fields after
actual init receipt validation and before any Start. The writer opens the checked
private0700parent with a nofollow directory descriptor, creates nofollow/O_EXCL600
relative to it, validates uid/mode/nlink, writes bounded hash-only data and fsyncs
both file and same directory descriptor. No adoption, overwrite, operator path,
raw metadata/UUID or retroactive R7 receipt exists. Success result includes its
hash; on later failure the exact fixed sidecar remains independently inspectable.
A failed/partial fsync is not reported as durability; Start is never reached.

main passes the hash of the actual already validated raw approval bytes through a
mandatory internal keyword. No canonical parsed-GO hash, ambient state or new GO
key is introduced. Actual noncanonical-but-valid approval byte regression asserts
that precise forwarding. Direct legacy behavior tests use explicit synthetic raw
approval bytes and isolate their filesystem writer; separate actual-writer full
transport tests prove file existence/hash/UUID/profile/source binding BEFORE
Start and safe Stopped cleanup after EEXIST/unsafe parent/file+dir fsync failures.
Existing full-flow/failure/budget tests now use realistic idmapped-storage DTOs,
including absent Running ready, true stopped false/STOPPED/no-veth. Shifted-disk
and malformed/disk-regression/missing/current-map/UUID negatives remain explicit.

Worker AST parse and git diff --check PASS. Test/type/quality/host/effect/commit
NOT_RUN. Root owns exact review, gates and separately authorized live scenario.
No previous failed case, history or resource is relabeled as successful.

## Independent review and Root exact PC integration

Independent architecture/security review verified allthree frozen pins and primary
Incus6.0.5 disk/current idmap semantics; Source GO before PC gates, not live GO.
PC WSL R1 clean a57f02e0 plus exactthree: nearest359 PASS15.546s; type980 PASS;
allseven QUALITY PASS,3677 discovery/36skipped/269.225s. Code/test pins unchanged.
Focused4150cf4816fb4b98ae1cebfe89bcdacdc3025787d4f762b7c2e302c1bd2d9b29;
typee1356c54133a38ec780870eb0886739c3e97a12b5410fa9c19a47f96c6807f99;
quality15ffa63c26ab4493ba7a389302fd72205631fd2ed81c4d10875b1b924670203c.
Private ext4 copies are byte/hash verified. Record-only append follows those
executing source/test bytes. Capability matrix remains EMPTY; no live PASS.

Historical R7 cleanup: independently reviewed helper43438022 bound current UUID,
exact run/profile/root-volume/spec/audit and full original preservation. Separate
Root actual plan382e4821 and GO01ca7f0c admitted ONLY own graceful stop+three
nonforce deletes. All three delete-returned receipts are durable; the aggregate
execution budget refused its final read. No effect was retried. A separate fresh
read-only600s full snapshot using unchanged helper snapshot(3) proved no own
objects remain and complete original preservation; final snapshot
ac81ce85bb99374a0a026fb62898dc0e4f01f79aebb18bb856ebad3741571b7b.
Old execution RECOVERY_BUDGET and R7 fixture failure remain historical; separate
final proof does not convert qualification to PASS or assert missing initial UUID
continuity. All three original LXD instances remain Running, original socket
inactive. No original actions were performed by the cleanup helper.
