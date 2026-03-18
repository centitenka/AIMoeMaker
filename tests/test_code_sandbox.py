# tests/test_code_sandbox.py
from core.code_sandbox import CodeSandbox


def test_safe_code_executes():
    sandbox = CodeSandbox()
    result = sandbox.execute("x = 1 + 2", "simple math")
    assert result["success"] is True


def test_import_os_blocked():
    sandbox = CodeSandbox()
    result = sandbox.execute("import os", "import os")
    assert result["success"] is False
    assert "禁止" in result["error"] or "blocked" in result["error"].lower()


def test_import_sys_blocked():
    sandbox = CodeSandbox()
    result = sandbox.execute("import sys", "import sys")
    assert result["success"] is False


def test_import_subprocess_blocked():
    sandbox = CodeSandbox()
    result = sandbox.execute("import subprocess", "import subprocess")
    assert result["success"] is False


def test_open_blocked():
    sandbox = CodeSandbox()
    result = sandbox.execute("f = open('/etc/passwd')", "open file")
    assert result["success"] is False


def test_eval_blocked():
    sandbox = CodeSandbox()
    result = sandbox.execute("eval('1+1')", "eval")
    assert result["success"] is False


def test_exec_blocked():
    sandbox = CodeSandbox()
    result = sandbox.execute("exec('x=1')", "exec")
    assert result["success"] is False


def test_dunder_builtins_blocked():
    sandbox = CodeSandbox()
    result = sandbox.execute("__builtins__", "access builtins")
    assert result["success"] is False


def test_dunder_import_blocked():
    sandbox = CodeSandbox()
    result = sandbox.execute("__import__('os')", "dunder import")
    assert result["success"] is False


def test_dunder_subclasses_blocked():
    sandbox = CodeSandbox()
    result = sandbox.execute("().__class__.__subclasses__()", "subclasses")
    assert result["success"] is False


def test_safe_builtins_available():
    sandbox = CodeSandbox()
    result = sandbox.execute("x = len([1,2,3])\ny = range(5)\nz = list(y)", "safe builtins")
    assert result["success"] is True


def test_math_import_allowed():
    sandbox = CodeSandbox()
    result = sandbox.execute("import math\nx = math.pi", "math import")
    assert result["success"] is True


def test_timeout_protection():
    sandbox = CodeSandbox(timeout=1)
    result = sandbox.execute("while True: pass", "infinite loop")
    assert result["success"] is False
    assert "超时" in result["error"] or "timeout" in result["error"].lower()


def test_empty_code():
    sandbox = CodeSandbox()
    result = sandbox.execute("", "empty")
    assert result["success"] is True
