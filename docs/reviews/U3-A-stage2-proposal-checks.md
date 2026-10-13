# Lane A Stage 2 discriminating proposal checks

Author checks, not native tests, a qualifying corpus, human hand fixtures or Stage 3.
Run from Lane A repository root using the existing `.venv/bin/python -I -B` with this block
on stdin. No writes, generated artifacts, candidate or producer calls. Current local
contract/YAML reads only verify unchanged strict carrier facts and all hardware leaves;
module origins are asserted. The mathematical expectations below use independent integer/
rational operations. Set `U3A_DOC_REF=184d2c2b08c28a01673be143b086ef223ba6706a` to inspect
old proposal text directly via Git, without copying a checkpoint or changing any file.
That run is expected to report A-F1–A-F10 proposal assertions failed. It is not a native
regression result. Restoring current document selection must pass.

```python
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from fractions import Fraction as F
from pathlib import Path

root = Path.cwd().resolve()
sys.path[:0] = [str(root / 'contract'), str(root / 'src')]
import uarch_contract
import yaml
from uarch_contract.hardware import HardwareSpec, sourced_leaves
from uarch_contract.prepared import PreparedOp
from uarch_contract.table import Counts, ExtCounts
assert Path(uarch_contract.__file__).resolve().is_relative_to(root)
package = 'docs/reviews/U3-native-stage-design-v2/'
ref = os.environ.get('U3A_DOC_REF')
def doc(name):
    if ref:
        return subprocess.check_output(['git', 'show', ref + ':' + package + name], text=True)
    return (root / package / name).read_text()
i, v, d, u = (doc(n) for n in ('interface.md', 'verification.md', 'delivery.md', 'proposed-U0011.md'))

def ne(f, t, n=0):
    # Search the mathematical definition rather than production next_edge/index formula.
    k = t * f // 10**12
    while k and math.ceil(F((k-1)*10**12, f)) >= t:
        k -= 1
    while math.ceil(F(k*10**12, f)) < t:
        k += 1
    return math.ceil(F((k+n)*10**12, f))

cap = F(10**12) * F(71, 78) / 8
service = F(256 * 10**12, cap)
def timeline(core, noc, dram, write=False, ordinal=1):
    port = ne(core, 0, 1) if write else 0
    req_align, arrival = ne(noc, port), ne(noc, port, 4)
    dram_align, latency = ne(dram, arrival), ne(dram, arrival, 48)
    begin = math.ceil(latency + (ordinal-1)*service)
    end = math.ceil(latency + ordinal*service)
    resp_align, resp = ne(noc, end), ne(noc, end, 4)
    core_align = ne(core, resp)
    complete = core_align if write else ne(core, resp, 1)
    prefix = [0, 0, port] if write else [0]
    return prefix + [req_align, arrival, dram_align, latency, begin, end,
                     resp_align, resp, core_align, complete]

def f1():
    rows = [r for r in i.splitlines() if r.startswith('| K2 |') or r.startswith('| B |')]
    assert len(rows) == 6
    assert any('| B | test | kernel_fixture / fixture_cold' in r for r in rows)
    assert any('| B | production | component / cold' in r and 'ratio1' in r for r in rows)
    for field in ('profile_hash', 'case_id', 'eligibility', 'TestProfileMismatch',
                  'TestVariantNotAdmitted', 'TestOnlyHardware', 'AdmissionMismatch'):
        assert field in i
    # Symbolic admission tuples, not fabricated authentic job/hash values.
    frozen = {('B','test','component','fixture_resident','variant-credit1',1),
              ('B','test','kernel_fixture','fixture_cold','base',1)}
    def admits(t):
        return t in frozen if t[1] == 'test' else t == ('B','production','component','cold','base',1)
    assert admits(('B','test','component','fixture_resident','variant-credit1',1))
    assert not admits(('B','production','component','cold','variant-credit1',1))
    assert not admits(('B','test','component','fixture_resident','unlisted',1))
    marker = {'checkpoint':'B','invocation':'test','profile_hash':'symbolic-P',
              'case_id':'c1','eligibility':'verification_only'}
    digest = lambda x: hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
    assert digest(marker) != digest(dict(marker, invocation='production'))
    assert 'proposed-design stipulation with a rationale' in i


def f2():
    rows = [r for r in v.splitlines() if r.startswith('| read') or r.startswith('| write')]
    cases = [(10**9,10**9,10**9,False,1),(10**9,10**9,10**9,False,2),
             (10**9,10**9,10**9,True,1),(10**9,1200000000,10**9,False,1),
             (10**9,1200000000,10**9,True,1),(800000000,1200000000,900000000,False,1),
             (800000000,1200000000,900000000,True,1)]
    assert len(rows) == len(cases)
    for row, args in zip(rows,cases):
        numbers = [int(x) for x in re.findall(r'\d+', '|'.join(row.split('|')[2:]))]
        assert numbers == timeline(*args), (numbers,timeline(*args))
    assert ne(10**9,54250,4) == 59000 != 54250+4000
    old_resp = math.ceil(54250+F(4*10**12,1200000000))
    assert ne(10**9,old_resp,1) == 59000 != timeline(10**9,1200000000,10**9)[-1]
    assert 'do not align channel completion to a DRAM edge' in v
    assert 'alignment' in v and '→memory' in v and '→noc' in v
    assert 4000 + (54250-4000) + (59000-54250) + 1000 == 60000


def f3():
    finishes = lambda s: [ne(10**9,ne(10**9,math.ceil(52000+j*s),4),1) for j in range(1,6)]
    good,bad = finishes(service), finishes(F(2048))
    assert good == [60000,62000,64000,66000,69000]
    assert bad == [60000,62000,64000,66000,68000]
    assert good[:2] == bad[:2] and good[-1] != bad[-1]
    assert '[60000,62000,64000,66000,69000]' in v
    assert '[60000,62000,64000,66000,68000]' in v
    assert all(((1536+2048*j)//256)%8 == 6 for j in range(33))
    assert 'address1536+2048*j' in v and 'no separate finite issue-rate cap' in v
    assert 'Only compute jobs pay job_overhead_cycles' in v


def f4():
    ready, owner_free = 1000,3000
    granted = max(ready,owner_free)
    assert granted+2000 == 5000 != max(owner_free,ready+2000)
    assert '**after owner grant**' in i and '**5000 ps**' in i
    assert 'h=0' in i and 'nonaliasing' in i and 'phase2' in i


def f5():
    blocks = re.findall(r'```json\n(.*?)\n```',i,re.S)
    op = json.loads(blocks[0]); projection = json.loads(blocks[1])
    prepared = dict(id='g0',depends_on=[],padding=[],replication=[],fusion='none',
                    kv_access=None,weight_copies=1,work_repeat=1,embedding_local_tokens=None,
                    operand_access={'X':'read','W':'read','Y':'write'},spec=op)
    PreparedOp.model_validate(prepared)
    Counts.model_validate(projection['counts'])
    ExtCounts.model_validate(projection['ext_counts'])
    work = projection['work_counts']
    assert work['completed_mac_count']*2 == projection['counts']['matrix_ops']
    assert work['issued_matrix_ops'] == 2097152
    for bad in (dict(projection['ext_counts'], issued_matrix_ops=2097152),
                {k:x for k,x in projection['ext_counts'].items() if k!='noc_flit_hop_count'}):
        try: ExtCounts.model_validate(bad)
        except ValueError: pass
        else: raise AssertionError('old strict ExtCounts was weakened')
    assert (2*3*5+2*5*7,2*3*7,2*256,256) == (100,42,512,256)
    assert 'operator_version=prepared-op/1' in i
    assert 'then validate all content hashes and nested closure' in i
    assert 'CoefficientHashMismatch' in i and 'InvalidOperatorSchema' in i


def expand(s):
    m=re.search(r'\{([^{}]+)\}',s)
    if m:
        return [x for item in m[1].split(',') for x in expand(s[:m.start()]+item+s[m.end():])]
    if '[i]' in s: return [s.replace('[i]',f'[{j}]') for j in range(4)]
    return [s]

def f6():
    text=i.split('## B hardware representation ledger',1)[1].split('## Literal component',1)[0]
    listed=[]
    for row in text.splitlines():
        if not row.startswith('| '): continue
        path=row.split('|')[1].strip()
        if path.startswith(('clock_domains.','cores.','sync.','nocs[','memory.','formats.','energy.')):
            listed += [x for part in path.split('; ') for x in expand(part)]
    spec=HardwareSpec.model_validate(yaml.safe_load((root/'hw/designs/npu-l4.yaml').read_text()))
    actual={path for path,_ in sourced_leaves(spec)}
    assert len(listed)==len(set(listed))==59 and set(listed)==actual
    assert 16777216//32==524288 and 524288//524288==1
    assert 'bank=floor(offset_bytes/bank_region_bytes)' in i
    order=['matrix','vector','sram','dma','dma_port','channel','router','link','barrier']
    positions=[i.index(x+'(',i.index('Canonical owner enumeration:')) for x in order]
    assert positions==sorted(positions)
    assert 'native-owners/1' in i and 'operand capacity is required' in i


def f7():
    row=next(r for r in d.splitlines() if r.startswith('| K2 /'))
    assert 'fixed-delay fixture loader/import' in row
    assert 'Component mapper/import is required before B, not K2' in row
    assert 'M fixtures/mapper/import and K1' not in row


def f8():
    assert all(x in d for x in ('Q6-C','Q6-D','Q6-W','W+T totals **184–312**'))
    assert (40+28+8,64+48+12)==(76,124)
    assert (20+20+4,36+32+8)==(44,76)
    assert (76+44,124+76)==(120,200)
    assert (76+108,124+188)==(184,312)
    assert 'schedule W\nindependently' in d and 'charge it zero again to T' in d
    assert 4096//16==256 and 16*16==256


def f9():
    assert 'U0011-Q' in d and 'U0011-Q' in u
    assert 'the small K2/B diagnostic fixture is not that trigger' in d
    assert 'both routes still require G6 and full G5' in d


def f10():
    req=16*4*(2*256*256*3//256)
    assert req==98304 and 4*req==393216
    assert F(req*850,2**20)>79
    assert F(576*850,2**20)<1
    assert 576*32==18432 < 65536
    assert '576 requests' in d and 'K2 ≤256 fixed-delay jobs/1024 edges' in d
    assert 'planning ≤18432' in i
    assert 'Maximum production B scope is unchanged' in d


failures=[]
for n, check in enumerate((f1,f2,f3,f4,f5,f6,f7,f8,f9,f10),1):
    try: check()
    except (AssertionError,ValueError,KeyError,IndexError,StopIteration) as exc:
        failures.append(f'A-F{n}')
        print(f'A-F{n}: FAIL {type(exc).__name__}: {exc}')
    else: print(f'A-F{n}: PASS (proposal check only)')
print('document source:',ref or 'working tree','failures:',failures)
if failures: raise SystemExit(1)

# Shared B-F2/F3/F5/F6/F7: independent counterexamples, no analytic engine call.
assert 'head/embed' in d and 'layers/kv' in d
assert 'u_c0_duration_ps=null' in i and 'B effort6–10 hours' in d
assert 'half-open observation window [t0,t1)' in d
assert 'base/slower clock' in d and 'a tie alone is insufficient' in d
assert 'normally' in v and 'first claim' in v and 'V24' in v
assert 32+128-64 == 96
assert 64 != 128+32  # reuse and new outputs defeat old compute-byte identity
model = lambda c,m,k: max(F(c,k),F(m))
assert model(20,15,1)==20 and model(20,15,2)==15  # faster-only memory dominance
assert model(8,10,1)==model(8,10,2)==10  # base memory dominance
assert model(20,10,1)/model(20,10,2)==2  # tie does not imply speedup < k
per_op = lambda k: model(20,10,k)+model(0,4,k)
assert per_op(2)==14 != per_op(1)/2  # one remaining memory-only op suffices
print('shared DMA/clock/first-use proposals: PASS (no engine call)')
```
