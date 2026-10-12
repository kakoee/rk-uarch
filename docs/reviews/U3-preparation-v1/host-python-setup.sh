#!/usr/bin/env bash
# Run as javid on the designated server. No sudo, system-Python changes or repository edits.
set -euo pipefail
[ "$(id -un)" = javid ] || { echo 'Run this as javid.' >&2; exit 1; }
[ "$(hostname)" = v2202507191245365394 ] || { echo 'Unexpected host; stop.' >&2; exit 1; }
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  command -v curl >/dev/null 2>&1 || { echo 'curl is missing; ask the administrator to install it.' >&2; exit 1; }
  u3_installer=$(mktemp)
  trap 'rm -f "$u3_installer"' EXIT
  curl --proto '=https' --tlsv1.2 -fsSL https://astral.sh/uv/install.sh -o "$u3_installer"
  UV_INSTALL_DIR="$HOME/.local/bin" UV_NO_MODIFY_PATH=1 sh "$u3_installer"
fi
uv --version
uv python install 3.12
u3_python=$(uv python find --managed-python 3.12)
"$u3_python" --version
python3 - <<'PYHOST'
import json,platform,shutil,subprocess,os
r={'hostname':platform.node(),'tools':{}}
for cmd in ('uv','podman','docker','rustc','cargo','newuidmap','newgidmap','tmux'):
 p=shutil.which(cmd);r['tools'][cmd]={'path':p}
 if p and cmd not in ('newuidmap','newgidmap'):
  v=subprocess.run([p, '-V' if cmd == 'tmux' else '--version'],capture_output=True,text=True,timeout=10)
  r['tools'][cmd].update(exit_code=v.returncode,version=(v.stdout+v.stderr).strip().splitlines()[:2])
from pathlib import Path
r['subordinate_id_entries']={}
for filename in ('/etc/subuid','/etc/subgid'):
 p=Path(filename)
 r['subordinate_id_entries'][filename]=[line for line in p.read_text().splitlines() if line.startswith('javid:')] if p.exists() else []
print(json.dumps(r,indent=2))
PYHOST
printf '%s\n' 'Python setup complete. No container installation, runner registration, repository edits or benchmarks performed.'
