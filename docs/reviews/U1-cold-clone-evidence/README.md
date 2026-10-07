# U1 published-revision cold-clone evidence

Archived on 2026-10-07 from `/tmp/u1-cold-clone-rwaqeoco` for publication commit
`44559fb1672e4d3468b4b6fc930cfdf4b4c1e99e`. These are the original validation outputs,
not a new validation run. See [the closeout](../U1-closeout.md) and
[ADR U0020](../../decisions/U0020-u1-cold-clone-validation-exception.md).

- [report.txt](report.txt): complete report, commands, results, host details and authorization.
- [results.jsonl](results.jsonl): command index with timestamps, exits and original log paths.
- [logs/](logs/): all 32 original logs, including hosted CI job metadata and full job output.
- [environment.json](environment.json): recorded isolation variables. No inherited virtual
  environment was present; the runner removes `VIRTUAL_ENV` if present.
- [user-approved-exception.txt](user-approved-exception.txt): exact authorization text.
- [audit.py.txt](audit.py.txt): original runner source preserved as text, not installed tooling.
- [original-SHA256SUMS.txt](original-SHA256SUMS.txt): original evidence manifest; its
  `audit.py` entry maps to `audit.py.txt` here. Every other listed path is unchanged.
- [SHA256SUMS](SHA256SUMS): archive manifest for all original evidence bytes at their archived
  names, including the original manifest. The README and this manifest are new archive metadata.

All copied contents are byte-identical to the originals. Absolute `/tmp` paths in those
contents record the original run location; read matching relative files here to inspect the
retained evidence. The checkout, virtual environment and uv cache are not archived.

Verify the archive from the repository root:

```sh
(cd docs/reviews/U1-cold-clone-evidence && sha256sum -c SHA256SUMS)
```

The report records the sandbox mount failure and initial unqualified `python` probe failure
separately from the successful requested checks. Hosted conditional no-ops are enumerated;
they are not engine, golden, performance or silicon validation.

The archived `logs/ci-log.log` and `logs/lint-imports.log` retain eight original
trailing-space lines from tool output. A staged-diff whitespace check reports them;
they are preserved intentionally so original evidence bytes and checksums remain valid.
Authored Markdown is checked separately.
