# RC1 planned WSL distribution restart

This is the observed recovery procedure for the owned isolated RC1 test target,
not a claim about arbitrary power loss or rebooting the shared WSL kernel.
The complete result is retained with issue-299. Existing explicit live approval
and ownership of all affected nodes are prerequisites.

1. Verify the healthy platform and authenticated applications. Preserve provider
   UUIDs, Swarm/service identity, effective configuration and persistent fixture
   comparisons. Stop the owned CI runner so no job starts during the boundary.
2. For a planned shutdown, stop Docker, its socket and containerd on the manager,
   then each owned worker. Verify all three units are inactive on every node:

   ```sh
   incus exec swarm-manager -- systemctl stop docker.service docker.socket containerd.service
   incus exec swarm-worker-1 -- systemctl stop docker.service docker.socket containerd.service
   incus exec swarm-worker-2 -- systemctl stop docker.service docker.socket containerd.service
   ```

3. Stop the Incus startup service to shut down owned nodes gracefully, and stop
   its socket. Restart only the selected distribution with the host's existing
   distribution controls. Preserve unrelated distributions and sessions. In the
   observed isolated test, a prequalified interoperability guard also prevented
   the second distribution's systemd from unregistering the shared WSL handler.
4. Allow the enabled Incus and node Docker services to start normally. Compare
   the distribution PID1 start time/PID namespace, provider UUIDs and creation
   times. The shared kernel boot ID remains unchanged for this boundary.
5. Within a 600-second startup window, require both canonical platform verify
   and all eight Classic application-readiness tests. A platform-only pass does
   not establish application readiness. Then execute the canonical authenticated
   acceptance suite and persistent-state comparisons; any error, failure or skip
   leaves the scenario unverified.

The first test omitted explicit Docker quiescence. Docker reported Pulsar Manager
running with an empty overlay EndpointID and IPAddress. The first full acceptance
failed; a targeted container restart and Swarm replacement recovered it, followed
by all 25 live tests and seven API checks. Intermediate port-allocation failures
remain diagnostic history. The underlying Docker startup cause is not established.

The second test used the planned procedure above. Application readiness completed
in 133.629 seconds from the verifier start; authenticated acceptance completed in
87.931 seconds. Provider/service/Swarm identity and persistent fixture/configuration
comparisons passed, with zero authentication failures/errors/skips and no repair
after restart. The two attempts are separate evidence; the earlier failure is
not reclassified as a successful automatic boot.

This procedure does not disable safety guards or edit service specifications.
Do not delete networks, reset nodes or recreate persistent volumes to make a
readiness test pass. Diagnose an actual failed boundary and retain its failure
before applying an owned repair.
