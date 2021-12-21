from __future__ import annotations

import base64
import json
import sympy
import sys
from dataclasses import dataclass
from typing import Any, Union

@dataclass
class SymbolPtr:
    id: str

    def symbol(self) -> Symbol:
        s = symbol_by_id.get(self.id, None)
        if s is None:
            s = symbol_by_name.get(self.id, None)
        if s is None:
            raise ValueError(f"Symbol with id or name {self.id} not found")
        return s

    def __repr__(self):
        try:
            name = self.symbol().name
        except ValueError:
            name = self.id
        return f"sym {name}"

def maybe_expr_to_sympy(e: MaybeExpr):
    if e is None:
        raise ValueError("Cannot convert nil expression")
    if isinstance(e, Expr):
        return e.sympy()
    elif isinstance(e, SymbolPtr):
        return sympy.Symbol(e.symbol().name)

@dataclass
class Expr:
    type: str
    left: MaybeExpr
    right: MaybeExpr

    def sympy(self) -> Any:
        def eq(a, b):
            return (a & b) | (~a & ~b)
        fs = {
            "or":      lambda e: maybe_expr_to_sympy(e.left) | maybe_expr_to_sympy(e.right),       # a_ym | b_ym
            "and":     lambda e: maybe_expr_to_sympy(e.left) & maybe_expr_to_sympy(e.right),       # (a_ym) & (b_ym)
            "not":     lambda e: ~maybe_expr_to_sympy(e.left),                                     # (a_n | a_m)
            "equal":   lambda e: eq(maybe_expr_to_sympy(e.left), maybe_expr_to_sympy(e.right)),    # (a_y & b_y) | (a_m & b_m) | (a_n & b_n)
            "unequal": lambda e: ~eq(maybe_expr_to_sympy(e.left), maybe_expr_to_sympy(e.right)),   # ~((a_y & b_y) | (a_m & b_m) | (a_n & b_n))
            "lth":     lambda e: maybe_expr_to_sympy(e.left) <  maybe_expr_to_sympy(e.right),      #
            "leq":     lambda e: maybe_expr_to_sympy(e.left) <= maybe_expr_to_sympy(e.right),      #
            "gth":     lambda e: maybe_expr_to_sympy(e.left) >  maybe_expr_to_sympy(e.right),      #
            "geq":     lambda e: maybe_expr_to_sympy(e.left) >= maybe_expr_to_sympy(e.right),      #
            "symbol":  lambda e: maybe_expr_to_sympy(e.left),
        }
        if self.type not in fs:
            raise ValueError(f"Cannot convert {self.type} expression to sympy.")
        op = fs[self.type]
        return op(self)
        return sympy.logic.boolalg.to_dnf(op(self))

    def __repr__(self):
        return f"{self.sympy()}"

@dataclass
class Symbol:
    id: str
    name: str
    dependencies: MaybeExpr
    selected_by: MaybeExpr
    implied: MaybeExpr
    #cur_val: Value

MaybeExpr = Union[Expr, SymbolPtr, None]

def load_kernel_symbols(filename: str) -> dict:
    with open(filename, "r") as f:
        return json.load(f)

raw_syms = load_kernel_symbols("./syms-linux-5.15.10.json")

def parse_expr(e: Union[dict, str, None]) -> MaybeExpr:
    if e is None:
        return None
    if isinstance(e, dict):
        return Expr(e["type"], parse_expr(e["left"]), parse_expr(e["right"]))
    elif isinstance(e, str):
        return SymbolPtr(e)

symbol_by_id: dict[str, Symbol] = {}
symbol_by_name: dict[str, Symbol] = {}


def print_expr(expr):
    if not expr:
        return
    if isinstance(expr, dict):
        print(f"({expr['type']} ", end="")
        print_expr(expr["left"])
        print(" ", end="")
        print_expr(expr["right"])
        print(")", end="")
    elif isinstance(expr, str):
        print(raw_syms[expr]["name"], raw_syms[expr]["ptr"], end="")


for ptr,s in raw_syms.items():
    if "name" not in s:
        continue

    symbol = Symbol(
        id=ptr,
        name=s["name"],
        dependencies=parse_expr(s["dir_dep"].get("expr", None)),
        selected_by=parse_expr(s["rev_dep"].get("expr", None)),
        implied=parse_expr(s["implied"].get("expr", None)),
    )

    symbol_by_id[symbol.id] = symbol
    symbol_by_name[symbol.name] = symbol

def main() -> None:
    #kernel = load_kernel("/usr/src/linux")
    #kernel.syms["EXPERT"]

    s = SymbolPtr(sys.argv[1]).symbol()
    print(s)
