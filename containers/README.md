# containers — the engine image

Dockerfile.engine builds the pinned fork, BookSim 2 and Ramulator 2 at pinned SHAs, and the
native engine, unattended, from a script. Build and run on the Linux box only; never on a
laptop. The image digest is recorded in every EngineResult produced inside it.
