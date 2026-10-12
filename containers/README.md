# containers — the engine image

Dockerfile.engine is planned to build native and explicitly admitted dependencies/references
at pinned revisions, unattended. It does not require a complete external simulator. Native
build/run and performance work require the designated Linux host and real runner/manual
nightly readiness. The image digest is recorded in results produced inside it; the present
base image is not evidence that native or any reference is implemented.
