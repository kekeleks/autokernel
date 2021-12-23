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

def m_maybe_expr_to_sympy(e: MaybeExpr):
    if e is None:
        raise ValueError("Cannot convert nil expression")
    if isinstance(e, Expr):
        return e.m_sympy()
    elif isinstance(e, SymbolPtr):
        return m_sym(e.symbol().name) | y_sym(e.symbol().name)

def y_maybe_expr_to_sympy(e: MaybeExpr):
    if e is None:
        raise ValueError("Cannot convert nil expression")
    if isinstance(e, Expr):
        return e.y_sympy()
    elif isinstance(e, SymbolPtr):
        return y_sym(e.symbol().name)

def y_sym(name: str):
    return sympy.Symbol("y_" + name) & ~ sympy.Symbol("m_" + name)

def m_sym(name: str):
    return ~ sympy.Symbol("y_" + name) & sympy.Symbol("m_" + name)

def n_sym(name: str):
    return ~ sympy.Symbol("y_" + name) & ~ sympy.Symbol("m_" + name)

def symop(op, a, b):
    return sympy.Symbol(f'{a.symbol().name}_{op}_{b.symbol().name}')

@dataclass
class Expr:
    type: str
    left: MaybeExpr
    right: MaybeExpr

    def y_sympy(self) -> Any:
        def eq(a, b):
            return (y_maybe_expr_to_sympy(a) & y_maybe_expr_to_sympy(b)
                    | (m_maybe_expr_to_sympy(a) & m_maybe_expr_to_sympy(b) & ~ y_maybe_expr_to_sympy(a) & ~ y_maybe_expr_to_sympy(b))
                    | (~ m_maybe_expr_to_sympy(a) & ~ m_maybe_expr_to_sympy(b)))
        #def sym_yes(
        fs = {
            "or":      lambda e: y_maybe_expr_to_sympy(e.left) | y_maybe_expr_to_sympy(e.right),       # a_ym | b_ym
            "and":     lambda e: y_maybe_expr_to_sympy(e.left) & y_maybe_expr_to_sympy(e.right),       # (a_ym) & (b_ym)
            "not":     lambda e: ~ y_maybe_expr_to_sympy(e.left)   & ~  ~ ~  m_maybe_expr_to_sympy(e.left),      # (a_n | a_m)
            "equal":   lambda e: symop("equal", e.left, e.right),
            "unequal": lambda e: symop("unequal", e.left, e.right),
            "lth":     lambda e: symop("lth", e.left, e.right),
            "leq":     lambda e: symop("leq", e.left, e.right),
            "gth":     lambda e: symop("gth", e.left, e.right),
            "geq":     lambda e: symop("geq", e.left, e.right),
            "symbol":  lambda e: y_maybe_expr_to_sympy(e.left),
        }
        if self.type not in fs:
            raise ValueError(f"Cannot convert {self.type} expression to sympy.")
        op = fs[self.type]
        return sympy.simplify(op(self))

    def m_sympy(self) -> Any:
        def eq(a, b):
            return y_maybe_expr_to_sympy(a) & y_maybe_expr_to_sympy(b) \
                    | (m_maybe_expr_to_sympy(a) & m_maybe_expr_to_sympy(b) \
                    & ~ y_maybe_expr_to_sympy(a) & ~ y_maybe_expr_to_sympy(b)) \
                    | (~ m_maybe_expr_to_sympy(a) & ~ m_maybe_expr_to_sympy(b))
        #def sym_yes(
        fs = {
            "or":      lambda e: m_maybe_expr_to_sympy(e.left) | m_maybe_expr_to_sympy(e.right),       # a_ym | b_ym
            "and":     lambda e: m_maybe_expr_to_sympy(e.left) & m_maybe_expr_to_sympy(e.right),       # (a_ym) & (b_ym)
            "not":     lambda e: ~ y_maybe_expr_to_sympy(e.left),      # (a_n | a_m)
            "equal":   lambda e: symop("equal", e.left, e.right),
            "unequal": lambda e: symop("unequal", e.left, e.right),
            "lth":     lambda e: symop("lth", e.left, e.right),
            "leq":     lambda e: symop("leq", e.left, e.right),
            "gth":     lambda e: symop("gth", e.left, e.right),
            "geq":     lambda e: symop("geq", e.left, e.right),
            "symbol":  lambda e: m_maybe_expr_to_sympy(e.left),
        }
        if self.type not in fs:
            raise ValueError(f"Cannot convert {self.type} expression to sympy.")
        op = fs[self.type]
        return sympy.simplify(op(self))

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
        return f"\nm_expr={sympy.logic.boolalg.to_dnf(self.m_sympy())}\n\ny_expr={self.y_sympy()}"

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

from graph_tool.all import Graph, graph_draw
from graph_tool.draw import sfdp_layout
import matplotlib.cm

def write_graph(filename):
    g = Graph()
    g_labels = g.new_vertex_property("string")
    g.vp.labels = g_labels
    g_refcount = g.new_vertex_property("int")
    g.vp.refcount = g_refcount

    vs = {}
    for id,s in symbol_by_id.items():
        v = g.add_vertex()
        vs[id] = v
        g_labels[v] = s.name

    refcount = {k: 0 for k in vs}
    for id,s in symbol_by_id.items():
        def rec(e: MaybeExpr):
            if isinstance(e, Expr):
                rec(e.left)
                rec(e.right)
            elif isinstance(e, SymbolPtr):
                g.add_edge(vs[s.id], vs[e.id])
                refcount[e.id] += 1
        rec(s.dependencies)

    for id,s in symbol_by_id.items():
        g_refcount[vs[id]] = refcount[id]

    g.save(filename)
    pos = sfdp_layout(g)
    graph_draw(g, pos, output_size=(1000, 1000), vertex_color=[1,1,1,0],
            #vertex_fill_color=g_refcount,
            vertex_size=1, edge_pen_width=1.2,
            vcmap=matplotlib.cm.gist_heat_r, output=f"{filename}.pdf")

def main() -> None:
    #kernel = load_kernel("/usr/src/linux")
    #kernel.syms["EXPERT"]

    #write_graph("fettergraph.xml.gz")
    s = SymbolPtr(sys.argv[1]).symbol()
    print(s)
