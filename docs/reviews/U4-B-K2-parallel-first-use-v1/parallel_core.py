"""Thread-free fork supervision and bounded atomic receipts; no project/native imports."""

import fcntl
import hashlib
import json
import multiprocessing
import os
import signal
import stat
import threading
import time
import uuid
from pathlib import Path


def require(ok, why):
    if not ok:
        raise ValueError(why)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


class Store:
    """All workers share one flock budget; link publication never replaces a receipt."""

    def __init__(self, root, budget):
        self.root, self.budget = Path(root), budget
        require(self.root.is_dir() and not self.root.is_symlink(), "real receipt directory")
        require(budget > 0, "positive receipt budget")

    def path(self, name):
        require(
            isinstance(name, str)
            and not name.startswith("/")
            and all(x not in ("", ".", "..") for x in name.split("/")),
            "confined receipt path",
        )
        path = self.root / name
        for parent in reversed(path.parents):
            if parent == self.root or self.root in parent.parents:
                require(not parent.is_symlink(), "real receipt parent")
                parent.mkdir(exist_ok=True)
                require(stat.S_ISDIR(parent.lstat().st_mode), "real receipt parent")
        return path

    def publish(self, name, data, *, shared=False):
        lock = os.open(self.root / ".budget-lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX)
            path = self.path(name)
            if path.exists() or path.is_symlink():
                require(
                    shared and stat.S_ISREG(path.lstat().st_mode) and path.read_bytes() == data,
                    "duplicate receipt or different-byte blob collision",
                )
                return name
            budget_path = self.root / ".budget.json"
            used = json.loads(budget_path.read_bytes())["reserved"] if budget_path.exists() else 0
            require(used + len(data) + 4096 <= self.budget, "receipt budget exceeded")
            # Reserve first: death mid-write cannot bypass the budget. Leave failures
            # private and incomplete; no refund/retry disguises a partial publication.
            budget_tmp = self.root / (".budget-" + uuid.uuid4().hex)
            with budget_tmp.open("xb") as stream:
                stream.write(encoded({"reserved": used + len(data)}))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(budget_tmp, budget_path)
            temp = path.parent / (".pending-" + str(os.getpid()) + "-" + uuid.uuid4().hex)
            with temp.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temp, path, follow_symlinks=False)
            temp.unlink()
            fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
            return name
        finally:
            os.close(lock)

    def blob(self, data):
        return self.publish("blobs/" + digest(data).split(":")[1], data, shared=True)

    def json(self, name, value):
        return self.publish(name, encoded(value))

    def check_budget(self):
        paths = list(self.root.rglob("*"))
        require(not any(p.is_symlink() for p in paths), "receipt symlink")
        require(
            sum(p.stat().st_size for p in paths if p.is_file()) <= self.budget,
            "actual receipt budget exceeded",
        )
        require(
            not any(p.name.startswith(".pending-") for p in paths), "unfinished atomic publication"
        )


def safe_fork(executable_paths=()):
    require(
        threading.active_count() == 1 and len(list(Path("/proc/self/task").iterdir())) == 1,
        "fork requires no active threads",
    )
    require(not multiprocessing.active_children(), "no inherited worker children")
    for entry in Path("/proc/self/fd").iterdir():
        try:
            target = os.readlink(entry)
        except FileNotFoundError:
            continue
        require(target not in executable_paths, "executable descriptor open at fork")


def _send(connection, value):
    connection.send_bytes(encoded(value))


def _receive(connection):
    return json.loads(connection.recv_bytes(1024 * 1024))


class WorkerStopped(BaseException):
    pass


def _worker(connection, function, inherited):
    for fd in inherited:
        os.close(fd)
    os.setsid()

    def stopped(*_):
        raise WorkerStopped("owned worker termination")

    signal.signal(signal.SIGTERM, stopped)
    try:
        _send(connection, {"kind": "ready"})
        while True:
            message = _receive(connection)
            if message == {"kind": "stop"}:
                return
            require(message.get("kind") == "task", "worker protocol")
            task = message["task"]
            result = function(task)
            _send(connection, {"kind": "done", "task": task, "result": result})
    except BaseException as error:
        try:
            _send(connection, {"kind": "error", "error": repr(error)})
        except (BrokenPipeError, OSError):
            pass
        raise
    finally:
        connection.close()


def run_workers(
    tasks,
    function,
    *,
    workers,
    task_timeout,
    total_timeout,
    startup_timeout=30,
    executable_paths=(),
    progress=None,
):
    """One task/case per worker at a time. All forks precede dispatch; no pool threads.

    Function/state are inherited only via Linux fork. Results are bounded JSON over
    pipes, not pickle or AcceptedHostBinding reconstruction. Call from a dedicated
    container: if a worker cannot unwind its production runner, exit the container.
    """
    tasks = list(tasks)
    require(tasks and len(tasks) == len(set(tasks)), "nonempty unique task membership")
    require(0 < workers <= len(tasks), "bounded worker count")
    require(min(task_timeout, total_timeout, startup_timeout) > 0, "positive deadlines")
    safe_fork(executable_paths)
    context = multiprocessing.get_context("fork")
    states, done, next_index = [], {}, 0
    start = time.monotonic()
    failed = True
    try:
        for _ in range(workers):
            parent, child = context.Pipe(duplex=True)
            inherited = [s["connection"].fileno() for s in states] + [parent.fileno()]
            process = context.Process(target=_worker, args=(child, function, inherited))
            process.start()
            child.close()
            states.append(
                {
                    "process": process,
                    "connection": parent,
                    "task": None,
                    "ready": False,
                    "sent": time.monotonic(),
                }
            )
        while len(done) != len(tasks):
            now = time.monotonic()
            require(now - start < total_timeout, "campaign supervision deadline")
            for state in states:
                process, connection = state["process"], state["connection"]
                if connection.poll():
                    message = _receive(connection)
                    if message.get("kind") == "ready":
                        require(
                            not state["ready"] and state["task"] is None, "duplicate worker ready"
                        )
                        state["ready"] = True
                    elif message.get("kind") == "done":
                        task = message["task"]
                        require(
                            task == state["task"] and task not in done,
                            "duplicate/foreign worker result",
                        )
                        done[task] = message["result"]
                        state["task"] = None
                        if progress:
                            progress(task, message["result"])
                    else:
                        raise ValueError("worker failure: " + repr(message))
                require(process.exitcode is None, "worker exited before complete collection")
                if state["ready"] and state["task"] is None and next_index < len(tasks):
                    task = tasks[next_index]
                    next_index += 1
                    state["task"], state["sent"] = task, now
                    _send(connection, {"kind": "task", "task": task})
                deadline = task_timeout if state["ready"] else startup_timeout
                if state["task"] is not None or not state["ready"]:
                    require(now - state["sent"] < deadline, "worker task/startup deadline")
            time.sleep(0.01)
        require(set(done) == set(tasks), "complete worker membership")
        for state in states:
            _send(state["connection"], {"kind": "stop"})
        for state in states:
            state["process"].join(5)
            require(state["process"].exitcode == 0, "worker did not exit cleanly")
        failed = False
        return [done[t] for t in tasks]
    finally:
        # SIGTERM raises in the worker so the unchanged runner's finally can reap
        # its native process group. A stuck worker gets SIGKILL; the dedicated
        # container's exit/outer launcher then reaps remaining owned descendants.
        for state in states:
            process = state["process"]
            if failed and process.is_alive():
                process.terminate()
        deadline = time.monotonic() + 5
        for state in states:
            process = state["process"]
            process.join(max(0, deadline - time.monotonic()))
            if process.is_alive():
                process.kill()
                process.join(5)
            state["connection"].close()
            if process.exitcode is not None:
                process.close()


def verify_six_way(rows, cases):
    """Receipt-only cross-mode/repetition check; cannot make a result qualify."""
    expected = {
        (mode, repetition, case)
        for case in cases
        for mode in ("debug", "release")
        for repetition in (0, 1, 2)
    }
    observed = [(r["mode"], r["repetition"], r["case_id"]) for r in rows]
    require(
        expected and len(observed) == len(expected) and set(observed) == expected,
        "exact six-way slot membership",
    )
    seen = {}
    for row in rows:
        key = (row["request_hash"], row["stdout_hash"], row["stderr_hash"], row["status"])
        require(seen.setdefault(row["case_id"], key) == key, "six-way result drift")


def snapshot_paths(roots):
    """Complete bounded deployment snapshot; private evidence, never a repository manifest."""
    rows = {}
    for root in map(Path, roots):
        if not root.exists() and not root.is_symlink():
            rows[str(root)] = {"absent": True}
            continue
        paths = [root, *root.rglob("*")] if root.is_dir() and not root.is_symlink() else [root]
        for path in paths:
            st = path.lstat()
            row = {
                "uid": st.st_uid,
                "gid": st.st_gid,
                "mode": st.st_mode,
                "inode": st.st_ino,
                "size": st.st_size,
            }
            if path.is_symlink():
                row["symlink"] = str(path.readlink())
            elif path.is_file():
                row["byte_hash"] = digest(path.read_bytes())
            else:
                require(path.is_dir(), "unexpected deployment inode kind")
            rows[str(path)] = row
    return rows


def verify_snapshots(before, after):
    require(bool(before) and before == after, "full sealed deployment changed")
