#include <string.h>
#include <strings.h>
#include <stdlib.h>

#include "lkc.h"
#include <ctype.h>

void expr_to_json(struct expr* value);

const char* type_to_str(enum symbol_type type) {
	switch (type) {
		case S_UNKNOWN:   return "unknown";
		case S_BOOLEAN:   return "boolean";
		case S_TRISTATE:  return "tristate";
		case S_INT:       return "int";
		case S_HEX:       return "hex";
		case S_STRING:    return "string";
	}
}

const char* prop_type_to_str(enum symbol_type type) {
	switch (type) {
		case P_UNKNOWN:  return "unknown";
		case P_PROMPT:   return "prompt";
		case P_COMMENT:  return "comment";
		case P_MENU:     return "menu";
		case P_DEFAULT:  return "default";
		case P_CHOICE:   return "choice";
		case P_SELECT:   return "select";
		case P_IMPLY:    return "imply";
		case P_RANGE:    return "range";
		case P_SYMBOL:   return "symbol";
	}
}

const char* expr_type_to_str(enum expr_type type) {
	switch (type) {
		case E_NONE:     return "none";
		case E_OR:       return "or";
		case E_AND:      return "and";
		case E_NOT:      return "not";
		case E_EQUAL:    return "equal";
		case E_UNEQUAL:  return "unequal";
		case E_LTH:      return "lth";
		case E_LEQ:      return "leq";
		case E_GTH:      return "gth";
		case E_GEQ:      return "geq";
		case E_LIST:     return "list";
		case E_SYMBOL:   return "symbol";
		case E_RANGE:    return "range";
	}
}

const char* tristate_to_str(enum tristate tri) {
	switch (tri) {
		case no:  return "no";
		case mod: return "mod";
		case yes: return "yes";
	}
}

void text_to_json(const char* text) {
	if (!text) {
		printf("null\n");
		return;
	}

	printf("\"");
	while (*text) {
		if (*text == '"') {
			printf("\\");
		}
		printf("%c", *text);
		++text;
	}
	printf("\"");
}

void value_to_json(struct symbol_value value) {
	printf("{\n");
	printf("\"val\": \"%s\",\n", "" /* TODO value.val*/);
	printf("\"tri\": \"%s\"\n", tristate_to_str(value.tri));
	printf("}\n");
}

void expr_child_to_json(const char* child, struct expr* value) {
	printf("\"%s\":", child);
	expr_to_json(value);
	printf(",");
}

#define PRINT_L expr_child_to_json("left", value->left)
#define PRINT_R expr_child_to_json("left", value->left)

void expr_to_json(struct expr* value) {
	if (!value) {
		printf("null\n");
		return;
	}
	printf("{\n");
	printf("\"type\": \"%s\",\n", expr_type_to_str(value->type));
	switch (type) {
		case E_NONE:     break;
		case E_OR:       PRINT_L; PRINT_R; break;
		case E_AND:      PRINT_L; PRINT_R; break;
		case E_NOT:      PRINT_L; break;
		case E_EQUAL:    PRINT_L; PRINT_R; break;
		case E_UNEQUAL:  PRINT_L; PRINT_R; break;
		case E_LTH:      PRINT_L; PRINT_R; break;
		case E_LEQ:      PRINT_L; PRINT_R; break;
		case E_GTH:      PRINT_L; PRINT_R; break;
		case E_GEQ:      PRINT_L; PRINT_R; break;
		case E_LIST:     /* TODO */ break;
		case E_RANGE:    /* TODO */ break;
		case E_SYMBOL:   printf("\"symbol\": \"%p\"\n", value->left.sym); break;
	}
	printf("\"dummy\": null\n");
	printf("}\n");
}

void expr_value_to_json(struct expr_value value) {
	printf("{\n");
	if (value.expr) {
		printf("\"expr\": "); expr_to_json(value.expr); printf(",\n");
	}
	printf("\"tri\": \"%s\"\n", tristate_to_str(value.tri));
	printf("}\n");
}

int main(int ac, char **av) {
	conf_parse(av[1]);
	conf_read(".config");
	struct symbol *sym, *csym;
	int i, cnt;
	printf("[\n");
	for_all_symbols(i, sym) {
		printf("{\n");
		printf("\"name\": \"%s\",\n", sym->name);
		printf("\"type\": \"%s\",\n", type_to_str(sym->type));
		printf("\"curr\": "); value_to_json(sym->curr); printf(",\n");
		printf("\"def\": {\n");
		printf("\"user\": "); value_to_json(sym->def[0]); printf(",\n");
		printf("\"auto\": "); value_to_json(sym->def[1]); printf(",\n");
		printf("\"def3\": "); value_to_json(sym->def[2]); printf(",\n");
		printf("\"def4\": "); value_to_json(sym->def[3]); printf("\n");
		printf("},\n");
		printf("\"visible\": \"%s\",\n", tristate_to_str(sym->visible));
		printf("\"flags\": \"%d\",\n", sym->flags);
		printf("\"properties\": [\n");
		struct property* p = sym->prop;
		while (p) {
			printf("{\n");
			printf("\"type\": \"%s\",\n", prop_type_to_str(p->type));
			printf("\"text\": "); text_to_json(p->text); printf(",\n");
			printf("\"visible\": "); expr_value_to_json(p->visible); printf(",\n");
			if (p->expr) {
				printf("\"expr\": "); expr_to_json(p->expr); printf(",\n");
			}
			//if (p->menu) {
			//	printf("\"menu\": \"%s\",\n", expr_to_str(p->expr));
			//}
			if (p->file) {
				printf("\"file\": \"%s\",\n", p->file->name);
			}
			printf("\"lineno\": \"%d\"\n", p->lineno);
			printf("},\n");
			p = p->next;
		}
		printf("{\"_dummy_\": null\n}");
		printf("]\n");
		printf("},\n");
	}
	printf("{\"_dummy_\": null}\n");
	printf("]\n");
	return 0;
}
