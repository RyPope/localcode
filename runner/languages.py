"""Supported languages: how to lay out a submission and the commands that compile and run it.

Adding a language means adding a harness under harness/ and one entry in LANGUAGES.
"""

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from harness.cpp_gen import gen_main

HARNESS = Path(__file__).resolve().parent / "harness"
CASES, RESULTS = "cases.json", "results.jsonl"

# Implicit imports share the user's first line so reported line numbers match the editor.
JAVA_IMPORTS = (
    "import java.util.*; import java.util.function.*; import java.util.stream.*; import java.math.*; "
    "import javafx.util.Pair; "
)
KOTLIN_IMPORTS = "import java.util.*; import kotlin.math.*; "
JVM_CLASSPATH = ".:/opt/lib/gson.jar:/opt/lib/driver.jar"


@dataclass(frozen=True)
class Plan:
    compile: list[str] | None
    run: list[str]
    limit_address_space: bool  # False for the JVM, which reserves address space up front; its heap is capped instead


@dataclass(frozen=True)
class Language:
    name: str
    startup_grace_ms: int
    prepare: Callable[[dict, Path, int], Plan]  # (request, workdir, memory_mb) -> Plan


def _copy(names: list[str], src: Path, dest: Path) -> None:
    for name in names:
        shutil.copy(src / name, dest)


def _jvm_run(classpath: str, memory_mb: int, *extra: str) -> list[str]:
    heap = max(64, memory_mb * 3 // 4)  # leave room for metaspace and thread stacks
    return ["java", f"-Xmx{heap}m", "-Xss256m", "-XX:+UseSerialGC", *extra, "-cp", classpath, "Driver", CASES, RESULTS]


def _python(req: dict, workdir: Path, memory_mb: int) -> Plan:
    (workdir / "solution.py").write_text(req["code"])
    _copy(["py_driver.py"], HARNESS, workdir)
    return Plan(None, ["python3", "-I", "py_driver.py", "solution.py", CASES, RESULTS], True)


def _java(req: dict, workdir: Path, memory_mb: int) -> Plan:
    sources = ["Solution.java", "ListNode.java", "TreeNode.java"]
    (workdir / "Solution.java").write_text(JAVA_IMPORTS + req["code"])
    _copy(sources[1:], HARNESS / "jvm", workdir)
    compile_cmd = ["javac", "-nowarn", "-encoding", "UTF-8", "-cp", JVM_CLASSPATH, "-d", ".", *sources]
    return Plan(compile_cmd, _jvm_run(JVM_CLASSPATH, memory_mb, "-XX:TieredStopAtLevel=1"), False)


def _kotlin(req: dict, workdir: Path, memory_mb: int) -> Plan:
    sources = ["Solution.kt", "ListNode.kt", "TreeNode.kt"]
    (workdir / "Solution.kt").write_text(KOTLIN_IMPORTS + req["code"])
    _copy(sources[1:], HARNESS / "jvm", workdir)
    classpath = f"{JVM_CLASSPATH}:/opt/kotlinc/lib/kotlin-stdlib.jar"
    return Plan(["kotlinc", "-nowarn", "-d", ".", *sources], _jvm_run(classpath, memory_mb), False)


def _cpp(req: dict, workdir: Path, memory_mb: int) -> Plan:
    (workdir / "main.cpp").write_text(gen_main(req["code"], req["cpp_sig"]))
    # Flags must match the precompiled header built in the Dockerfile.
    compile_cmd = ["g++", "-std=c++20", "-O2", "-w", "-I", "/opt/lc", "-o", "sol", "main.cpp", "/opt/lc/lc_io.o"]
    return Plan(compile_cmd, ["./sol", CASES, RESULTS], True)


LANGUAGES: dict[str, Language] = {
    lang.name: lang
    for lang in (
        Language("python", 1000, _python),
        Language("java", 2000, _java),
        Language("kotlin", 2500, _kotlin),
        Language("cpp", 500, _cpp),
    )
}
