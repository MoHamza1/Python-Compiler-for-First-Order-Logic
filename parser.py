import re


connectives = [r"\\land", r"\\lor", r"\\implies", r"\\iff"]
predicates = [{"name":"P","variables":"2"},{"name":"Q","variables":"1"}]
quantifiers= [r"\\exists", r"\\forall"]
equalities = ["="]
variables= ["w","x","y","z"]
constants= ["C","D"]
terms = '|'.join(constants + variables)



class formula:

    def find_errors(self,inputFormula):

    def case5(self,inputFormula):
        # case 5: formula connective formula

        query = f"^({terms})=({terms})$"

        if re.match(query,inputFormula):
            self.type = "Propositional_statement"
            self.value = "="
            self.child_left = formula(inputFormula[0:inputFormula.find("=")])
            self.child_right = formula(inputFormula[inputFormula.find("=")+1:])
            return True

        query = "(%s)" % ("|".join(connectives))

        found_connectives = re.finditer(query, inputFormula)
        counter = 0

        for found_connective in found_connectives:


            stack = []
            end = len(inputFormula)
            for loop in range(0, found_connective.start()):
                c = inputFormula[loop]
                end = 0
                if c == '(':
                    stack.append(loop)
                elif c == ')':
                    stack.pop()
                    if len(stack) == 0:
                        end = loop
                        break

            if len(stack) == 0:
                temp = {r"\land": "∧", r"\lor": "∨", r"\implies": "⇒", r"\iff": "⇄"}
                self.type = "Propositional_statement"
                self.value = temp[inputFormula[found_connective.start():found_connective.end()]]
                self.child_left = formula(self.strip_surrounding_braces(inputFormula[0:found_connective.start()]))
                self.child_right = formula(\
                    self.strip_surrounding_braces(inputFormula[found_connective.end():len(inputFormula)]))
                return True
            counter += 1
        return False

    def strip_surrounding_braces(self,inp):
        if inp[0] == "(" and inp[-1] == ")":
            stack = []
            for index,char in enumerate(inp):
                if char == "(":
                    stack.append(index)
                elif char == ")":
                    stack.pop()
                    if len(stack) == 0 and index < len(inp)-1:
                        return inp
                    elif len(stack) == 0 and index == len(inp)-1:
                        return self.strip_surrounding_braces(inp[1:-1])
        else:
            return inp

    def __init__(self,inputFormula):

        #lets find out which case it is:
        #case 1: ¬formula
        #case 2: primative_formula
        #case 3: quantifier variable formula
        #case 4: Term
        #case 5: formula connective formula

        ########## Some error checking #############

        if (self.find_errors(inputFormula)):

            exit(-1)

        ############################################

        if (re.search(r"^(\\neg)", inputFormula)):
            # case 1: ¬formula
            # lets find the formula this is negating

            query = r"(^\\neg)(" + r"\\exists|\\forall|" + terms + "|"+ "|".join(x["name"] for x in predicates)+ ")"

            if (re.search(query, inputFormula)):
                #This is the case the negation is happening to predicate, var, const or quantifier
                res = re.search(query, inputFormula)
                formulaBeingNegated = inputFormula[4:]


            elif re.search(r"^(\\neg)\(", inputFormula):
                #This is the case its negating a formula enclosed in braces

                target = re.search(r"^(\\neg)\(", inputFormula).span()
                stack = []
                end = len(inputFormula)

                for loop in range(target[1]-1,len(inputFormula)):
                    c = inputFormula[loop]
                    if c == '(':
                        stack.append(loop)
                    elif c == ')':
                        stack.pop()
                        if len(stack) == 0:
                            end = loop
                            break
                formulaBeingNegated = inputFormula[target[1] : end]


            else:
                # NEED TO FIND OUT IF \NEG\LOR is legal!
                #This would mean that its negating a connective which is not okay!
                print("Error Parsing, Connectives cannot be negated.")
                exit(-1)

            formulaBeingNegated = self.strip_surrounding_braces(formulaBeingNegated)

            self.type = "Negation"
            self.value = "¬"
            self.child = formula(formulaBeingNegated)


        elif re.match(("(^%s)\((.*)\)$" % ('|'.join(x["name"] for x in predicates))),inputFormula) and not(self.case5(inputFormula)):
            # case 2: primative_formula

            originalPredicate = None;
            for predicate in predicates:
                if (re.match(r"(^%s)\(.*\)$" % (predicate["name"]),inputFormula)):
                    originalPredicate = predicate

            target_vars = inputFormula[len(originalPredicate["name"])+1:-1]

            arguments = []
            start = 0
            stack = []
            for index,char in enumerate(target_vars):
                if char == "(":
                    stack.append(index)
                elif char == ")":
                    stack.pop()
                if len(stack) == 0 and (index+1 == len(target_vars) or target_vars[index+1] == ","):
                    arguments.append((start,index+1))
                    start = index + 2

            for loop in range(len(arguments)):
                arguments[loop] = target_vars[ arguments[loop][0]:arguments[loop][1]]

            if not(len(arguments) == int(originalPredicate["variables"])):
                print(f"Predicate:{originalPredicate['name']} expected {int(originalPredicate['variables'])} arguments but {len(arguments)} where given")
                exit(-1)
            else:
                #here we have a list of arguments that are formulae themselves

                self.type = "Predicate_Function"
                self.value = originalPredicate['name']
                self.children = []
                for argument in arguments:
                    self.children.append(formula(argument))



        elif  re.match(r"^((%s)[%s])" % (r'\\exists|\\forall','|'.join(variables)),inputFormula) and not(self.case5(inputFormula)) :
            # case 3: quantifier variable formula
            self.value = "∀" if re.match(r"^(\\forall)",inputFormula) else "∃"

            self.value+= inputFormula[re.match(r"^(%s)" % (r'\\exists|\\forall'),inputFormula).span()[1]:\
            re.match(r"^((%s)[%s])" % (r'\\exists|\\forall', '|'.join(variables)), inputFormula).span()[1]]

            formulaBeingQuantified = inputFormula[re.match(r"^((%s)[%s])" % (r'\\exists|\\forall', '|'.join(variables)), inputFormula).span()[1]:]
            formulaBeingQuantified = self.strip_surrounding_braces(formulaBeingQuantified)

            self.type = "Quantified_variable"
            self.child = formula(formulaBeingQuantified)


        elif re.match(r"^[%s]$"%(terms),inputFormula):
            # case 4: Term

            self.type = "Term"
            self.value = inputFormula
            self.child = None

        else:
            self.case5(inputFormula)




depth = 0

def formula_to_graph(the_formula,parent,x,y):


    global counter
    global depth
    counter += 1
    G.add_node(counter)
    labels[counter] = the_formula.value

    pos[counter] = (x,y)
    merge = counter

    # print(counter," Predecessor: ",parent," token is: ",the_formula.value)
    # print(the_formula.type,":",the_formula.value)

    G.add_edge(parent,counter)
    #adj_list[parent].append(counter)      #problem is we need to know the size from before which is tricky


    if the_formula.type == "Negation" or the_formula.type == "Quantified_variable":
        depth += 10
        formula_to_graph(the_formula.child,counter,x,y-10)
    elif the_formula.type == "Predicate_Function":
        depth += 10
        for index,argument in enumerate(the_formula.children):
            formula_to_graph(argument,merge,(x-5/depth)+index/3,y-5)
        depth -= 10
    elif the_formula.type == "Propositional_statement":
        depth += 10
        formula_to_graph(the_formula.child_left,merge,(x-10/depth),y-10)
        depth -= 10
        formula_to_graph(the_formula.child_right,merge,(x+10/depth),y-10)


adj_list = {}
inp = r"\forall x ((( \exists y ( P(x,y) \implies \neg P(x,Q(z)) ) \lor \exists z ( ( (C = z) \land Q(z) ) \land P(x,z) ) )))"
inp = re.sub(r'\s+','', inp)
test = formula(inp)
counter = -1


import networkx as nx
import matplotlib.pyplot as plt

labels = {}
G = nx.Graph()
pos = {}
list_of_node_names = []
counter = -1
formula_to_graph(test,0,0,0)


# nx.draw_networkx_nodes(G,pos,node_size=500)
# nx.draw_networkx_edges(G,pos,width=8)
# nx.draw_networkx_labels(G,pos,labels,font_size=16)
nx.draw(G, pos=pos, labels=labels,with_labels=True)
plt.axis('off')
plt.show()
