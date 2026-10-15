# Next U4 work: mapped loader and K2 first-use preparation

Javid asked to continue after the installed K1 inventory was published. This handoff
starts the next bounded development work; it does not confer public fixture authority.
Baseline: `d9d51ca67ba8f1862ae71224020504cb7e8f5bcb` (pull subsequent peer commits normally).

K1 is implemented, independently reviewed, installed and locally checked. The final
28-test/replay binding is live. M's protected carriers and the selected-policy artifact
migration are installed. The fixed-delay runtime loader/export and K2 public binary/
Python runner are not delivered: `src/rkuarch/engines/native/__init__.py` is a placeholder.
The component mapper is first needed at checkpoint B, not at K2.

Use a **fresh Lane A author session** in the existing A clone for the new task. Continue
the **existing Lane B author session** in its independent clone. Keep the K1 reviewer
session separate. Send [A's prompt](lane-A.txt) and [B's prompt](lane-B.txt) in parallel;
they can exchange published commit/API references through the coordinator.

## Concrete work now

- A implements the ordinary, additive fixed-delay saved-input loader/export boundary
  using the installed M contract, with tests first. A also prepares the concrete K2
  interface/build-identity and result-accounting proposal against the reviewed kernel.
- B turns the applicable independent kernel/clock catalogue into exact finite mapped
  fixture/profile/registry candidates, checks A's actual dependencies, and prepares the
  first-use acceptance table and public-boundary test obligations.

## First-use boundary

U0011's installed M release requires each qualifying corpus/profile/registry and expected
engine binding to be accepted before public use. U0024 retains that prerequisite even
while remote CI is deferred. The current schema fixtures and old B proposals contain
synthetic anchors or incomplete joins; they cannot be silently promoted to authority.

This task releases loader implementation and K2 preparation, **not public K2 execution
or qualification**. Unit tests may inject explicitly synthetic authority to test the
loader, including positive controls, but may not claim human acceptance or a native pass.
Return a concrete first-use package for coordinator reconciliation; identify any exact
engine-build binding that must be finalized after K2 implementation. Do not invent a
binary hash or create a circular profile/build identity. The next implementation release
must distinguish that construction step from final public qualification.

No new architecture decision, full table, component model, registry publication, server
setup, performance run or U4 closure is requested. Local checks under U0024 remain the
execution environment; remote correctness/nightly/performance obligations stay pending.
Protected paths remain proposal-only. No new dependency, licence or schema permission
is inferred. Existing K1 tool pins remain accepted for their original scope; propose any
required K2 extension concretely rather than requesting the same K1 vote again.

Ordinary owned work uses tests-first, normal commits and normal pushes to main from the
independent clones, integrating peer commits without force push. No whole-tree checkpoint
copies, CI polling or untracked peer inputs. Each handoff separates executed checks from
historical evidence and leaves independent review to a different session.
