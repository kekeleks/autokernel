from __future__ import annotations

import base64
import json
import sys
from dataclasses import dataclass
from typing import Union

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

    def __str__(self):
        return f"sym {self.id}"

@dataclass
class Expr:
    type: str
    left: MaybeExpr
    right: MaybeExpr

    def __str__(self):
        return f"({self.type}, {self.left}, {self.right})"

@dataclass
class Symbol:
    id: str
    name: str
    dir_depend: MaybeExpr
    rev_depend: MaybeExpr
    implied: MaybeExpr
    #cur_val: Value

    def __str__(self):
        return f"Symbol({self.id=}, {self.name=}, {self.dir_depend=}, {self.rev_depend=}, {self.implied=})"

MaybeExpr = Union[Expr, SymbolPtr, None]

def load_kernel_symbols(filename: str) -> dict:
    with open(filename, "r") as f:
        return json.load(f)

raw_syms = load_kernel_symbols("./syms-linux-5.15.10.json")

def parse_expr(e: Union[dict, str, None]) -> MaybeExpr:
    if e is not None:
        return
    if isinstance(e, dict):
        return Expr(e["type"], parse_expr(e["left"]), parse_expr(e["right"]))
    elif isinstance(e, str):
        return SymbolPtr(e)

symbol_by_id: dict[str, Symbol] = {}
symbol_by_name: dict[str, Symbol] = {}

for ptr,s in raw_syms.items():
    if "name" not in s:
        continue

    symbol = Symbol(
        id=ptr,
        name=s["name"],
        dir_depend=parse_expr(s["dir_dep"].get("expr", None)),
        rev_depend=parse_expr(s["rev_dep"].get("expr", None)),
        implied=parse_expr(s["implied"].get("expr", None)),
    )

    symbol_by_id[symbol.id] = symbol
    symbol_by_name[symbol.name] = symbol

def main() -> None:
    #kernel = load_kernel("/usr/src/linux")
    #kernel.syms["EXPERT"]

    s = SymbolPtr(sys.argv[1]).symbol()
    print(s)
