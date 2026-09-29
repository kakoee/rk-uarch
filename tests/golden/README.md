# golden — full-request regressions

scenarios/ are lane-writable requests; expected/ is human-owned and changes only via
`make golden-update` plus a docs/decisions/U*.md saying why. Until an expected file exists its
test skips with a reason. Golden tables are small on purpose (2-core and 4×4 designs, 12-point
grids) so CI stays fast.
