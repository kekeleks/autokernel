#!/bin/bash

cp ../src/bridge/main.c scripts/kconfig/bridge.c
cp ../src/bridge/base64.h scripts/kconfig/base64.h
gcc  -g -fsanitize=address -Wp,-MMD,scripts/kconfig/.bridge.o.d -Wall -Wstrict-prototypes -O2 -fomit-frame-pointer -std=gnu89      -D_DEFAULT_SOURCE -D_XOPEN_SOURCE=600 -c -o scripts/kconfig/bridge.o scripts/kconfig/bridge.c
gcc  -g -fsanitize=address   -o scripts/kconfig/bridge scripts/kconfig/bridge.o scripts/kconfig/confdata.o scripts/kconfig/expr.o scripts/kconfig/lexer.lex.o scripts/kconfig/menu.o scripts/kconfig/parser.tab.o scripts/kconfig/preprocess.o scripts/kconfig/symbol.o scripts/kconfig/util.o   -lncursesw -lmenuw -lpanelw

