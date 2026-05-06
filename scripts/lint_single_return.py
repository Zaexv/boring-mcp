#!/usr/bin/env python3
"""Lint rule: Single-Exit-Point.

Every function must have exactly one `return` statement, and it must be the
last statement in the function body. No early returns, no mid-function returns.

Usage:
    python scripts/lint_single_return.py [paths...]

Exits with code 1 if violations are found.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


class SingleReturnVisitor(ast.NodeVisitor):
    """AST visitor that enforces single-exit-point in all functions."""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.violations: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check that a function has at most one return, at the end."""
        returns = self._collect_returns(node)

        if len(returns) == 0:
            # No return statements — fine (implicit None return)
            pass
        elif len(returns) == 1:
            # One return — must be the last statement in the body
            ret = returns[0]
            last_stmt = node.body[-1]
            if ret.lineno != last_stmt.lineno:
                self.violations.append(
                    f"{self.filepath}:{ret.lineno}: "
                    f"function '{node.name}' has its return at line {ret.lineno} "
                    f"but the last statement is at line {last_stmt.lineno}. "
                    f"Return must be the final statement."
                )
        else:
            # Multiple returns — always a violation
            locations = ", ".join(str(r.lineno) for r in returns)
            self.violations.append(
                f"{self.filepath}:{node.lineno}: "
                f"function '{node.name}' has {len(returns)} return statements "
                f"(lines {locations}). Only one return at the end is allowed."
            )

    def _collect_returns(self, node: ast.AST) -> list[ast.Return]:
        """Collect all return statements in a function (excluding nested functions)."""
        returns: list[ast.Return] = []
        self._walk_excluding_nested(node, returns)
        return returns

    def _walk_excluding_nested(self, node: ast.AST, returns: list[ast.Return]) -> None:
        """Walk AST nodes but do not descend into nested function definitions."""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip nested functions entirely — they have their own scope
                continue
            if isinstance(child, ast.Return):
                returns.append(child)
            self._walk_excluding_nested(child, returns)


def check_file(filepath: Path) -> list[str]:
    """Check a single Python file for single-return violations."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))
    visitor = SingleReturnVisitor(str(filepath))
    visitor.visit(tree)
    return visitor.violations


def main() -> int:
    """Run the single-return linter on the given paths."""
    paths = sys.argv[1:] if len(sys.argv) > 1 else ["src/"]
    all_violations: list[str] = []

    for path_str in paths:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".py":
            all_violations.extend(check_file(path))
        elif path.is_dir():
            for py_file in sorted(path.rglob("*.py")):
                all_violations.extend(check_file(py_file))

    if all_violations:
        print("❌ Single-Exit-Point violations found:\n")
        for v in all_violations:
            print(f"  {v}")
        print(f"\n{len(all_violations)} violation(s) total.")
        print("Rule: Every function must have exactly one `return`, at the end.")
        return 1

    print("✅ All functions follow the single-exit-point rule.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
