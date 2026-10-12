#!/usr/bin/env bash
# Read-only inventory on the designated Linux host; installs and changes nothing.
set -eu
python3 - <<'PYHOST'
import json,os,platform,shutil,subprocess
from pathlib import Path
r={'hostname':platform.node(),'kernel':platform.release(),'architecture':platform.machine(),'cpu_count':os.cpu_count(),'user':os.environ.get('USER'),'wsl_detected':'microsoft' in platform.release().lower(),'os_release':Path('/etc/os-release').read_text() if Path('/etc/os-release').exists() else None,'memory':{line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:','MemAvailable:'))},'home_disk':dict(zip(('total','used','free'),shutil.disk_usage(Path.home()))),'tools':{}}
for cmd in ('git','python3','uv','cc','c++','cmake','podman','docker','rustc','cargo','gh'):
 p=shutil.which(cmd)
 r['tools'][cmd]={'path':p}
 if p:
  try:
   v=subprocess.run([p,'--version'],capture_output=True,text=True,timeout=10)
   r['tools'][cmd].update(exit_code=v.returncode,version=(v.stdout+v.stderr).strip().splitlines()[:2])
  except Exception as e:r['tools'][cmd]['error']=type(e).__name__
print(json.dumps(r,indent=2))
PYHOST
