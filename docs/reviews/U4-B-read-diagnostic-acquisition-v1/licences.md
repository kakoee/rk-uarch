# Actual diagnostic notices and applicability

Both acquired copyright files match the earlier metadata bytes exactly, now tied to the
authenticated package payloads. Complete notices/changelogs remain preserved in the private
extraction, alongside the actual binaries. Identities below are actual-file SHA256 values,
not inferred from package hashes. This is an inspection record, not new licence authority,
a distribution permission, a simulator dependency change or a source-level compliance audit.

| Material | Actual notice identity and scope |
| --- | --- |
| strace copyright | `40e4ca01654c733c06fabee65168da4c177117b1bd084f3a752bc8a989736e04`: strace LGPL-2.1-or-later; upstream test suite GPL-2.0-or-later. The acquired data listing contains the tracer, log-merge shell script, docs/examples and manpages; no test-suite tree was delivered or executed. |
| strace-log-merge | Script SHA256 `a8c835c03d9760c4ffa777cab90f5336983115a3b0e6d8fd5cbfb7554bb5cd2b`; embedded SPDX identifies LGPL-2.1-or-later. It was read as text, never sourced/executed. It is outside the proposed tracer invocation. |
| libunwind8 copyright | `977d981f5677652884b09cccef6b62f992aa9c74b7a748bfe9863a703f5aed58`: upstream files, including named ptrace/x86_64 files, Expat; debian/* GPL-2.0-or-later. Preserve both branches and notices. The package contains four DSOs, docs and control metadata; its ldconfig trigger was not executed. |
| Existing image libc6 copyright | `40c7e1f2118531f038ca22999bd976901254e1bc5cd1b0f0211bdd064c599987`: most GNU libc LGPL-2.1-or-later, utility GPL and incorporated-code notices also retained. Its introductory historical 2.23 text is not the installed package pin; actual dpkg identity is 2.36-9+deb12u14. |
| Existing image liblzma5 copyright | `a2dc8fac0f496e1c58aff67018cf0c6b88336316afa5642f9335b71642e28aa8`: upstream liblzma sources are described as public domain, with separate source/packaging/utility licences and an explicit caveat that toolchain-added binary code may be copyrighted. No blanket claim that the entire binary is public domain follows. |
| Existing full LGPL-2.1 text | `/usr/share/common-licenses/LGPL-2.1`: `dc626520dcd53a22f727af3ee42c770e56c97a64fe3adb063799d8ab032fe551`. |
| Existing full GPL-2 text | `/usr/share/common-licenses/GPL-2`: `8177f97513213526df2cf6184d8ff986c675afb514d4e68a404010521b880643`. |

The extra coredump library is possessed and inspected because it is in the approved
libunwind8 package; strace does not DT_NEEDED-load it. No optional script/test/example
execution or additional library loading is authorized by its presence. GPL metadata and
LGPL diagnostic code are not relabeled as Expat or folded into accepted Rust dependency
pins. Coordinator/human review must address use of this exact separate diagnostic payload
before execution. No new exception or distribution decision is asserted here.
