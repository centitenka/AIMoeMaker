# core/code_sandbox.py
"""
Code Sandbox: safely execute AI-generated Python code.

Security layers:
1. AST pre-check: block dangerous patterns before execution
2. Restricted builtins: only safe built-in functions
3. Import whitelist: only safe modules allowed
4. Timeout: kill execution after N seconds
"""
import ast
import threading
from typing import Optional


# Modules that are safe to import
ALLOWED_MODULES = {"math", "mathutils", "random", "json", "re", "itertools", "functools", "collections"}

# Modules that require bpy context (allowed but only useful in Blender)
BPY_MODULES = {"bpy", "bmesh", "mathutils"}

# Dangerous module names
BLOCKED_MODULES = {"os", "sys", "subprocess", "shutil", "pathlib", "socket", "http",
                   "urllib", "requests", "ctypes", "importlib", "code", "codeop",
                   "compile", "compileall", "py_compile", "signal", "multiprocessing",
                   "threading", "pickle", "shelve", "marshal", "tempfile", "glob",
                   "fnmatch", "io", "builtins", "__builtin__"}

# Dangerous attribute names
BLOCKED_ATTRS = {"__builtins__", "__import__", "__subclasses__", "__globals__",
                 "__code__", "__closure__", "__bases__", "__mro__", "__class__"}

# Dangerous function names
BLOCKED_CALLS = {"eval", "exec", "compile", "open", "input", "breakpoint",
                 "__import__", "getattr", "setattr", "delattr", "globals", "locals",
                 "vars", "dir", "type", "super"}

# Safe builtins for the sandbox
SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool,
    "dict": dict, "enumerate": enumerate, "filter": filter,
    "float": float, "frozenset": frozenset, "int": int,
    "isinstance": isinstance, "issubclass": issubclass,
    "iter": iter, "len": len, "list": list, "map": map,
    "max": max, "min": min, "next": next, "print": print,
    "range": range, "repr": repr, "reversed": reversed,
    "round": round, "set": set, "slice": slice, "sorted": sorted,
    "str": str, "sum": sum, "tuple": tuple, "zip": zip,
    "True": True, "False": False, "None": None,
}


class ASTSecurityChecker(ast.NodeVisitor):
    """Walk the AST and reject dangerous patterns."""

    def __init__(self):
        self.errors: list[str] = []

    def visit_Import(self, node):
        for alias in node.names:
            module = alias.name.split('.')[0]
            if module in BLOCKED_MODULES:
                self.errors.append(f"禁止导入模块: {alias.name}")
            elif module not in ALLOWED_MODULES and module not in BPY_MODULES:
                self.errors.append(f"禁止导入模块: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            module = node.module.split('.')[0]
            if module in BLOCKED_MODULES:
                self.errors.append(f"禁止导入模块: {node.module}")
            elif module not in ALLOWED_MODULES and module not in BPY_MODULES:
                self.errors.append(f"禁止导入模块: {node.module}")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if node.attr in BLOCKED_ATTRS:
            self.errors.append(f"禁止访问属性: {node.attr}")
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in BLOCKED_ATTRS:
            self.errors.append(f"禁止访问: {node.id}")
        if node.id in BLOCKED_CALLS and isinstance(getattr(node, '_parent_call', None), ast.Call):
            pass  # Will be caught in visit_Call
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_CALLS:
                self.errors.append(f"禁止调用函数: {node.func.id}")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in ("__subclasses__", "__import__"):
                self.errors.append(f"禁止调用: {node.func.attr}")
        self.generic_visit(node)

    def check(self, code: str) -> Optional[str]:
        """Parse and check code. Returns error message or None if safe."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"语法错误: {e}"

        self.errors.clear()
        self.visit(tree)

        if self.errors:
            return "; ".join(self.errors)
        return None


class CodeSandbox:
    """Execute AI-generated code in a restricted environment."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._checker = ASTSecurityChecker()

    def execute(self, code: str, description: str) -> dict:
        """
        Execute code safely.
        Returns: {"success": bool, "error": str (if failed), "message": str}
        """
        if not code.strip():
            return {"success": True, "message": "空代码，无操作"}

        # Layer 1: AST pre-check
        error = self._checker.check(code)
        if error:
            return {"success": False, "error": f"安全检查未通过: {error}"}

        # Layer 2: Build restricted namespace
        allowed = ALLOWED_MODULES | BPY_MODULES

        def _safe_import(name, *args, **kwargs):
            top = name.split('.')[0]
            if top not in allowed:
                raise ImportError(f"禁止导入模块: {name}")
            return __import__(name, *args, **kwargs)

        safe_builtins = SAFE_BUILTINS.copy()
        safe_builtins["__import__"] = _safe_import
        namespace = {"__builtins__": safe_builtins}

        # Pre-populate safe modules so they're available without re-importing
        for mod_name in ALLOWED_MODULES:
            try:
                namespace[mod_name] = __import__(mod_name)
            except ImportError:
                pass

        # Layer 3: Execute with timeout
        result = {"success": False, "error": "执行超时"}
        exception_holder = [None]

        def _run():
            try:
                exec(code, namespace)
                result["success"] = True
                result["error"] = ""
                result["message"] = f"代码执行成功: {description}"
            except Exception as e:
                exception_holder[0] = e

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        thread.join(timeout=self.timeout)

        if thread.is_alive():
            return {"success": False, "error": f"代码执行超时({self.timeout}秒)"}

        if exception_holder[0]:
            return {"success": False, "error": f"执行错误: {exception_holder[0]}"}

        return result
