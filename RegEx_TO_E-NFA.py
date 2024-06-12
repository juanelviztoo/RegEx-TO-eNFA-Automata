from graphviz import Digraph

# Menentukan jenis dari setiap node Expression Tree dalam RegEx
class Type:
    SYMBOL = 1
    CONCAT = 2
    UNION  = 3
    KLEENE = 4

# Merepresentasikan setiap node dalam Expression Tree dari RegEx
class ExpressionTree:
    def __init__(self, _type, value=None):
        self._type = _type
        self.value = value
        self.left = None
        self.right = None
    

# Fungsi ini mengonstruksi Expression Tree dari RegEx yang diberikan
def constructTree(regexp):
    stack = []
    # Setiap karakter atau operator diinterpretasikan dan dijadikan node dalam pohon
    for c in regexp:
        if c.isalnum():
            stack.append(ExpressionTree(Type.SYMBOL, c))
        else:
            if c == "+":
                z = ExpressionTree(Type.UNION)
                z.right = stack.pop()
                z.left = stack.pop()
            elif c == ".":
                z = ExpressionTree(Type.CONCAT)
                z.right = stack.pop()
                z.left = stack.pop()
            elif c == "*":
                z = ExpressionTree(Type.KLEENE)
                z.left = stack.pop()
            stack.append(z)

    return stack[0]

# Fungsi ini melakukan penelusuran inorder pada Expression Tree dan mencetak ekspresi dalam bentuk infix
def inorder(et):
    if et._type == Type.SYMBOL:
        print(et.value)
    elif et._type == Type.CONCAT:
        inorder(et.left)
        print(".")
        inorder(et.right)
    elif et._type == Type.UNION:
        inorder(et.left)
        print("+")
        inorder(et.right)
    elif et._type == Type.KLEENE:
        inorder(et.left)
        print("*")

# Fungsi untuk membandingkan precedensi dari dua operator
def higherPrecedence(a, b):
    p = ["+", ".", "*"]
    return p.index(a) > p.index(b)

# Fungsi ini mengonversi RegEx menjadi bentuk postfix (postfix notation) dengan menggunakan algoritma shunting-yard
def postfix(regexp):
    # adding dot "." between consecutive symbols
    temp = []
    for i in range(len(regexp)):
        if i != 0\
            and (regexp[i-1].isalnum() or regexp[i-1] == ")" or regexp[i-1] == "*")\
            and (regexp[i].isalnum() or regexp[i] == "("):
            temp.append(".")
        temp.append(regexp[i])
    regexp = temp
    
    stack = []
    output = ""

    for c in regexp:
        if c.isalnum(): # Memeriksa apakah alphanumeric (letter or number)
            output = output + c
            continue

        if c == ")":
            while len(stack) != 0 and stack[-1] != "(":
                output = output + stack.pop()
            stack.pop()
        elif c == "(":
            stack.append(c)
        elif c == "*":
            output = output + c
        elif len(stack) == 0 or stack[-1] == "(" or higherPrecedence(c, stack[-1]):
            stack.append(c)
        else:
            while len(stack) != 0 and stack[-1] != "(" and not higherPrecedence(c, stack[-1]):
                output = output + stack.pop()
            stack.append(c)

    while len(stack) != 0:
        output = output + stack.pop()

    return output

# Merepresentasikan state dalam ε-NFA
class FiniteAutomataState:
    def __init__(self):
        self.next_state = {} # Setiap state memiliki daftar next_state yang merupakan transition function

# Fungsi ini menghasilkan ε-NFA yang setara dari Expression Tree yang diberikan
def evalRegex(et):
    # Setiap fungsi ini mengevaluasi bagian-bagian dari RegEx dan menghasilkan ε-NFA yang sesuai
    if et._type == Type.SYMBOL:
        return evalRegexSymbol(et)
    elif et._type == Type.CONCAT:
        return evalRegexConcat(et)
    elif et._type == Type.UNION:
        return evalRegexUnion(et)
    elif et._type == Type.KLEENE:
        return evalRegexKleene(et)

def evalRegexSymbol(et):
    start_state = FiniteAutomataState()
    end_state   = FiniteAutomataState()
    
    start_state.next_state[et.value] = [end_state]
    return start_state, end_state

def evalRegexConcat(et):
    left_nfa  = evalRegex(et.left)
    right_nfa = evalRegex(et.right)

    left_nfa[1].next_state['ε'] = [right_nfa[0]]
    return left_nfa[0], right_nfa[1]

def evalRegexUnion(et):
    start_state = FiniteAutomataState()
    end_state   = FiniteAutomataState()

    up_nfa   = evalRegex(et.left)
    down_nfa = evalRegex(et.right)

    start_state.next_state['ε'] = [up_nfa[0], down_nfa[0]]
    up_nfa[1].next_state['ε'] = [end_state]
    down_nfa[1].next_state['ε'] = [end_state]

    return start_state, end_state

def evalRegexKleene(et):
    start_state = FiniteAutomataState()
    end_state   = FiniteAutomataState()

    sub_nfa = evalRegex(et.left)

    start_state.next_state['ε'] = [sub_nfa[0], end_state]
    sub_nfa[1].next_state['ε'] = [sub_nfa[0], end_state]

    return start_state, end_state

# Fungsi tambahan untuk membuat gambar transition menggunakan Graphviz
def visualizeTransition(finite_automata):
    dot = Digraph()
    states_done = []
    symbol_table = {finite_automata[0]: 'q0'}  # Menyimpan mapping antara state dengan label 'q' + nomor state
    dot.attr(rankdir='LR')  # Menyetel tata letak mendatar (left to right)
    dot.node('q0', shape='circle')  # Menandai start state sebagai circle biasa
    stack = [finite_automata[0]]

    while stack:
        state = stack.pop()
        if state not in states_done:
            states_done.append(state)
            for symbol in list(state.next_state):
                for ns in state.next_state[symbol]:
                    if ns not in symbol_table:
                        symbol_table[ns] = 'q' + str(len(symbol_table))
                    dot.node(symbol_table[ns], shape='doublecircle' if ns == finite_automata[1] else 'circle')
                    dot.edge(symbol_table[state], symbol_table[ns], label=symbol)
                    if ns not in states_done:
                        stack.append(ns)

    dot.render('E-NFA_transition_graph', format='png', cleanup=True)
    print("\n<!--Stored Successfully--!>")
    print("Transition Graph is Saved as E-NFA_transition_graph.png")

# Fungsi untuk membantu mencetak transition table dari state
def printStateTransitions(state, states_done, symbol_table):
    if state in states_done:
        return

    states_done.append(state)

    for symbol in list(state.next_state):
        line_output = "q" + str(symbol_table[state]) + "\t\t" + symbol + "\t\t"
        for ns in state.next_state[symbol]:
            if ns not in symbol_table:
                symbol_table[ns] = 1 + sorted(symbol_table.values())[-1]
            line_output = line_output + "q" + str(symbol_table[ns]) + " "

        print(line_output)

        for ns in state.next_state[symbol]:
            printStateTransitions(ns, states_done, symbol_table)

def printTransitionTable(finite_automata):
    print("|State|\t\t|Symbol|\t|Next State|")
    print("-------\t\t--------\t------------")
    printStateTransitions(finite_automata[0], [], {finite_automata[0]:0})

# Memvalidasi input regex dari pengguna
def validateRegexInput(regex):
    allowed_characters = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+.*()')
    # Mengecek apakah input regex sudah terisi dan tidak dalam kondisi kosong
    if not regex:
        print("<!--ERROR OCCURRED--!>\nInput Is Empty. Please Enter a Valid Regular Expression.")
        return False
    # Mengecek apakah regex hanya terdiri dari karakter alfanumerik atau karakter khusus (+, *, (), .)
    if not set(regex).issubset(allowed_characters):
        print("<!--ERROR OCCURRED--!>\nInput Contains Invalid Characters. Please Only Use Alphanumeric Characters, '+', '.', '*', '(', and ')'.")
        return False
    # Mengecek apakah simbol "(" dan ")" berpasangan
    if regex.count("(") != regex.count(")"):
        print("<!--ERROR OCCURRED--!>\nThe Open and Close Bracket Signs Aren't Paired Properly, Please Double Check Your Input.")
        return False
    return True

# Meminta pengguna untuk input regex yang valid
def promptValidRegexInput():
    while True:
        r = input("\nPlease Enter The Correct Regex: ")
        print("Processing...")
        if validateRegexInput(r):
            return r

# Program utama yang menggabungkan seluruh fungsionalitas untuk membaca input, mengonversi, mengevaluasi, dan menampilkan hasil konversi RE menjadi ε-NFA
def main():
    r = promptValidRegexInput()
    pr = postfix(r)
    et = constructTree(pr)

    #inorder(et)

    fa = evalRegex(et)
    print()
    print("\t     Transition Table")
    print("============================================")
    printTransitionTable(fa)
    print("Visualizing Transition...")
    visualizeTransition(fa)

if __name__ == "__main__":
    main()