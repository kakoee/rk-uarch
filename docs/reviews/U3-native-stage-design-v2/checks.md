# Reproducible documentation checks

Run the following standard-library block from repository root with `python3`.
It imports no repository module, runs no engine/producer and generates no artifacts.
It checks documentation links and JSON projections, retained/reconciled arithmetic and
estimate totals. These are author checks, not native verification or independent review.
Git ancestry/scope/whitespace and normal commit hooks are additional checks in the handoff.

```python
import json
import math
import re
from fractions import Fraction as F
from pathlib import Path

package = Path('docs/reviews/U3-native-stage-design-v2')
files = sorted(package.glob('*.md'))
assert len(files) == 8
links = projections = 0
for path in files:
    body = path.read_text()
    for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^\s)]+)\)', body):
        if '://' in target or target.startswith('#'):
            continue
        local = target.split('#', 1)[0]
        assert (path.parent / local).exists(), (path, target)
        links += 1
    for block in re.findall(r'```json\n(.*?)\n```', body, re.S):
        json.loads(block)
        projections += 1

edge = lambda k: math.ceil(F(k * 10**12, 1_200_000_000))
assert [edge(k) for k in range(5)] == [0, 834, 1667, 2500, 3334]
assert edge(10**9) == 833_333_333_334
assert (max(3000, 5000) + 2000, 3000 + 5000 + 2000) == (7000, 10000)
assert 2 * 16 * 256 * 256 == 2_097_152
assert (2*16*256, 2*256*256, 4*16*256) == (8192, 131072, 16384)
assert 32 + 136 + 526 + 8 == 702
assert (2*3*5*7, 2*3*256*256) == (210, 393216)
assert 32 + 1 + 513 + 1 == 547
assert 2*257*256*256 == 33_685_504
assert (32+256+766+128, 32+129+511+1) == (1182, 673)
assert 1182+673 == 1855
assert 2*147456 == 294912 < 16777216
cap = F(10**12) * (1-F(350,3900)) / 8
assert cap == F(4437500000000,39)
service = F(256*10**12,cap)
assert service == F(159744,71)
assert math.ceil(52000+service) == 54250
assert math.ceil(52000+2*service) == 56500
def next_edge_1ghz(t, n):
    return (math.ceil(F(t, 1000)) + n)*1000
assert next_edge_1ghz(54250, 4) == 59000
assert next_edge_1ghz(56500, 4) == 61000
assert next_edge_1ghz(next_edge_1ghz(54250, 4), 1) == 60000
assert next_edge_1ghz(next_edge_1ghz(56500, 4), 1) == 62000
assert 62000+32000 == 94000
assert (2*17*4*2, 2*32*4*2, 2*1*4*2) == (272,512,16)
assert (3*5*4*4*4, 3*(2*4*4*6+8*4*4), 3*2*4*4*6) == (960,960,576)
assert (32+128-64, 2000+4000+2000, 1000+4000+1000) == (96,8000,6000)
assert (20+20+10+32, 32+32+16+52) == (82,132)
assert (12+8+8+24, 20+14+12+40) == (52,86)
assert (6+4+4+8, 10+6+6+12) == (22,34)
assert (82+52+22, 132+86+34) == (156,252)
assert (40+28+8, 64+48+12) == (76,124)  # shared W
assert (20+20+4, 36+32+8) == (44,76)  # R-specific
assert (76+44, 124+76) == (120,200)
assert (76+108, 124+188) == (184,312)  # W+T if R has not supplied W
assert (28+32+8, 48+56+16) == (68,120)
assert (60+36+12, 104+64+20) == (108,188)
assert (3*(2+2+2), 3*(4+4+4)) == (18,36)
print(f'PASS: {len(files)} Markdown files, {links} local links, '
      f'{projections} JSON projections; independent arithmetic/effort assertions passed.')
```
