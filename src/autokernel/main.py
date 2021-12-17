import os
import base64
import json
import sys

def load_kernel_symbols(filename: str) -> dict:
    with open(filename, "r") as f:
        return json.load(f)

raw_syms = load_kernel_symbols("./syms-linux-5.15.10.json")

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

def main() -> None:
    #kernel = load_kernel("/usr/src/linux")
    #kernel.syms["EXPERT"]

    syms = {}
    for ptr,s in raw_syms.items():
        if "name" not in s:
            continue
        syms[s["name"]] = s
        s["ptr"] = ptr

    #print(json.dumps(syms["PCMCIA_RAYCS"]))
    print("properties:")
    s = syms.get(sys.argv[1], None)
    if not s:
        s = raw_syms[sys.argv[1]]
    for i in s["properties"]:
        if "type" not in i:
            continue
        print(f"{i['type']}")
        if i["text"]:
            print(base64.b64decode(i["text"]))
        if "expr" in i:
            print("expr: ", end="")
            print_expr(i["expr"])
            print()
        if "expr" in i["visible"]:
            print("vis expr: ", end="")
            print_expr(i["visible"]["expr"])
            print()
    print("current value: ", end="")
    if "val" in s["curr"]:
        if s["curr"]["val"].startswith("0x"):
            print(raw_syms[s["curr"]["val"]]["name"])
        else:
            print(base64.b64decode(s["curr"]["val"]))
    else:
        print("Keine du")
    if "expr" in s["dir_dep"]:
        print("dir dep: ", end="")
        print_expr(s["dir_dep"]["expr"])
        print()
    if "expr" in s["rev_dep"]:
        print("rev dep: ", end="")
        print_expr(s["rev_dep"]["expr"])
        print()
    if "expr" in s["implied"]:
        print("implied: ", end="")
        print_expr(s["implied"]["expr"])
        print()
