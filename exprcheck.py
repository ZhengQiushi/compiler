# exprcheck.py
'''
Project 3 : Program Checking
============================
In this project you need to perform semantic checks on your program.
There are a few different aspects of doing this.

First, you will need to define a symbol table that keeps track of
previously declared identifiers.  The symbol table will be consulted
whenever the compiler needs to lookup information about variable and
constant declarations.

Next, you will need to define objects that represent the different
builtin datatypes and record information about their capabilities.
See the file exprtype.py.

Finally, you'll need to write code that walks the AST and enforces
a set of semantic rules.  Here is a complete list of everything you'll
need to check:

1.  Names and symbols:

    All identifiers must be defined before they are used.  This includes variables,
    constants, and typenames.  For example, this kind of code generates an error:

       a = 3;              // Error. 'a' not defined.
       var a int;

    Note: typenames such as "int", "float", and "string" are built-in names that
    should be defined at the start of the program.

2.  Types of literals

    All literal symbols must be assigned a type of "int", "float", or "string".  
    For example:

       const a = 42;         // Type "int"
       const b = 4.2;        // Type "float"
       const c = "forty";    // Type "string"

    To do this assignment, check the Python type of the literal value and attach
    a type name as appropriate.

3.  Binary operator type checking

    Binary operators only operate on operands of the same type and produce a
    result of the same type.   Otherwise, you get a type error.  For example:

        var a int = 2;
        var b float = 3.14;

        var c int = a + 3;    // OK
        var d int = a + b;    // Error.  int + float
        var e int = b + 4.5;  // Error.  int = float

4.  Unary operator type checking.

    Unary operators return a result that's the same type as the operand.

5.  Supported operators

    Here are the operators supported by each type:

    int:      binary { +, -, *, /}, unary { +, -}
    float:    binary { +, -, *, /}, unary { +, -}
    string:   binary { + }, unary { }

    Attempts to use unsupported operators should result in an error. 
    For example:

        var string a = "Hello" + "World";     // OK
        var string b = "Hello" * "World";     // Error (unsupported op *)

6.  Assignment.

    The left and right hand sides of an assignment operation must be
    declared as the same type.

    Values can only be assigned to variable declarations, not
    to constants.

For walking the AST, use the NodeVisitor class defined in exprast.py.
A shell of the code is provided below.
'''

from errors import error
from exprast import *
from exprtype import IntType, FloatType, StringType, BoolType, ExprType

class SymbolTable(dict):
    '''
    Class representing a symbol table.  It should provide functionality
    for adding and looking up nodes associated with identifiers.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def add(self, name, value):
        self[name] = value
    def lookup(self, name):
        return self.get(name, None)

class CheckProgramVisitor(NodeVisitor):
    '''
    Program checking class.   This class uses the visitor pattern as described
    in exprast.py.   You need to define methods of the form visit_NodeName()
    for each kind of AST node that you want to process.

    Note: You will need to adjust the names of the AST nodes if you
    picked different names.
    '''
    def __init__(self):
        self.symtab = SymbolTable()
        self.symtab.update({
            "int": IntType,
            "float": FloatType,
            "string": StringType,
            "bool": BoolType
        })
        self.typemap = {
            int: IntType, 
            float: FloatType, 
            str: StringType,
            bool: BoolType
        }

    def check_type_unary(self, node, op, val):
        if hasattr(val, "check_type"):
            if op not in val.check_type.unary_ops:
                error(node.lineno, "Unary operator {} not supported".format(op))
            return val.check_type

    def check_type_binary(self, node, op, left, right):
        if hasattr(left, "check_type") and hasattr(right, "check_type"):
            if left.check_type != right.check_type:
                error(node.lineno, "Binary operator {} does not have matching LHS/RHS types".format(op))
                return left.check_type
            errside = None
            if op not in left.check_type.binary_ops:
                errside = "LHS"
            if op not in right.check_type.binary_ops:
                errside = "RHS"
            if errside is not None:
                error(node.lineno, "Binary operator {} not supported on {} of expression".format(op, errside))
            # XXX: right now we just propagate the left type, but we should probably handle error conditions
            return left.check_type

    def check_type_rel(self, node, op, left, right):
        if hasattr(left, "check_type") and hasattr(right, "check_type"):
            if left.check_type != right.check_type:
                error(node.lineno, "Relational operator {} does not have matching LHS/RHS types".format(op))
                return left.check_type
            errside = None
            if op not in left.check_type.rel_ops:
                errside = "LHS"
            if op not in right.check_type.rel_ops:
                errside = "RHS"
            if errside is not None:
                error(node.lineno, "Relational operator {} not supported on {} of expression".format(op, errside))
            # XXX: right now we just propagate the left type, but we should probably handle error conditions
            return BoolType

    def visit_Program(self,node):
        node.symtab = self.symtab
        # 1. Visit all of the statements
        for statement in node.statements.statements:
            self.visit(statement)
            # 2. Record the associated symbol table
            if isinstance(statement, AssignmentStatement):
                self.symtab.add(statement.location.name, statement.expr)

    def visit_Unaryop(self,node):
        self.visit(node.expr)
        # 1. Make sure that the operation is supported by the type
        check_type = self.check_type_unary(node, node.op, node.expr)
        # 2. Set the result type to the same as the operand
        node.check_type = check_type


    def visit_Binop(self,node):
        # 1. Make sure left and right operands have the same type
        # 2. Make sure the operation is supported
        # AM note: both are done in check_type_binary
        self.visit(node.left)
        self.visit(node.right)
        check_type = self.check_type_binary(node, node.op, node.left, node.right)
        # 3. Assign the result type
        node.check_type = check_type

    def visit_Relop(self,node):
        # 1. Make sure left and right operands have the same type
        # 2. Make sure the operation is supported
        # AM note: both are done in check_type_binary
        self.visit(node.left)
        self.visit(node.right)
        check_type = self.check_type_rel(node, node.op, node.left, node.right)
        # 3. Assign the result type
        node.check_type = check_type

    def visit_AssignmentStatement(self,node):
        # 1. Make sure the location of the assignment is defined
        sym = self.symtab.lookup(node.location.name)
        if not sym:
            error(node.lineno, "name '{}' not defined".format(node.location.name))
        # 2. Check that assignment is allowed
        self.visit(node.expr)
        if isinstance(sym, VarDeclaration):
            # empty var declaration, so check against the declared type name
            if hasattr(sym, "check_type") and hasattr(node.expr, "check_type"):
                declared_type = sym.check_type
                value_type = node.expr.check_type
                if declared_type != value_type:
                    error(node.lineno, "Cannot assign {} to {}".format(value_type, declared_type))
                    return
        if isinstance(sym, ConstDeclaration):
            error(node.lineno, "Cannot assign to constant {}".format(sym.name))
            return
        # 3. Check that the types match
        if hasattr(node.location, "check_type") and hasattr(node.expr, "check_type"):
            declared_type = node.location.check_type
            value_type = node.expr.check_type
            if declared_type != value_type:
                error(node.lineno, "Cannot assign {} to {}".format(value_type, declared_type))

    def visit_ConstDeclaration(self,node):
        # 1. Check that the constant name is not already defined
        if self.symtab.lookup(node.name) is not None:
            error(node.lineno, "Attempted to redefine const '{}', not allowed".format(node.name))
        # 2. Add an entry to the symbol table
        self.symtab.add(node.name, node)
        self.visit(node.expr)
        node.check_type = node.expr.check_type

    def visit_VarDeclaration(self,node):
        # 1. Check that the variable name is not already defined
        if self.symtab.lookup(node.name) is not None:
            error(node.lineno, "Attempted to redefine var '{}', not allowed".format(node.name))
            return
        # 2. Add an entry to the symbol table
        self.symtab.add(node.name, node)
        # 3. Check that the type of the expression (if any) is the same
        self.visit(node.typename)
        # propagate check_type from Typename up to Var declaration
        if hasattr(node.typename, "check_type"):
            node.check_type = node.typename.check_type
        # 4. If there is no expression, set an initial value for the value
        self.visit(node.expr)
        if node.expr is None:
            default = node.check_type.default
            node.expr = Literal(default)
            node.expr.check_type = node.check_type

    def visit_Typename(self,node):
        # 1. Make sure the typename is valid and that it's actually a type
        sym = self.symtab.lookup(node.name)
        if not isinstance(sym, ExprType):
            error(node.lineno, "{} is not a valid type".format(node.name))
            return
        node.check_type = sym

    def visit_Location(self,node):
        # 1. Make sure the location is a valid variable or constant value
        sym = self.symtab.lookup(node.name)
        if not sym:
            error(node.lineno, "name '{}' not found".format(node.name))
        # 2. Assign the type of the location to the node
        node.check_type = sym.check_type

    def visit_LoadLocation(self, node):
        # 1. Make sure the loaded location is valid.
        sym = self.symtab.lookup(node.location.name)
        if not sym:
            error(node.lineno, "name '{}' not found".format(node.location.name))
            return
        # 2. Assign the appropriate type
        if isinstance(sym, ExprType):
            error(node.lineno, "cannot use {} outside of variable declarations".format(sym.typename))
            return
        check_type = sym.check_type
        if check_type is None:
            error(node.lineno, "Using unrecognized type {}".format(valtype))
        node.check_type = check_type

    def visit_Literal(self,node):
        # Attach an appropriate type to the literal
        valtype = type(node.value)
        check_type = self.typemap.get(valtype, None)
        if check_type is None:
            error(node.lineno, "Using unrecognized type {}".format(valtype))
        node.check_type = check_type
        
# ----------------------------------------------------------------------
#                       DO NOT MODIFY ANYTHING BELOW       
# ----------------------------------------------------------------------

def check_program(node):
    '''
    Check the supplied program (in the form of an AST)
    '''
    checker = CheckProgramVisitor()
    checker.visit(node)

if __name__ == '__main__':
    import exprlex
    import exprparse
    import sys
    from errors import subscribe_errors
    lexer = exprlex.make_lexer()
    parser = exprparse.make_parser()
    with subscribe_errors(lambda msg: sys.stdout.write(msg+"\n")):
        program = parser.parse(open(sys.argv[1]).read())
        # Check the program
        check_program(program)
            
