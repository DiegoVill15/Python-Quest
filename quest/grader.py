import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .execution import validate_source

if os.name == "posix":
    import resource


TIME_LIMIT = 2
OUTPUT_LIMIT = 32_768


def _limit_output():
    resource.setrlimit(resource.RLIMIT_FSIZE, (OUTPUT_LIMIT, OUTPUT_LIMIT))
    resource.setrlimit(resource.RLIMIT_CPU, (TIME_LIMIT + 1, TIME_LIMIT + 1))
    if sys.platform != 'darwin':
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))


def _stop_process(process):
    if os.name == "nt":
        if process.poll() is not None:
            return
        try:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass
        if process.poll() is None:
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def run_one(source, stdin):
    try:
        validate_source(source)
    except (SyntaxError, ValueError, RecursionError) as error:
        return {"actual": "", "stdout": "", "error": str(error), "timed_out": False}
    with tempfile.TemporaryDirectory(prefix="python-quest-") as directory:
        path = Path(directory)
        (path / "solution.py").write_text(source, encoding="utf-8")
        with (path / "stdout.txt").open("w+b") as stdout, (path / "stderr.txt").open("w+b") as stderr:
            environment = {key: value for key, value in os.environ.items()
                           if key in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG", "LC_ALL"}}
            environment["PYTHONIOENCODING"] = "utf-8"
            environment["PYTHONNOUSERSITE"] = "1"
            process = None
            try:
                process = subprocess.Popen(
                    [sys.executable, "-I", str(Path(__file__).with_name('execution.py')), str(path / 'solution.py')], stdin=subprocess.PIPE,
                    stdout=stdout, stderr=stderr, cwd=path, env=environment,
                    preexec_fn=_limit_output if os.name == "posix" else None,
                    start_new_session=os.name == "posix",
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
                )
                try:
                    process.stdin.write(stdin.encode())
                    process.stdin.close()
                except BrokenPipeError:
                    process.stdin.close()
                deadline = time.monotonic() + TIME_LIMIT
                stopped_for = None
                while process.poll() is None:
                    if stdout.name and (os.path.getsize(stdout.name) >= OUTPUT_LIMIT
                                        or os.path.getsize(stderr.name) >= OUTPUT_LIMIT):
                        stopped_for = "Salida demasiado extensa"
                    elif time.monotonic() >= deadline:
                        stopped_for = f"Tiempo agotado ({TIME_LIMIT} segundos)"
                    if stopped_for:
                        _stop_process(process)
                        break
                    time.sleep(0.02)
                process.wait()
            except OSError as error:
                return {"actual": "", "stdout": "", "error": str(error), "timed_out": False}
            finally:
                if process is not None:
                    _stop_process(process)
                    process.wait()
            stdout.seek(0)
            stderr.seek(0)
            output = stdout.read(OUTPUT_LIMIT).decode("utf-8", errors="replace")
            actual = output.strip()
            error = stderr.read(1000).decode("utf-8", errors="replace").strip()
            if stopped_for:
                error = stopped_for
            elif "File size limit exceeded" in error or stdout.seek(0, 2) >= OUTPUT_LIMIT:
                error = "Salida demasiado extensa"
            elif process.returncode and not error:
                error = f"El programa terminó con código {process.returncode}."
            return {"actual": actual, "stdout": output, "error": error[-1000:],
                    "timed_out": error.startswith("Tiempo agotado")}


def run_cases(source, tests):
    return [
        {**run_one(source, case["input"]), "passed": False}
        for case in tests
    ]


def grade(source, tests):
    results = run_cases(source, tests)
    for case, result in zip(tests, results):
        result["passed"] = not result["error"] and result["actual"] == case["expected"].strip()
    return results
