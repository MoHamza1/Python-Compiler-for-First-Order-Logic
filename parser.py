import re
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout
import sys
import time

def log_errors(error_message):
    print(error_message)
    exit(1)

class UserDefinedSyntax:

    def __init__(self, path_to_input):

        message = ""
        with open(path_to_input, 'r') as fd:
            for line in fd:
                line = line.replace("\\", "").replace("\n", "")
                message += line
        locationsInFile = {}
        categories = ["variables", "constants", "predicates", "equality", "connectives", "quantifiers", "formula"]
        query = "(%s)" % ("|".join(categories))
        found_categories = re.finditer(query, message)
        lis = []

        for category in found_categories:
            try:
                lis.append(category.span())
            except:
                log_errors("The syntax has not been defined")

        for index, category in enumerate(lis):

            key = message[category[0]:category[1]]
            val = message[
                  category[1] + 1: (lis[index + 1][0]) if index < (len(lis) - 1) else (len(message))]
            locationsInFile[key] = val.split() if not (key == "formula") else val

            if key == "predicates":
                temp = []
                for item in locationsInFile[key]:
                    try:
                        name = re.search(r"(([0-9a-zA-Z_])+)\[", item).group(1)
                        cardinality_of_predicate = re.search(r"\[([0-9]+)\]", item).group(1)
                        if len(cardinality_of_predicate) + len(name) + 2 == len(item):
                            temp.append({"name": name, "variables": int(cardinality_of_predicate)})
                        else:
                            log_errors(f"The predicate {name}'s name or arity contains symbols that are prohibitted.")
                    except:
                        log_errors(f"The predicate {name}'s name or arity contains symbols that are prohibitted.")

                locationsInFile[key] = temp

        log_errors("The formula has not been defined in the file") if not ("formula" in locationsInFile) else None

        temp = len(locationsInFile['variables']) + len(locationsInFile['predicates']) + len(
            locationsInFile['constants'])
        log_errors("A formula is declared with no variables, predicate or constant") if len(
            locationsInFile['formula']) > 0 and temp == 0 else None

        temp = [value for value in locationsInFile['variables'] if
                value in [x['name'] for x in locationsInFile['predicates']]]
        log_errors(f"Error: duplicate Predicate(s) and Variable(s) found in the provided syntax: {temp}") if len(
            temp) else None

        temp = [value for value in locationsInFile['constants'] if
                value in [x['name'] for x in locationsInFile['predicates']]]
        log_errors(f"Error: duplicate Predicate(s) and Constant(s) found in the provided syntax: {temp}") if len(
            temp) else None

        temp = [value for value in locationsInFile['variables'] if value in locationsInFile['constants']]
        log_errors(f"Error: duplicate variable(s) and constant(s) found in the provided syntax: {temp}") if len(
            temp) else None

        self.constants = locationsInFile['constants'] if 'constants' in locationsInFile else None
        self.variables = locationsInFile['variables'] if 'variables' in locationsInFile else None
        self.predicates = locationsInFile['predicates'] if 'predicates' in locationsInFile else None
        self.quantifiers = locationsInFile['quantifiers'] if 'quantifiers' in locationsInFile else None
        self.equality = locationsInFile['equality'][0] if 'equality' in locationsInFile else None
        self.connectives = locationsInFile['connectives'] if 'connectives' in locationsInFile else None
        self.negation = self.connectives.pop() if len(self.connectives) == 5 else log_errors("You have not defined the connectives in this language propperly")
        self.formula = re.sub(r'\s+', '', locationsInFile['formula']) if 'formula' in locationsInFile else log_errors("Error: You have given a formula to parse")
        self.terms = '|'.join(self.constants + self.variables)


class formula:

    def __init__(self, inputFormula):

        # case 1: ¬formula
        # case 2: primative_formula
        # case 3: quantifier variable formula
        # case 4: Term
        # case 5: formula connective formula


        if re.search(r"^(%s)" % syntax.negation, inputFormula) and not (
                self.case5(inputFormula)):
            # case 1: ¬formula
            # lets find the formula this is negating

            query = (r"(^%s)(" % syntax.negation) + "|".join(syntax.quantifiers) + syntax.terms + "|" + "|".join(
                x["name"] for x in syntax.predicates) + ")"
            formulaBeingNegated = ""
            if (re.search(query, inputFormula)):
                # This is the case the syntax.negation is happening to predicate, var, const or quantifier
                res = re.search(query, inputFormula)
                if inputFormula[len(syntax.negation):res.span()[1]] in [x["name"] for x in syntax.predicates]:
                    stack = []
                    end = len(inputFormula)
                    target = inputFormula[len(syntax.negation):len(inputFormula)]

                    for loop in range(len(target)):
                        c = inputFormula[loop]
                        if c == '(':
                            stack.append(loop)
                        elif c == ')':
                            stack.pop()
                            if len(stack) == 0:
                                end = loop
                                break

                    formulaBeingNegated = target[0:end - 2]



            elif re.search(r"^(%s)\(" % syntax.negation, inputFormula):
                # This is the case its negating a formula enclosed in braces

                target = re.search(r"^(%s)\(" % syntax.negation, inputFormula).span()
                stack = []
                end = len(inputFormula)

                for loop in range(target[1] - 1, len(inputFormula)):
                    c = inputFormula[loop]
                    if c == '(':
                        stack.append(loop)
                    elif c == ')':
                        stack.pop()
                        if len(stack) == 0:
                            end = loop
                            break
                formulaBeingNegated = inputFormula[target[1]: end]


            else:
                # NEED TO FIND OUT IF \NEG\LOR is legal!
                # This would mean that its negating a connective which is not okay!
                log_errors("Error Parsing, Connectives cannot be negated.")
                exit(-1)

            formulaBeingNegated = self.strip_surrounding_braces(formulaBeingNegated)

            self.type = "Negation"
            self.value = "¬"
            self.err = f"Error: too many arguments being negated: {formulaBeingNegated}"
            self.child = formula(formulaBeingNegated)

        elif re.match(("(^%s)\((.*)\)$" % ('|'.join(x["name"] for x in syntax.predicates))), inputFormula) and not (
                self.case5(inputFormula)):
            # case 2: primative_formula

            predicate_found = False
            originalPredicate = None
            for predicate in syntax.predicates:
                if (re.match(r"(^%s)\(.*\)$" % (predicate["name"]), inputFormula)):
                    originalPredicate = predicate
                    predicate_found = True

            log_errors('Error: The predicate %s has not been declared in the syntax file.' % (
                re.match(r"(^%s)\(.*\)$" % (predicate["name"]), inputFormula))) if not predicate_found else None

            target_vars = inputFormula[len(originalPredicate["name"]) + 1:-1]

            arguments = []
            start = 0
            stack = []
            for index, char in enumerate(target_vars):
                if char == "(":
                    stack.append(index)
                elif char == ")":
                    stack.pop()
                if len(stack) == 0 and (index + 1 == len(target_vars) or target_vars[index + 1] == ","):
                    arguments.append((start, index + 1))
                    start = index + 2

            for loop in range(len(arguments)):
                arguments[loop] = target_vars[arguments[loop][0]:arguments[loop][1]]

            if not (len(arguments) == originalPredicate["variables"]):
                log_errors(
                    f"Error: Predicate:{originalPredicate['name']} expected {originalPredicate['syntax.variables']} arguments but {len(arguments)} where given")
                exit(-1)
            else:
                # here we have a list of arguments that are formulae themselves

                self.type = "Predicate_Function"
                self.value = originalPredicate['name']
                self.children = []
                self.err = f"Error: error in parsing arguments in this predicate function {inputFormula}"
                for argument in arguments:
                    temp = formula(argument)
                    log_errors(
                        f"Error: Constant {temp.value} was used in a predicate function {originalPredicate['name']} in the formula {inputFormula}") if temp.type == "Term" and temp.value in syntax.constants else None
                    self.children.append(temp)

        # elif inputFormula.startswith(tuple(syntax.quantifiers)) and not (self.case5(inputFormula)):
        elif re.match(r"^((%s)[%s])" % ("|".join(syntax.quantifiers), syntax.terms), inputFormula) and not (
        self.case5(inputFormula)):

            # case 3: quantifier variable formula
            formulaBeingQuantified = inputFormula[re.match(r"^(%s)(%s)" % ("|".join(syntax.quantifiers), syntax.terms),
                                                           inputFormula).span()[1]:]

            self.value = inputFormula.split(formulaBeingQuantified)[0]
            formulaBeingQuantified = self.strip_surrounding_braces(formulaBeingQuantified)
            self.type = "Quantified_variable"

            var = inputFormula[re.match(r"^(%s)" % ("|".join(syntax.quantifiers)), inputFormula).span()[1]:
                               re.match(r"^(%s)(%s)" % ("|".join(syntax.quantifiers), syntax.terms),
                                        inputFormula).span()[1]]
            log_errors(
                f"Error: You cannot quantify a constant{var}, it is a CONSTANT") if var in syntax.constants else None
            self.err = f'Error: quantified variable is: {var} but more than one arguments were passed {formulaBeingQuantified}'
            self.child = formula(formulaBeingQuantified)

        elif re.match(r"^(%s)$" % (syntax.terms), inputFormula):
            # case 4: Term
            self.type = "Term"
            self.value = inputFormula
            self.child = None

        else:
            self.case5(inputFormula)

    # def find_errors(self, inputFormula):

    def case5(self, inputFormula):
        # case 5: formula connective formula

        query = f"^({syntax.terms}){syntax.equality}({syntax.terms})$"

        if re.match(query, inputFormula):
            self.type = "Propositional_statement"
            self.value = syntax.equality
            self.err = f"Error: Equality Not well formed {inputFormula}"
            self.child_left = formula(inputFormula[0:inputFormula.find(syntax.equality)])
            self.child_right = formula(inputFormula[inputFormula.find(syntax.equality) + len(syntax.equality):])
            return True
        else:

            query = "(%s)" % ("|".join(syntax.connectives))

            found_connectives = re.finditer(query, inputFormula)

            for found_connective in found_connectives:

                stack = []
                for loop in range(0, found_connective.start()):
                    c = inputFormula[loop]
                    if c == '(':
                        stack.append(loop)
                    elif c == ')':
                        stack.pop()
                        if len(stack) == 0:
                            end = loop
                            break

                if len(stack) == 0:
                    self.type = "Propositional_statement"
                    self.value = inputFormula[found_connective.start():found_connective.end()]
                    self.err = f"Error: logical expression:{inputFormula} is not structured propperly"
                    self.child_left = formula(self.strip_surrounding_braces(inputFormula[0:found_connective.start()]))
                    self.child_right = formula(
                        self.strip_surrounding_braces(inputFormula[found_connective.end():len(inputFormula)]))
                    return True
        return False

    def strip_surrounding_braces(self, inp):
        if inp[0] == "(" and inp[-1] == ")":
            stack = []
            for index, char in enumerate(inp):
                if char == "(":
                    stack.append(index)
                elif char == ")":
                    stack.pop()
                    if len(stack) == 0 and index < len(inp) - 1:
                        return inp
                    elif len(stack) == 0 and index == len(inp) - 1:
                        return self.strip_surrounding_braces(inp[1:-1])
        else:
            return inp


def formula_to_grammar(grammar,syntax):



    equality_used = True if syntax.equality in grammar["used_connectives"] else False
    connectives_used = [m for m in list(dict.fromkeys(grammar["used_connectives"])) if not (m == syntax.equality)]
    predicates_used = list(dict.fromkeys(grammar["used_predicates"]))
    variables_used = [m for m in list(dict.fromkeys(grammar["used_terms"])) if m in syntax.variables]
    constants_used = [m for m in list(dict.fromkeys(grammar["used_terms"])) if m in syntax.constants]
    quantifiers_used = []
    if True in [m.startswith(syntax.quantifiers[0]) for m in grammar['used_quantifiers'] ]:
        quantifiers_used.append(syntax.quantifiers[0])
    if True in [m.startswith(syntax.quantifiers[1]) for m in grammar['used_quantifiers'] ]:
        quantifiers_used.append(syntax.quantifiers[1])

    out_file = []

    form = "formula -> (formula)"

    if equality_used:
        form += f"|Term {syntax.equality} Term "
    if len(predicates_used) > 0:
        form += "|Primative Formula|"
    if grammar["used_negation"] == True:
        form += f"|{syntax.negation} Formula"
    if len(quantifiers_used) > 0:
        form += "|Quantifier Variable Formula"
    if len(connectives_used) > 0:
        form += "|Formula Connective Formula"

    out_file.append(form[0:-1]) if form[-1] == "|" else out_file.append(form)


    if len(predicates_used) > 0:
        temp = "Primative Formula ->"
        for x in predicates_used:
            my_lis = [(x["name"],x["variables"]) for x in syntax.predicates]
            for y in my_lis:
                if y[0] == x:
                    temp += x + "("+','.join([str("term") for x in range(y[1])])  +") |"      #",".join(  " term "* y[1])

    out_file.append(temp[0:-1]) if temp[-1] == "|" else out_file.append(temp)

    temp = "Term -> "
    temp += "Variable |" if len(variables_used) > 0 else None
    temp += "Constant |" if len(constants_used) > 0 else None
    out_file.append(temp[0:-1]) if temp[-1] == "|" else out_file.append(temp)


    out_file.append (f"Variables -> {'|'.join(variables_used)}")
    out_file.append (f"Constants -> {'|'.join(constants_used)}")
    out_file.append (f"Quantifiers -> {'|'.join(quantifiers_used)}")
    out_file.append (f"Logical connectives -> {'|'.join(connectives_used)}")

    for index in range(len(out_file)):
        out_file[index] += "\n"

    out = open(f"grammar {time.asctime()}.txt", "w")
    out.writelines(out_file)
    out.close()  # to change file access modes



def formula_to_graph(the_formula, parent):
    global counter
    global grammar

    try:

        counter += 1
        G.add_node(counter)
        labels[counter] = the_formula.value
        print(the_formula.value)
        grammar["used_terms"].append(the_formula.value) if the_formula.type == "Term" else None

        merge = counter

        G.add_edge(parent, counter)


        if the_formula.type == "Negation" or the_formula.type == "Quantified_variable":
            grammar["used_negation"] = True if not (grammar["used_negation"]) and the_formula.type == "Negation" else None
            grammar["used_quantifiers"].append(the_formula.value) if the_formula.type == "Quantified_variable" else None


            formula_to_graph(the_formula.child, counter)
        elif the_formula.type == "Predicate_Function":
            grammar["used_predicates"].append(the_formula.value)

            for index, argument in enumerate(the_formula.children):
                formula_to_graph(argument, merge)

        elif the_formula.type == "Propositional_statement":
            grammar["used_connectives"].append(the_formula.value)
            formula_to_graph(the_formula.child_left, merge)

            formula_to_graph(the_formula.child_right, merge)


    except:
        try:
            log_errors(the_formula.err)
        except:
            log_errors(
                "Error: outputting parse tree image, try looking above; I will list an approximate in pre-order traversal of the parse tree")
        exit(1)

print(f"Reading input file in from {sys.argv[1]}")

old_stdout = sys.stdout
log_file = open(f"parse_log {time.asctime()}.log", "w")
sys.stdout = log_file

syntax = UserDefinedSyntax(f"{sys.argv[1]}")
test = formula(syntax.formula)

grammar = {"used_predicates":[],"used_terms":[],"used_quantifiers":[],"used_connectives":[],"used_negation":False}
counter = -1
labels = {}
G = nx.DiGraph()

formula_to_graph(test, 0)

# nx.nx_agraph.write_dot(G,'testg.dot')
plt.title(f"Parse tree for the formula: \n {syntax.formula}")
pos =graphviz_layout(G, prog='dot')
nx.draw_networkx_nodes(G,pos,node_size=500,node_color='w')
nx.draw_networkx_edges(G,pos,arrows=True)
nx.draw_networkx_labels(G,pos,labels)

plt.savefig(f'parse_tree {time.asctime()}.png')

sys.stdout = old_stdout
log_file.close()

formula_to_grammar(grammar,syntax)

print("The grammer tree has been printed successfully to a txt file in this directory.")
print("The parse tree has been printed successfully to a png file in this directory.")
print("You can also see a pre-order traversal of thr parse tree in the log file also in this directory")

