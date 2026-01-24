from ast_nodes import ASTNode, NodeType

def create_example_ast1():
    return ASTNode(
        NodeType.ASSIGN,
        left=ASTNode(NodeType.VARIABLE, value='x'),
        right=ASTNode(
            NodeType.BINOP,
            value='+',
            left=ASTNode(NodeType.NUMBER, value=5),
            right=ASTNode(NodeType.NUMBER, value=3)
        )
    )

def create_example_ast2():
    return ASTNode(
        NodeType.ASSIGN,
        left=ASTNode(NodeType.VARIABLE, value='y'),
        right=ASTNode(
            NodeType.BINOP,
            value='*',
            left=ASTNode(
                NodeType.BINOP,
                value='+',
                left=ASTNode(NodeType.NUMBER, value=10),
                right=ASTNode(NodeType.NUMBER, value=5)
            ),
            right=ASTNode(NodeType.NUMBER, value=2)
        )
    )

def create_example_ast3():
    return ASTNode(
        NodeType.ASSIGN,
        left=ASTNode(NodeType.VARIABLE, value='z'),
        right=ASTNode(
            NodeType.BINOP,
            value='+',
            left=ASTNode(NodeType.VARIABLE, value='x'),
            right=ASTNode(NodeType.VARIABLE, value='y')
        )
    )

def create_program_ast():
    return ASTNode(
        NodeType.PROGRAM,
        children=[
            create_example_ast1(),
            create_example_ast2(),
            create_example_ast3()
        ]
    )
