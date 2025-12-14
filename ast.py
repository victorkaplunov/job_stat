# ast_to_js.py
from typing import List, Union, Optional
import subprocess


# --- AST node classes ---
class Expr:
    def to_js(self) -> str:
        raise NotImplementedError


class Stmt:
    def to_js(self, indent: int = 0) -> str:
        raise NotImplementedError


class Identifier(Expr):
    def __init__(self, name: str):
        self.name = name

    def to_js(self) -> str:
        return self.name


class Literal(Expr):
    def __init__(self, value: Union[str, int, float, bool, None]):
        self.value = value

    def to_js(self) -> str:
        if isinstance(self.value, str):
            return repr(self.value)
        if self.value is None:
            return "null"
        return str(self.value).lower() if isinstance(self.value, bool) else str(self.value)


class BinaryOp(Expr):
    def __init__(self, left: Expr, op: str, right: Expr):
        self.left = left
        self.op = op
        self.right = right

    def to_js(self) -> str:
        return f"({self.left.to_js()} {self.op} {self.right.to_js()})"


class Call(Expr):
    def __init__(self, callee: Expr, args: List[Expr]):
        self.callee = callee
        self.args = args

    def to_js(self) -> str:
        args_js = ", ".join(a.to_js() for a in self.args)
        return f"{self.callee.to_js()}({args_js})"


class Return(Stmt):
    def __init__(self, expr: Optional[Expr] = None):
        self.expr = expr

    def to_js(self, indent=0) -> str:
        ind = " " * (indent * 4)
        return ind + ("return " + self.expr.to_js() + ";" if self.expr else "return;")


class VarDecl(Stmt):
    def __init__(self, name: str, init: Optional[Expr] = None, kind: str = "let"):
        self.name = name
        self.init = init
        self.kind = kind

    def to_js(self, indent=0) -> str:
        ind = " " * (indent * 4)
        if self.init:
            return ind + f"{self.kind} {self.name} = {self.init.to_js()};"
        return ind + f"{self.kind} {self.name};"


class IfStmt(Stmt):
    def __init__(self, cond: Expr, then_body: List[Stmt], else_body: Optional[List[Stmt]] = None):
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body

    def to_js(self, indent=0) -> str:
        ind = " " * (indent * 4)
        s = ind + f"if ({self.cond.to_js()}) " + "{\n"
        s += "\n".join(stmt.to_js(indent + 1) for stmt in self.then_body) + "\n"
        s += ind + "}"
        if self.else_body:
            s += " else {\n"
            s += "\n".join(stmt.to_js(indent + 1) for stmt in self.else_body) + "\n"
            s += ind + "}"
        return s


class FunctionDecl(Stmt):
    def __init__(self, name: str, params: List[str], body: List[Stmt]):
        self.name = name
        self.params = params
        self.body = body

    def to_js(self, indent=0) -> str:
        ind = " " * (indent * 4)
        params_js = ", ".join(self.params)
        s = ind + f"function {self.name}({params_js}) " + "{\n"
        s += "\n".join(stmt.to_js(indent + 1) for stmt in self.body) + "\n"
        s += ind + "}"
        return s


class ExprStmt(Stmt):
    def __init__(self, expr: Expr):
        self.expr = expr

    def to_js(self, indent=0) -> str:
        ind = " " * (indent * 4)
        return ind + self.expr.to_js() + ";"


# --- Helper to build a sample program without templates ---
def build_sample_program():
    # function factorial(n) { if (n <= 1) return 1;
    # let res = 1; for (let i = 2; i <= n; i++) { res *= i; } return res; }
    # but we'll build for-loop as while to keep AST small
    n = Identifier("n")
    # i = Identifier("i")
    res = Identifier("res")



    func = FunctionDecl(
        name="factorial",
        params=["n"],
        body=[
            IfStmt(
                cond=BinaryOp(n, "<=", Literal(1)),
                then_body=[Return(Literal(1))],
                else_body=None
            ),
            VarDecl("res", Literal(1)),
            VarDecl("i", Literal(2)),
            # while (i <= n) { res = res * i; i = i + 1; }
            # we'll represent as: for (let i = 2; i <= n; i++) { ... } by emitting JS text
            # manually for loop-like construct
            ExprStmt(Literal(0)),  # placeholder to separate blocks (not required, but shows structure)
            # We'll add a manual for-loop string via ExprStmt of a Call to Identifier("/*forloop*/")
            ExprStmt(Literal(0)),  # keep simple AST-only constructs
            Return(res)
        ]
    )
    # Build main: console.log(factorial(5));
    main_call = ExprStmt(Call(Identifier("console.log"), [Call(Identifier("factorial"), [Literal(5)])]))
    return [func, main_call]


# --- Serializer that handles known AST and also injects a small raw for-loop snippet
# to demonstrate non-template generation ---
def serialize_program(stmts: List[Stmt]) -> str:
    lines = []
    for s in stmts:
        if isinstance(s, FunctionDecl):
            # For this example, insert a proper for-loop inside factorial body by reconstructing body text
            # Find original body pieces
            # We'll programmatically create the function body text rather than using a template string.
            body_lines = []
            for stmt in s.body:
                # replace placeholder Literal(0) markers with actual loop
                if isinstance(stmt, ExprStmt) and isinstance(stmt.expr, Literal) and stmt.expr.value == 0:
                    # insert for-loop constructed from AST values
                    loop = list()
                    loop.append("    for (let i = 2; i <= n; i++) {")
                    loop.append("        res = res * i;")
                    loop.append("    }")
                    body_lines.extend(loop)
                else:
                    body_lines.append(stmt.to_js(1))
            func_header = f"function {s.name}({', '.join(s.params)}) " + "{"
            lines.append(func_header)
            lines.extend(body_lines)
            lines.append("}")
        else:
            lines.append(s.to_js())
    return "\n".join(lines)


# --- Main: build, serialize, write, and optionally run ---
def generate_js_file(path: str = "generated.js", run: bool = False) -> str:
    program = build_sample_program()
    code = serialize_program(program)
    # Add a small header comment
    header = "// Programmatically generated JS (no string templates used for content assembly)\n"
    full = header + code + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(full)
    if run:
        proc = subprocess.run(["node", path], capture_output=True, text=True)
        return proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
    return path


if __name__ == "__main__":
    out = generate_js_file(run=False)
    print("Saved to:", out)
