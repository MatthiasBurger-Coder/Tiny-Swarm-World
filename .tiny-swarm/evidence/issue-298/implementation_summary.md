# RC1-R02 Implementation Summary

Status: DONE. Native candidate c921e695 is qualified through actual SSH, isolated
fresh installation, complete canonical lifecycle and real VM reboot. The user
supplied the correct native account; known-host checking and SSH policy remained
intact. Private credentials and connection configuration are not published.

The existing native project was retained with its UUIDs/storage. The first new
project setup failed because stopped old nodes reserved their names on the shared
Incus bridge. Their names were temporarily changed, the never-started new node
removed, and zero instances were verified before repeating fresh setup. This
operator prerequisite correction is retained in both handover records and the
failed lifecycle summary; it is not counted as a successful fresh run.

The corrected fresh run creates the expected three nodes and executes all 14
canonical operations. Reconcile and image update preserve the existing state;
Jenkins A→B→A uses the same binary/data format and actual distinct image content.
All four authenticated phases pass. A later whole-VM reboot changes the native
boot ID, restores readiness within the declared bound and passes authenticated
use without manual runtime repair. An optional extra pre-reboot operator probe
failed before observation because PYTHONPATH was omitted; the retained successful
post-recovery snapshot is the baseline and the post-reboot verifier supplies it.

Native controlled failed-rollout and worker recovery reuse the bedb product tree,
whose only c921 differences are documentation/evidence. Actual SHAs are retained,
not rewritten. Whole-host native evidence cannot be substituted by WSL containers.
