# U3 host setup sequence

Javid's reported inventory identifies native Debian12 x86_64, 12 CPUs, about31.3GiB RAM
and896.4GiB free disk. This is the intended Linux host; actual candidate capacity and timing
remain to be measured under pre-registered G2. The system Python3.11 does not satisfy
rk-uarch's >=3.12 requirement. Original SSH inventory did not add user-local bin directories.

## Immediate user-account step

Completed: Javid reported uv0.12.13, already-installed Python3.12.14 and Rust1.99.0.
See [reported result](host-python-result.json). The earlier missing-tool output was a PATH issue.
Javid now reports Reza installed the packages and the rootless check passed.
See [Podman result](host-podman-result.json). The next action is runner registration below.

The completed command was `host-python-setup.sh` through authenticated SSH. It adds ~/.local/bin and ~/.cargo/bin
to this process's PATH, reuses uv if present, installs uv if absent, and installs managed
Python3.12. It leaves system Python, profiles, existing project clones and Reza's account
alone. It then reports container/Rust tools and Javid's subordinate-ID entries. It does not
install Rust, containers or the Actions runner. Installer source:
[uv installation](https://docs.astral.sh/uv/getting-started/installation/),
[installer options](https://docs.astral.sh/uv/reference/installer/),
[Python management](https://docs.astral.sh/uv/guides/install-python/).

## Container runtime

The repository runbook recommends rootless Podman. Treat that as the proposal for U0005,
not an already accepted runtime choice. If selected and absent, an administrator installs
Podman/uidmap and ensures Javid has nonoverlapping subuid/subgid ranges. Confirm rootless
operation as Javid before fork builds. Do not add Docker-group/root privileges. Do not
infer Docker container Actions compatibility from Podman's CLI similarity; current nightly
uses host commands. [Podman documentation](https://docs.podman.io/en/latest/markdown/podman.1.html).

## Runner registration

Repository runner registration is human-owned in the current nightly workflow. The owner
of kakoee/rk-uarch uses Settings → Actions → Runners → New self-hosted runner, Linux x64,
and executes the generated download/checksum/configuration commands on this server, in a
separate runner directory. Retain default linux/x64/self-hosted labels and add uarch. Do not
paste the short-lived registration token into chat or commit it. First confirm no suitable
existing runner; the coordinator's earlier API403 could not establish absence.
[GitHub registration instructions](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners).

The runner process needs ~/.local/bin on PATH (including uv) in its service/launch environment;
a successful interactive shell alone does not prove that. Keep its checkout separate from
Reza's and Javid's development clones. Choose persistent service setup with the administrator
rather than silently changing server services. Once online, re-enable the schedule and
verify a manual nightly run. Native sources remain absent, so that workflow step is a no-op. B has now committed five
mutants in two analytic modes: the nightly test step should execute those ten cases. Verify
actual collection and results; the workflow still tolerates pytest exit 5, so a green status
alone does not establish that tests ran. U-P5 candidate measurements
also wait for approved, human-committed U0005 pre-registration.
