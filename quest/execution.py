"""Python subset used by the course; shared by validation and the child runner."""
import ast
import builtins


BUILTINS = {name: getattr(builtins, name) for name in (
    'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'float', 'input', 'int',
    'len', 'list', 'map', 'max', 'min', 'print', 'range', 'reversed', 'round',
    'set', 'sorted', 'str', 'sum', 'tuple', 'zip')}
METHODS = {'append', 'clear', 'copy', 'count', 'endswith', 'extend', 'find', 'get',
           'index', 'insert', 'isdigit', 'items', 'join', 'keys', 'lower', 'pop',
           'remove', 'replace', 'reverse', 'sort', 'split', 'startswith', 'strip',
           'update', 'upper', 'values'}
FORBIDDEN_NAMES = set(vars(builtins)) - BUILTINS.keys()
NODES = {getattr(ast, name) for name in (
    'Module', 'Expr', 'Assign', 'AugAssign', 'Name', 'Load', 'Store', 'Constant',
    'List', 'Tuple', 'Dict', 'Set', 'Subscript', 'Slice', 'BinOp', 'UnaryOp',
    'BoolOp', 'Compare', 'Add', 'Sub', 'Mult', 'Div', 'FloorDiv', 'Mod', 'Pow',
    'UAdd', 'USub', 'Not', 'And', 'Or', 'Eq', 'NotEq', 'Lt', 'LtE', 'Gt', 'GtE',
    'In', 'NotIn', 'Is', 'IsNot', 'If', 'IfExp', 'For', 'While', 'Break',
    'Continue', 'Pass', 'FunctionDef', 'arguments', 'arg', 'Return', 'Call',
    'keyword', 'Attribute', 'JoinedStr', 'FormattedValue', 'ListComp',
    'DictComp', 'SetComp', 'GeneratorExp', 'comprehension')}


def validate_source(source):
    if not isinstance(source, str) or len(source) > 20_000:
        raise ValueError('El programa debe tener como máximo 20 000 caracteres.')
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if type(node) not in NODES:
            raise ValueError('Usa las herramientas del curso: no se permiten importaciones ni acceso al sistema.')
        name = (node.id if isinstance(node, ast.Name) else
                node.name if isinstance(node, ast.FunctionDef) else
                node.arg if isinstance(node, ast.arg) else '')
        if name.startswith('__') or name in FORBIDDEN_NAMES:
            raise ValueError(f'No se permite utilizar {name}.')
        if isinstance(node, ast.Attribute) and node.attr not in METHODS:
            raise ValueError(f'No se permite acceder al atributo {node.attr}.')
        if isinstance(node, ast.Call) and not isinstance(node.func, (ast.Name, ast.Attribute)):
            raise ValueError('No se permiten llamadas indirectas mediante índices u otras expresiones.')
        if isinstance(node, ast.FunctionDef) and (node.decorator_list or node.returns):
            raise ValueError('Las funciones del curso no utilizan decoradores ni anotaciones.')
        if isinstance(node, ast.arg) and node.annotation:
            raise ValueError('Las funciones del curso no utilizan anotaciones.')
    return tree


if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8', newline='\n')
    sys.stderr.reconfigure(encoding='utf-8', newline='\n')
    source = Path(sys.argv[1]).read_text(encoding='utf-8')
    tree = validate_source(source)
    scope = {'__builtins__': BUILTINS}
    exec(compile(tree, 'solucion.py', 'exec'), scope, scope)
