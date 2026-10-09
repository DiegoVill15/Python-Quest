"""Temario y ejemplos ejecutables: una sola fuente por etapa."""

import ast

WORLDS = [
    {'id': 'fundamentos', 'name': 'Aldea Inicial', 'topic': 'entrada, tipos, operaciones y funciones básicas', 'icon': '✦', 'color': '#7dd3fc'},
    {'id': 'condicionales', 'name': 'Bosque de Decisiones', 'topic': 'if, elif, else y comparaciones', 'icon': '◆', 'color': '#a7f3d0'},
    {'id': 'bucles', 'name': 'Montañas del Bucle', 'topic': 'for, while y range', 'icon': '↻', 'color': '#fcd34d'},
    {'id': 'listas', 'name': 'Archipiélago de Datos', 'topic': 'cadenas y listas de Python', 'icon': '▦', 'color': '#c4b5fd'},
    {'id': 'funciones', 'name': 'Torre de Funciones', 'topic': 'def, parámetros y retorno', 'icon': 'λ', 'color': '#fda4af'},
    {'id': 'diccionarios', 'name': 'Biblioteca de Claves', 'topic': 'diccionarios y operaciones básicas', 'icon': '⌘', 'color': '#fdba74'},
]
WORLDS.extend([{'id': 'taller',
  'name': 'Taller de Alquimia',
  'topic': 'herramientas numéricas y limpieza de cadenas',
  'icon': '⚗',
  'color': '#67e8f9'},
 {'id': 'rutas',
  'name': 'Laberinto de Rutas',
  'topic': 'búsquedas, control de bucles, orden y recorridos anidados',
  'icon': '⌁',
  'color': '#bef264'},
 {'id': 'proyecto',
  'name': 'Ciudadela del Aventurero',
  'topic': 'proyecto integrador: gestionar una expedición',
  'icon': '♜',
  'color': '#f9a8d4'}])
WORLD_BY_ID = {world["id"]: world for world in WORLDS}
STAGES_PER_WORLD = 5

CURRICULUM = {
    'fundamentos': [
        {
            'focus': 'input, int y print',
            'objectives': ['Leer un entero, realizar una operación aritmética directa y mostrar un resultado.'],
            'introduced': ['input', 'print', 'int', 'add', 'subtract', 'multiply'],
            'required': [],
            'review': [],
            'input_spec': {'lines': 1, 'value_type': 'integer'},
            'edge_cases': ['cero', 'negativo'],
            'common_mistakes': ['operar sobre texto sin convertir'],
            'forbidden': [],
            "lesson": {
                'title': 'Leer un número y mostrar un resultado',
                'explanation': 'input() lee una línea y siempre entrega texto. int(...) lo convierte en entero y print(...) muestra un resultado. Los operadores +, - y * suman, restan y multiplican. Escribe cada valor en una línea; con la entrada 4, sumar 1 produce 5.',
                'code': 'numero = int(input())\nprint(numero + 1)',
                'output': '5',
                'input': '4\n',
            },
        },
        {
            'focus': 'variables, texto, suma y resta',
            'objectives': ['Leer texto y un entero en líneas separadas; usar len y calcular resultados relacionados con suma o resta.'],
            'introduced': ['str', 'len'],
            'required': [],
            'review': ['fundamentos:1'],
            'input_spec': {'lines': 2, 'value_types': ['text', 'integer']},
            'edge_cases': ['texto con espacios'],
            'common_mistakes': ['mezclar str e int'],
            'forbidden': [],
            "lesson": {
                'title': 'Variables, texto, suma y resta',
                'explanation': 'Cada input() lee la siguiente línea. Guarda el nombre como texto y convierte los puntos con int. str(...) convierte un número en texto y len(...) cuenta caracteres. + suma números y - los resta. Unir texto con un entero sin convertirlo provoca TypeError.',
                'code': 'nombre = input()\npuntos = int(input())\nprint(nombre, len(nombre))\nprint(str(puntos) + " puntos")\nprint(puntos + 2, puntos - 2)',
                'output': 'Lía 3\n8 puntos\n10 6',
                'input': 'Lía\n8\n',
            },
        },
        {
            'focus': 'float y decimales',
            'objectives': ['Leer al menos tres entradas, convertir una con float y mostrar dos resultados relacionados con formato decimal.'],
            'introduced': ['float', 'divide', 'fstring'],
            'required': [],
            'review': ['fundamentos:2'],
            'input_spec': {'lines': 3, 'value_types': ['decimal', 'integer', 'decimal']},
            'edge_cases': ['resultado fraccionario'],
            'common_mistakes': ['omitir f o el formato decimal'],
            'forbidden': [],
            "lesson": {
                'title': 'Decimales con float',
                'explanation': 'float(input()) lee un decimal. Una f-string empieza con f antes de las comillas: lo que va entre { } se sustituye por su valor. Dentro de las llaves, :.2f muestra dos cifras decimales. El total es precio por cantidad menos descuento; la mitad es total / 2.',
                'code': 'precio = float(input())\ncantidad = int(input())\ndescuento = float(input())\ntotal = precio * cantidad - descuento\nprint(f"{total:.2f}")\nprint(f"{total / 2:.2f}")',
                'output': '9.00\n4.50',
                'input': '5\n2\n1\n',
            },
        },
        {
            'focus': 'división entera y resto',
            'objectives': ['Leer al menos tres entradas; encadenar cálculos y aplicar división entera y resto (// y %).'],
            'introduced': ['floor_divide', 'modulo'],
            'required': ['floor_divide', 'modulo'],
            'review': ['fundamentos:1'],
            'input_spec': {'lines': 3, 'divisor': 'nonzero'},
            'edge_cases': ['división exacta', 'resto distinto de cero'],
            'common_mistakes': ['confundir cociente con resto'],
            'forbidden': [],
            "lesson": {
                'title': 'Tres formas de dividir',
                'explanation': 'Lee cantidad, extra y tamaño de grupo en tres líneas. El total es cantidad + extra. / da un cociente decimal, // el cociente entero y % el resto. El tamaño del grupo debe ser mayor que cero; aprenderás a comprobarlo con if.',
                'code': 'cantidad = int(input())\nextra = int(input())\ngrupo = int(input())\ntotal = cantidad + extra\nprint(total / grupo)\nprint(total // grupo)\nprint(total % grupo)',
                'output': '3.5\n3\n1',
                'input': '6\n1\n2\n',
            },
        },
        {
            'focus': 'listas sencillas, split, sum y len',
            'objectives': ['Leer al menos cuatro líneas; contar palabras con split y len, y sumar y contar números de una lista literal.', 'Mostrar tres resultados relacionados, incluido un promedio con formato decimal.'],
            'introduced': ['list_literal', 'split', 'sum'],
            'required': ['sum', 'len'],
            'review': ['fundamentos:3'],
            'input_spec': {'lines': 4, 'numeric_count': 'positive'},
            'edge_cases': ['palabras con varios espacios'],
            'common_mistakes': ['sumar textos en lugar de números'],
            'forbidden': [],
            "lesson": {
                'title': 'Sumar y contar valores',
                'explanation': 'input().split() separa las palabras de una línea por espacios y las guarda en una lista de textos. Una lista literal, como [primero, segundo, tercero], agrupa los números ya convertidos. len cuenta elementos y sum suma números. Para el promedio divide el total numérico entre su cantidad, que aquí siempre es tres.',
                'code': 'palabras = input().split()\nprimero = int(input())\nsegundo = int(input())\ntercero = int(input())\nvalores = [primero, segundo, tercero]\nprint(len(palabras))\nprint(sum(valores), len(valores))\nprint(f"{sum(valores) / len(valores):.2f}")',
                'output': '3\n18 3\n6.00',
                'input': 'luz del faro\n4\n6\n8\n',
            },
        },
    ],
    'condicionales': [
        {
            'focus': 'comparaciones e if',
            'objectives': ['Mostrar una comparación y usar if para una acción adicional cuando se cumple; no usar else todavía.'],
            'introduced': ['comparison', 'if'],
            'required': ['if'],
            'review': ['fundamentos:1'],
            'input_spec': {'lines': 1},
            'edge_cases': ['condición verdadera', 'condición falsa'],
            'common_mistakes': ['confundir = con ==', 'sangría incorrecta'],
            'forbidden': [],
            "lesson": {
                'title': 'Comparar dos valores',
                'explanation': 'Una comparación produce True o False. == comprueba igualdad y = guarda un valor. if ejecuta su bloque solo cuando la condición es verdadera; si es falsa lo omite. Las líneas de ese bloque deben llevar la misma sangría: una sangría incorrecta puede provocar IndentationError.',
                'code': 'puntos = int(input())\nprint(puntos >= 5)\nif puntos >= 5:\n    print("Suficientes")',
                'output': 'True\nSuficientes',
                'input': '8\n',
                'cases': [{'input': '2\n', 'output': 'False'}],
            },
        },
        {
            'focus': 'if y else',
            'objectives': ['Leer dos números y elegir con if/else entre divisor cero y una división válida.', 'Reutilizar el formato decimal de fundamentos:3.'],
            'introduced': ['else'],
            'required': ['if', 'else'],
            'review': ['fundamentos:3'],
            'input_spec': {'lines': 2, 'divisor': 'may_be_zero'},
            'edge_cases': ['divisor cero', 'divisor distinto de cero'],
            'common_mistakes': ['dividir antes de comprobar cero'],
            'forbidden': [],
            "lesson": {
                'title': 'Dos caminos y divisor cero',
                'explanation': 'Lee total y partes en dos líneas. if/else elige uno de dos caminos. Antes de dividir comprueba si partes es cero: dividir entre cero provoca ZeroDivisionError. La f-string muestra el cociente con dos decimales.',
                'code': 'total = int(input())\npartes = int(input())\nif partes == 0:\n    print("No se puede dividir")\nelse:\n    print(f"{total / partes:.2f}")',
                'output': 'No se puede dividir',
                'input': '8\n0\n',
                'cases': [{'input': '8\n2\n', 'output': '4.00'}],
            },
        },
        {
            'focus': 'elif y varios casos',
            'objectives': ['Elegir entre tres o más resultados con elif y límites explícitos.'],
            'introduced': ['elif'],
            'required': ['elif'],
            'review': ['fundamentos:1'],
            'input_spec': {'lines': 1},
            'edge_cases': ['valor en cada límite'],
            'common_mistakes': ['dejar un límite sin cubrir'],
            'forbidden': [],
            "lesson": {
                'title': 'Tres o más casos con elif',
                'explanation': 'elif prueba otra condición solo si las anteriores fallaron. Prueba los valores justo en cada límite para evitar huecos. Cada input() puede alimentar la comparación sin cambiar la estructura de las ramas.',
                'code': 'edad = int(input())\nif edad < 12:\n    print("Infancia")\nelif edad < 18:\n    print("Adolescencia")\nelse:\n    print("Adultez")',
                'output': 'Adolescencia',
                'input': '12\n',
                'cases': [{'input': '18\n', 'output': 'Adultez'}],
            },
        },
        {
            'focus': 'operadores lógicos',
            'objectives': ['Combinar and y or en una decisión donde ambos sean necesarios.'],
            'introduced': ['and', 'or'],
            'required': ['if', 'and', 'or'],
            'review': ['condicionales:1'],
            'input_spec': {'lines': 2},
            'edge_cases': ['condiciones solapadas'],
            'common_mistakes': ['confundir and y or'],
            'forbidden': [],
            "lesson": {
                'title': 'Combinar condiciones',
                'explanation': 'and exige que ambas condiciones se cumplan y or acepta cualquiera. Lee la edad y luego 1 si hay pase o 0 si no. Los paréntesis agrupan las condiciones: se permite entrar a un adulto con pase o a alguien menor de tres años.',
                'code': 'edad = int(input())\ntiene_pase = int(input()) == 1\nif (edad >= 18 and tiene_pase) or edad < 3:\n    print("Entra")\nelse:\n    print("Espera")',
                'output': 'Espera',
                'input': '16\n1\n',
                'cases': [{'input': '2\n0\n', 'output': 'Entra'}],
            },
        },
        {
            'focus': 'casos límite con decisiones',
            'objectives': ['Resolver prioridades y límites con al menos cuatro resultados posibles.', 'Reutilizar conversiones y comparaciones de las etapas anteriores.'],
            'introduced': [],
            'required': ['elif'],
            'review': ['fundamentos:2'],
            'input_spec': {'lines': 2},
            'edge_cases': ['excepciones con prioridad'],
            'common_mistakes': ['poner una regla general antes de una excepción'],
            'forbidden': [],
            "lesson": {
                'title': 'Prioridad entre reglas',
                'explanation': 'En una cadena if/elif gana la primera condición verdadera. Primero se detecta saldo negativo, después saldo cero, luego atención VIP y finalmente atención normal. Lee el saldo y la marca VIP (1 o 0) en líneas separadas.',
                'code': 'saldo = int(input())\nes_vip = int(input()) == 1\nif saldo < 0:\n    print("Saldo inválido")\nelif saldo == 0:\n    print("Sin saldo")\nelif es_vip:\n    print("Atención especial")\nelse:\n    print("Atención normal")',
                'output': 'Sin saldo',
                'input': '0\n1\n',
            },
        },
    ],
    'bucles': [
        {
            'focus': 'for y range',
            'objectives': ['Leer una cantidad y repetir un cálculo con for y range.'],
            'introduced': ['for', 'range'],
            'required': ['for'],
            'review': ['fundamentos:1'],
            'input_spec': {'lines': 1, 'count': 'nonnegative'},
            'edge_cases': ['cantidad cero'],
            'common_mistakes': ['confundir el límite exclusivo de range'],
            'forbidden': [],
            "lesson": {
                'title': 'Repetir con for y range',
                'explanation': 'Lee cuántos pasos repetir. for recorre los números de range: range(1, pasos + 1) incluye pasos porque se detiene antes del segundo límite. Las líneas repetidas llevan sangría.',
                'code': 'pasos = int(input())\nfor paso in range(1, pasos + 1):\n    print(paso)',
                'output': '1\n2\n3',
                'input': '3\n',
            },
        },
        {
            'focus': 'acumuladores',
            'objectives': ['Leer N valores en N líneas, acumularlos y contar los que cumplen una condición.'],
            'introduced': ['augassign'],
            'required': ['for'],
            'review': ['condicionales:1'],
            'input_spec': {'lines': '1+N', 'count_first': True, 'allow_zero_records': True},
            'edge_cases': ['ningún valor cumple'],
            'common_mistakes': ['reiniciar el acumulador dentro del ciclo'],
            'forbidden': [],
            "lesson": {
                'title': 'Acumular y contar mientras repites',
                'explanation': 'La primera línea indica N. for con range(N) permite leer las siguientes N líneas. Empieza los acumuladores en cero: += añade al total y un if cuenta los valores mayores que uno. No confundas N, que indica cuántas entradas leer, con el valor leído en cada vuelta.',
                'code': 'cantidad_datos = int(input())\ntotal = 0\ncantidad = 0\nfor _ in range(cantidad_datos):\n    numero = int(input())\n    total += numero\n    if numero > 1:\n        cantidad += 1\nprint(total, cantidad)',
                'output': '6 2',
                'input': '3\n1\n2\n3\n',
            },
        },
        {
            'focus': 'while',
            'objectives': ['Leer valores hasta un centinela con while, acumularlos sin incluir el centinela.'],
            'introduced': ['while'],
            'required': ['while'],
            'review': ['condicionales:1'],
            'input_spec': {'lines': 'variable', 'terminator': 0, 'value_type': 'integer'},
            'edge_cases': ['centinela en la primera línea', 'valores negativos'],
            'common_mistakes': ['sumar el centinela', 'olvidar leer el siguiente valor'],
            'forbidden': ['for'],
            "lesson": {
                'title': 'Detener un ciclo con una señal',
                'explanation': 'Lee el primer valor antes del while. Mientras no sea 0, súmalo y lee la siguiente línea. El 0 es el centinela: termina la lectura y no se suma. Si aparece primero, el total queda en cero. Olvidar leer otro valor dentro del ciclo puede hacer que nunca termine.',
                'code': 'actual = int(input())\ntotal = 0\nwhile actual != 0:\n    total += actual\n    actual = int(input())\nprint(total)',
                'output': '6',
                'input': '3\n2\n1\n0\n',
                'cases': [{'input': '0\n', 'output': '0'}, {'input': '-2\n3\n0\n', 'output': '1'}],
            },
        },
        {
            'focus': 'bucles con condiciones',
            'objectives': ['Leer dos enteros por vuelta en líneas separadas, compararlos y actualizar uno de dos totales.'],
            'introduced': [],
            'required': ['for', 'if'],
            'review': ['condicionales:2'],
            'input_spec': {'lines': '1+2*N', 'count_first': True, 'lines_per_iteration': 2},
            'edge_cases': ['igualdad entre los dos valores'],
            'common_mistakes': ['intercambiar los dos valores o totales'],
            'forbidden': [],
            "lesson": {
                'title': 'Comparar pares durante un ciclo',
                'explanation': 'La primera línea indica cuántos pares leer. En cada vuelta lee dos líneas, una para cada entero. Compara ambos: si gana el primero, añade su valor al primer total; si no, añade el segundo al otro total. Ambos acumuladores empiezan en cero.',
                'code': 'pares = int(input())\ntotal_primero = 0\ntotal_segundo = 0\nfor _ in range(pares):\n    primero = int(input())\n    segundo = int(input())\n    if primero > segundo:\n        total_primero += primero\n    else:\n        total_segundo += segundo\nprint(total_primero, total_segundo)',
                'output': '5 2',
                'input': '2\n1\n2\n5\n2\n',
            },
        },
        {
            'focus': 'síntesis de bucles',
            'objectives': ['Seleccionar valores durante un ciclo y acumular solo los seleccionados.', 'Mostrar cantidad y promedio de los seleccionados, comprobando el divisor antes de dividir.', 'Reutilizar la salida decimal de fundamentos:3.'],
            'introduced': [],
            'required': ['for', 'if'],
            'review': ['fundamentos:3', 'condicionales:2'],
            'input_spec': {'lines': '1+N', 'count_first': True, 'allow_zero_records': True},
            'edge_cases': ['N=0', 'ningún valor seleccionado', 'valores seleccionados y descartados'],
            'common_mistakes': ['sumar valores descartados al promedio', 'dividir entre cero'],
            'forbidden': [],
            "lesson": {
                'title': 'Evitar dividir entre cero al terminar',
                'explanation': 'Lee N y luego N notas, una por línea. Para el promedio de aprobados, suma solo las notas aprobadas y divide entre su cantidad. N = 0 significa que no hay registros; no significa omitir la primera línea. Si no hay aprobados, muestra Ninguno antes de intentar dividir.',
                'code': 'cantidad_notas = int(input())\ntotal_aprobados = 0\naprobados = 0\nfor _ in range(cantidad_notas):\n    nota = int(input())\n    if nota >= 6:\n        total_aprobados += nota\n        aprobados += 1\nprint(aprobados)\nif aprobados == 0:\n    print("Ninguno")\nelse:\n    print(f"{total_aprobados / aprobados:.2f}")',
                'output': '2\n7.00',
                'input': '4\n2\n6\n8\n3\n',
                'cases': [{'input': '0\n', 'output': '0\nNinguno'}, {'input': '2\n2\n3\n', 'output': '0\nNinguno'}],
            },
        },
    ],
    'listas': [
        {
            'focus': 'índices de cadenas',
            'objectives': ['Consultar índices o fragmentos de una cadena recibida por entrada.'],
            'introduced': ['index', 'slice'],
            'required': [],
            'review': ['fundamentos:2'],
            'input_spec': {'lines': 1, 'min_characters': 3},
            'edge_cases': ['cadena de longitud mínima'],
            'common_mistakes': ['confundir la primera posición con 1'],
            'forbidden': [],
            "lesson": {
                'title': 'Posiciones de una cadena',
                'explanation': 'input() entrega una cadena. Sus posiciones empiezan en 0; -1 señala el último carácter. Un fragmento [inicio:fin] se detiene antes de fin. Este ejemplo necesita al menos tres caracteres para consultar esas posiciones.',
                'code': 'palabra = input()\nprint(palabra[0])\nprint(palabra[-1])\nprint(palabra[1:3])',
                'output': 'g\no\nat',
                'input': 'gato\n',
            },
        },
        {
            'focus': 'transformación de cadenas',
            'objectives': ['Recorrer una cadena y transformarla conservando el tratamiento explícito de los espacios.'],
            'introduced': [],
            'required': [],
            'review': ['bucles:2'],
            'input_spec': {'lines': 1, 'preserve_spaces': True},
            'edge_cases': ['espacios consecutivos'],
            'common_mistakes': ['perder espacios'],
            'forbidden': [],
            "lesson": {
                'title': 'Transformar texto y conservar espacios',
                'explanation': 'Puedes recorrer una cadena carácter por carácter. Los espacios también son caracteres y input() conserva los que escribes dentro de la línea. += añade texto al resultado: aquí cada espacio se convierte en un guion.',
                'code': 'texto = input()\nresultado = ""\nfor letra in texto:\n    if letra == " ":\n        resultado += "-"\n    else:\n        resultado += letra\nprint(resultado)',
                'output': 'a-b',
                'input': 'a b\n',
                'cases': [{'input': 'a  b\n', 'output': 'a--b'}],
            },
        },
        {
            'focus': 'split y listas numéricas',
            'objectives': ['Separar una línea numérica con split y convertir sus elementos con map(int, ...) y list(...).', 'Consultar un índice y modificar un elemento.'],
            'introduced': ['map', 'list', 'subscript_write'],
            'required': [],
            'review': ['fundamentos:5'],
            'input_spec': {'lines': 1, 'min_elements': 2},
            'edge_cases': ['números negativos'],
            'common_mistakes': ['usar int sobre la lista completa'],
            'forbidden': [],
            "lesson": {
                'title': 'Separar texto y convertir una lista numérica',
                'explanation': 'input().split() separa por espacios y devuelve textos. map(int, partes) convierte cada elemento y list(...) guarda los enteros: int(lista) no convierte todos sus elementos y provoca TypeError. Después puedes consultar o cambiar posiciones. Este ejemplo necesita al menos dos números.',
                'code': 'partes = input().split()\nnumeros = list(map(int, partes))\nnumeros[0] = numeros[0] + 1\nprint(numeros[0], numeros[1])',
                'output': '5 7',
                'input': '4 7\n',
            },
        },
        {
            'focus': 'recorrido y resumen de listas',
            'objectives': ['Recorrer una lista para filtrar o transformar valores con append; resumir con sum y len.'],
            'introduced': ['append'],
            'required': [],
            'review': ['bucles:2'],
            'input_spec': {'lines': 1, 'allow_empty': True},
            'edge_cases': ['ningún valor seleccionado', 'línea vacía'],
            'common_mistakes': ['reiniciar la lista dentro del ciclo'],
            'forbidden': [],
            "lesson": {
                'title': 'Recorrer y resumir una lista',
                'explanation': 'Convierte la línea en una lista numérica y recórrela con for. append añade un número a otra lista. Aquí se guardan solo los pares; sum obtiene su total y len su cantidad. Una línea vacía produce una lista vacía.',
                'code': 'numeros = list(map(int, input().split()))\npares = []\nfor numero in numeros:\n    if numero % 2 == 0:\n        pares.append(numero)\nprint(pares)\nprint(sum(pares), len(pares))',
                'output': '[2, 4]\n6 2',
                'input': '1 2 3 4\n',
                'cases': [{'input': '\n', 'output': '[]\n0 0'}],
            },
        },
        {
            'focus': 'síntesis y listas vacías',
            'objectives': ['Combinar cadenas y listas en al menos dos pasos de transformación con una operación distinta de la misión previa.', 'Contemplar listas vacías y comprobar la cantidad antes de calcular un promedio.'],
            'introduced': [],
            'required': [],
            'review': ['condicionales:2', 'fundamentos:3'],
            'input_spec': {'lines': 'defined_by_mission', 'allow_empty': True},
            'edge_cases': ['lista vacía', 'lista no vacía'],
            'common_mistakes': ['dividir entre len de una lista vacía'],
            'forbidden': [],
            "lesson": {
                'title': 'Lista vacía y promedio',
                'explanation': 'Lee dos líneas que contienen la misma cantidad de números. Suma los valores de la misma posición y guarda cada resultado en una lista nueva. Una línea vacía genera []; si ambas están vacías no hay pares. Antes de calcular el promedio comprueba la cantidad para evitar dividir entre cero.',
                'code': 'primera = list(map(int, input().split()))\nsegunda = list(map(int, input().split()))\ncombinados = []\nfor posicion in range(len(primera)):\n    combinados.append(primera[posicion] + segunda[posicion])\nprint(combinados)\nprint(len(combinados))\nif len(combinados) == 0:\n    print("Sin datos")\nelse:\n    print(f"{sum(combinados) / len(combinados):.2f}")',
                'output': '[3, 8]\n2\n5.50',
                'input': '1 3\n2 5\n',
                'cases': [{'input': '\n\n', 'output': '[]\n0\nSin datos'}],
            },
        },
    ],
    'funciones': [
        {
            'focus': 'def y return',
            'objectives': ['Definir y llamar una función con un parámetro y return; imprimir el resultado fuera de ella.'],
            'introduced': ['def', 'return'],
            'required': ['def', 'return'],
            'review': ['fundamentos:2'],
            'input_spec': {'lines': 1},
            'edge_cases': ['texto con espacios'],
            'common_mistakes': ['return print devuelve None'],
            'forbidden': ['print_in_function'],
            "lesson": {
                'title': 'Crear una función',
                'explanation': 'def da nombre a una tarea reutilizable. El parámetro recibe el valor que pasas en la llamada y return entrega el resultado. Lee el nombre fuera de la función y muestra con print el texto que devuelve.',
                'code': 'def saludo(nombre):\n    return "Hola, " + nombre\n\nnombre = input()\nprint(saludo(nombre))',
                'output': 'Hola, Lía',
                'input': 'Lía\n',
            },
        },
        {
            'focus': 'parámetros',
            'objectives': ['Definir una función con al menos dos parámetros y reutilizarla con distintos valores.'],
            'introduced': [],
            'required': ['def', 'return'],
            'review': ['fundamentos:1'],
            'input_spec': {'lines': 3},
            'edge_cases': ['parámetros iguales'],
            'common_mistakes': ['invertir el orden de los argumentos'],
            'forbidden': ['print_in_function'],
            "lesson": {
                'title': 'Dos parámetros y varias llamadas',
                'explanation': 'Los parámetros reciben valores en el orden de la llamada. Lee dos cantidades y un costo unitario. Usa la misma función dos veces con las cantidades distintas y el costo común, sin reescribir el cálculo.',
                'code': 'def precio(cantidad, costo):\n    return cantidad * costo\n\nprimera = int(input())\nsegunda = int(input())\ncosto = int(input())\nprint(precio(primera, costo))\nprint(precio(segunda, costo))',
                'output': '10\n15',
                'input': '2\n3\n5\n',
            },
        },
        {
            'focus': 'decisiones en funciones',
            'objectives': ['Tomar una decisión dentro de una función y devolver el resultado sin imprimir dentro.', 'Reutilizar la comprobación del divisor de condicionales:2 cuando haya división.'],
            'introduced': [],
            'required': ['def', 'return', 'if'],
            'review': ['condicionales:2'],
            'input_spec': {'lines': 2, 'divisor': 'may_be_zero'},
            'edge_cases': ['divisor cero', 'total cero con divisor positivo'],
            'common_mistakes': ['imprimir dentro en lugar de devolver'],
            'forbidden': ['print_in_function'],
            "lesson": {
                'title': 'Decidir dentro de una función',
                'explanation': 'Una función puede usar if y devolver resultados distintos. Aquí comprueba el divisor antes de dividir: un total de 0 con divisor positivo es válido y da 0.0. print debe estar fuera; print devuelve None, así que return print(...) no devuelve el mensaje.',
                'code': 'def dividir(total, partes):\n    if partes == 0:\n        return "No se puede dividir"\n    return total / partes\n\ntotal = int(input())\npartes = int(input())\nprint(dividir(total, partes))',
                'output': 'No se puede dividir',
                'input': '8\n0\n',
                'cases': [{'input': '0\n2\n', 'output': '0.0'}, {'input': '8\n2\n', 'output': '4.0'}],
            },
        },
        {
            'focus': 'composición de funciones',
            'objectives': ['Componer dos funciones propias: el resultado de una alimenta a la otra.'],
            'introduced': [],
            'required': ['def', 'return'],
            'review': ['fundamentos:2'],
            'input_spec': {'lines': 1},
            'edge_cases': ['valor inicial cero'],
            'common_mistakes': ['usar el valor original en lugar del intermedio'],
            'forbidden': ['print_in_function'],
            "lesson": {
                'title': 'Usar el resultado de otra función',
                'explanation': 'Una función puede recibir lo que devuelve otra. Lee un número, calcula primero su doble y guárdalo como valor intermedio. Luego pasa ese resultado a siguiente para sumarle uno.',
                'code': 'def doble(numero):\n    return numero * 2\n\ndef siguiente(numero):\n    return numero + 1\n\nnumero = int(input())\nintermedio = doble(numero)\nprint(siguiente(intermedio))',
                'output': '7',
                'input': '3\n',
            },
        },
        {
            'focus': 'síntesis de funciones',
            'objectives': ['Reutilizar funciones con parámetros y decisiones para varios casos de entrada.', 'Reutilizar lectura repetida de bucles:4 y separar return de print.'],
            'introduced': [],
            'required': ['def', 'return'],
            'review': ['bucles:4'],
            'input_spec': {'lines': '1+2*N', 'count_first': True},
            'edge_cases': ['cantidad cero', 'total cero con cantidad positiva'],
            'common_mistakes': ['confundir total cero con cantidad cero'],
            'forbidden': ['print_in_function'],
            "lesson": {
                'title': 'Reutilizar funciones con casos límite',
                'explanation': 'Lee cuántos casos procesar y, para cada caso, total y cantidad en dos líneas. Reutiliza la función promedio. Si cantidad es cero devuelve Sin datos; si el total es cero y la cantidad es positiva, el promedio es 0.0. La función devuelve y el programa imprime.',
                'code': 'def promedio(total, cantidad):\n    if cantidad == 0:\n        return "Sin datos"\n    return total / cantidad\n\ncasos = int(input())\nfor _ in range(casos):\n    total = int(input())\n    cantidad = int(input())\n    print(promedio(total, cantidad))',
                'output': '4.0\nSin datos',
                'input': '2\n12\n3\n0\n0\n',
                'cases': [{'input': '1\n0\n3\n', 'output': '0.0'}],
            },
        },
    ],
    'diccionarios': [
        {
            'focus': 'crear y consultar',
            'objectives': ['Crear un diccionario literal con las parejas clave-valor indicadas y consultar una clave recibida por entrada.'],
            'introduced': ['dict_literal'],
            'required': ['dict_literal'],
            'review': ['listas:1'],
            'input_spec': {'lines': 1, 'key': 'exists', 'literal_given': True},
            'edge_cases': ['consultar cada clave indicada'],
            'common_mistakes': ['usar el valor como clave'],
            'forbidden': ['for', 'while', 'def', 'return', 'dict_write', 'subscript_write'],
            "lesson": {
                'title': 'Buscar por clave',
                'explanation': 'Un diccionario literal guarda pares de clave y valor entre llaves: {"mapa": 2, "llave": 1}. La clave es el nombre y el valor es su cantidad. Lee una clave existente y escríbela entre corchetes para consultar su valor. Una clave ausente produce KeyError; en esta etapa las consultas siempre existen.',
                'code': 'mochila = {"mapa": 2, "llave": 1}\nclave = input()\nprint(mochila[clave])',
                'output': '1',
                'input': 'llave\n',
            },
        },
        {
            'focus': 'actualizar valores',
            'objectives': ['Añadir o actualizar claves a partir de varias líneas de entrada.', 'Reutilizar split, índices y conversión numérica de listas:3.'],
            'introduced': ['dict_write', 'get'],
            'required': ['dict_write'],
            'review': ['listas:3'],
            'input_spec': {'lines': '1+N+1', 'count_first': True, 'key': 'exists'},
            'edge_cases': ['clave nueva', 'clave existente'],
            'common_mistakes': ['sobrescribir cuando hay que acumular'],
            'forbidden': [],
            "lesson": {
                'title': 'Añadir y actualizar claves',
                'explanation': 'diccionario[clave] = valor añade una clave o cambia su valor. get(clave, 0) entrega el valor actual o cero si la clave es nueva. Lee N registros: split separa el nombre y la cantidad, que debes convertir con int. Aquí cada registro suma existencias a la mochila.',
                'code': 'mochila = {"llave": 1}\nregistros = int(input())\nfor _ in range(registros):\n    partes = input().split()\n    clave = partes[0]\n    cantidad = int(partes[1])\n    mochila[clave] = mochila.get(clave, 0) + cantidad\nconsulta = input()\nprint(mochila["llave"], mochila[consulta])',
                'output': '3 1',
                'input': '2\nllave 2\nmapa 1\nmapa\n',
            },
        },
        {
            'focus': 'recorrer pares',
            'objectives': ['Recorrer pares clave-valor con items y calcular un resultado a partir de los valores.'],
            'introduced': ['items', 'values', 'unpack'],
            'required': ['items'],
            'review': ['bucles:2'],
            'input_spec': {'lines': '1+N', 'count_first': True, 'unique_keys': True, 'allow_zero_records': True},
            'edge_cases': ['N=0'],
            'common_mistakes': ['sumar las claves en vez de los valores'],
            'forbidden': [],
            "lesson": {
                'title': 'Recorrer claves y valores',
                'explanation': 'items() entrega cada par de clave y valor. values() entrega solo los valores: sum(mochila.values()) calcula su total. El for puede recibir ambos en dos variables. Usa _ como nombre para la clave cuando no la necesitas; es una convención, no una operación especial. Después de leer los registros, suma las cantidades durante el recorrido.',
                'code': 'mochila = {}\nregistros = int(input())\nfor _ in range(registros):\n    partes = input().split()\n    mochila[partes[0]] = int(partes[1])\ntotal = 0\nfor _, cantidad in mochila.items():\n    total += cantidad\nprint(total)',
                'output': '3',
                'input': '2\nmapa 2\nllave 1\n',
                'cases': [{'input': '0\n', 'output': '0'}],
            },
        },
        {
            'focus': 'contar frecuencias',
            'objectives': ['Contar frecuencias con un diccionario y acumular apariciones repetidas.', 'Reutilizar el recorrido de cadenas de listas:2.'],
            'introduced': [],
            'required': ['dict_write', 'get'],
            'review': ['listas:2'],
            'input_spec': {'lines': 2, 'allow_empty': True},
            'edge_cases': ['palabra repetida', 'palabra ausente'],
            'common_mistakes': ['reiniciar una cuenta repetida'],
            'forbidden': [],
            "lesson": {
                'title': 'Contar repeticiones',
                'explanation': 'Lee las palabras de una línea con split. Para cada palabra consulta la cuenta con get(palabra, 0) y añade una unidad. La primera aparición empieza en cero. En la segunda línea lee la palabra a consultar; get también permite responder cero si no apareció.',
                'code': 'conteos = {}\nfor palabra in input().split():\n    conteos[palabra] = conteos.get(palabra, 0) + 1\nconsulta = input()\nprint(conteos.get(consulta, 0))',
                'output': '2',
                'input': 'sol luna sol\nsol\n',
                'cases': [{'input': '\nmar\n', 'output': '0'}],
            },
        },
        {
            'focus': 'síntesis de diccionarios',
            'objectives': ['Combinar actualización, recorrido y consulta de claves ausentes para producir varios resultados.', 'Reutilizar una función que devuelva un resultado, como en funciones:3.'],
            'introduced': [],
            'required': ['dict_write', 'items', 'get', 'def', 'return'],
            'review': ['funciones:3'],
            'input_spec': {'lines': '1+N+1', 'count_first': True, 'allow_zero_records': True, 'key': 'may_be_absent'},
            'edge_cases': ['clave ausente', 'N=0', 'clave repetida'],
            'common_mistakes': ['consultar una clave ausente con corchetes'],
            'forbidden': [],
            "lesson": {
                'title': 'Consultar claves ausentes',
                'explanation': 'Combina lectura de registros, actualización y recorrido del diccionario. Una función suma las cantidades de items() y devuelve el total. Después consulta una clave con get(clave, 0): responde cero si no existe. N = 0 representa un diccionario vacío y sigue habiendo una línea para la consulta.',
                'code': 'def total_existencias(inventario):\n    total = 0\n    for _, cantidad in inventario.items():\n        total += cantidad\n    return total\n\ninventario = {}\nregistros = int(input())\nfor _ in range(registros):\n    partes = input().split()\n    clave = partes[0]\n    cantidad = int(partes[1])\n    inventario[clave] = inventario.get(clave, 0) + cantidad\nconsulta = input()\nprint(total_existencias(inventario))\nprint(inventario.get(consulta, 0))',
                'output': '3\n0',
                'input': '2\nsol 2\nluna 1\nmar\n',
                'cases': [{'input': '0\nsol\n', 'output': '0\n0'}],
            },
        },
    ],
}


CURRICULUM.update({'taller': [{'focus': 'Mínimo, máximo y distancia',
             'objectives': ['Encontrar extremos de una lista no vacía y calcular una distancia con abs.'],
             'introduced': ['min', 'max', 'abs'],
             'required': ['min', 'max', 'abs'],
             'review': ['listas:3'],
             'input_spec': {'lines': 1, 'numeric_count': 'positive'},
             'edge_cases': ['un único valor', 'valores negativos'],
             'common_mistakes': ['usar min en una lista vacía'],
             'forbidden': [],
             'lesson': {'title': 'Mínimo, máximo y distancia',
                        'explanation': 'min encuentra el menor valor y max el mayor. abs convierte una diferencia negativa en su '
                                       'distancia positiva. Lee una lista no vacía con split y map. Con -3, 2 y 7, los extremos '
                                       'son -3 y 7; su distancia es abs(-3 - 7) = 10.',
                        'code': 'valores = list(map(int, input().split()))\n'
                                'menor = min(valores)\n'
                                'mayor = max(valores)\n'
                                'print(menor, mayor)\n'
                                'print(abs(menor - mayor))',
                        'input': '-3 2 7\n',
                        'output': '-3 7\n10',
                        'cases': [{'input': '4\n', 'output': '4 4\n0'}]}},
            {'focus': 'Redondear un cálculo',
             'objectives': ['Calcular una media protegida contra cero y redondear el valor con round.'],
             'introduced': ['round'],
             'required': ['round', 'if'],
             'review': ['funciones:3', 'fundamentos:3'],
             'input_spec': {'lines': 2, 'divisor': 'may_be_zero'},
             'edge_cases': ['divisor cero', 'resultado con más de dos decimales'],
             'common_mistakes': ['confundir redondear con mostrar dos decimales'],
             'forbidden': [],
             'lesson': {'title': 'Redondear un cálculo',
                        'explanation': 'round(valor, 2) devuelve un número redondeado a dos decimales. Una f-string con :.2f '
                                       'solo controla cómo se muestra. Protege el divisor antes de calcular. round usa el par '
                                       'más cercano en empates; para la misión usa resultados que no sean empates exactos.',
                        'code': 'total = float(input())\n'
                                'cantidad = int(input())\n'
                                'if cantidad == 0:\n'
                                '    print("Sin datos")\n'
                                'else:\n'
                                '    media = round(total / cantidad, 2)\n'
                                '    print(f"{media:.2f}")',
                        'input': '10\n3\n',
                        'output': '3.33',
                        'cases': [{'input': '0\n0\n', 'output': 'Sin datos'}]}},
            {'focus': 'Limpiar y normalizar texto',
             'objectives': ['Quitar espacios exteriores con strip y normalizar letras con upper antes de comparar.'],
             'introduced': ['strip', 'upper'],
             'required': ['strip', 'upper'],
             'review': ['condicionales:2'],
             'input_spec': {'lines': 1},
             'edge_cases': ['espacios exteriores', 'letras minúsculas'],
             'common_mistakes': ['creer que strip quita espacios interiores'],
             'forbidden': [],
             'lesson': {'title': 'Limpiar y normalizar texto',
                        'explanation': 'strip() devuelve el texto sin espacios al inicio y al final. upper() devuelve una '
                                       'versión en mayúsculas. Guarda el resultado: estos métodos no cambian la cadena original. '
                                       'Los espacios interiores permanecen. Normalizar permite reconocer la misma palabra aunque '
                                       'venga en minúsculas.',
                        'code': 'clave = input().strip().upper()\n'
                                'if clave == "SOL":\n'
                                '    print("Abierto")\n'
                                'else:\n'
                                '    print("Cerrado")',
                        'input': '  sol  \n',
                        'output': 'Abierto',
                        'cases': [{'input': ' so l \n', 'output': 'Cerrado'}]}},
            {'focus': 'Reemplazar partes de una cadena',
             'objectives': ['Usar replace para sustituir todas las apariciones y contar las palabras del texto limpio.'],
             'introduced': ['replace'],
             'required': ['replace', 'split', 'len'],
             'review': ['fundamentos:5', 'taller:3'],
             'input_spec': {'lines': 1},
             'edge_cases': ['varios separadores', 'texto vacío'],
             'common_mistakes': ['no guardar la cadena devuelta'],
             'forbidden': [],
             'lesson': {'title': 'Reemplazar partes de una cadena',
                        'explanation': 'replace(viejo, nuevo) devuelve una cadena con todas las apariciones sustituidas. Aquí '
                                       'cambia guiones por espacios; después split separa palabras e ignora espacios repetidos. '
                                       'Guarda cada transformación antes de contar con len.',
                        'code': 'texto = input().strip().replace("-", " ")\n'
                                'palabras = texto.split()\n'
                                'print(texto)\n'
                                'print(len(palabras))',
                        'input': 'sol-luna-mar\n',
                        'output': 'sol luna mar\n3',
                        'cases': []}},
            {'focus': 'Informe de alquimia',
             'objectives': ['Combinar función, lista numérica, extremos y media redondeada; aceptar entrada vacía.'],
             'introduced': [],
             'required': ['def', 'return', 'min', 'max', 'round', 'if'],
             'review': ['listas:4', 'funciones:3', 'taller:1', 'taller:2'],
             'input_spec': {'lines': 1, 'allow_empty': True},
             'edge_cases': ['lista vacía', 'un solo valor', 'decimales'],
             'common_mistakes': ['calcular extremos antes de comprobar la lista'],
             'forbidden': [],
             'lesson': {'title': 'Informe de alquimia',
                        'explanation': 'Reutiliza una función con return para elaborar un informe. Si len vale cero, evita min, '
                                       'max y la división. Para datos presentes devuelve un texto con mínimo, máximo y media. '
                                       'Todas las herramientas ya se enseñaron en el Taller y en Funciones.',
                        'code': 'def informe(valores):\n'
                                '    if len(valores) == 0:\n'
                                '        return "Sin datos"\n'
                                '    media = round(sum(valores) / len(valores), 2)\n'
                                '    return f"{min(valores):.2f} {max(valores):.2f} {media:.2f}"\n'
                                '\n'
                                'valores = list(map(float, input().split()))\n'
                                'print(informe(valores))',
                        'input': '2 4 9\n',
                        'output': '2.00 9.00 5.00',
                        'cases': [{'input': '\n', 'output': 'Sin datos'}]}}],
 'rutas': [{'focus': 'Pertenencia con in',
            'objectives': ['Comprobar pertenencia a una lista y a las claves de un diccionario antes de consultar.'],
            'introduced': ['in'],
            'required': ['in'],
            'review': ['diccionarios:1', 'listas:3'],
            'input_spec': {'lines': 2},
            'edge_cases': ['elemento ausente', 'lista vacía'],
            'common_mistakes': ['creer que in busca los valores del diccionario'],
            'forbidden': [],
            'lesson': {'title': 'Pertenencia con in',
                       'explanation': 'valor in lista pregunta si el elemento aparece. clave in diccionario pregunta por las '
                                      'claves, no por sus cantidades. También puede buscar una parte de una cadena. Comprueba '
                                      'pertenencia antes de consultar con corchetes si la clave puede faltar.',
                       'code': 'rutas = input().split()\n'
                               'consulta = input()\n'
                               'if consulta in rutas:\n'
                               '    print("Ruta conocida")\n'
                               'else:\n'
                               '    print("Ruta nueva")\n'
                               'mochila = {"mapa": 2, "llave": 1}\n'
                               'if consulta in mochila:\n'
                               '    print(mochila[consulta])\n'
                               'else:\n'
                               '    print(0)',
                       'input': 'mapa faro\nmapa\n',
                       'output': 'Ruta conocida\n2',
                       'cases': [{'input': '\nmar\n', 'output': 'Ruta nueva\n0'}]}},
           {'focus': 'Detener una búsqueda con break',
            'objectives': ['Buscar la primera coincidencia y detener el bucle con break; informar si no existe.'],
            'introduced': ['break'],
            'required': ['break', 'for', 'if'],
            'review': ['rutas:1', 'bucles:3'],
            'input_spec': {'lines': 2},
            'edge_cases': ['coincidencia al inicio', 'ninguna coincidencia'],
            'common_mistakes': ['seguir recorriendo después de encontrar'],
            'forbidden': [],
            'lesson': {'title': 'Detener una búsqueda con break',
                       'explanation': 'break termina inmediatamente el bucle que lo contiene. Una variable guarda el resultado '
                                      'de la búsqueda. En este ejemplo empezamos con -1 y lo cambiamos al índice encontrado. '
                                      'Detenerse garantiza que queda la primera coincidencia.',
                       'code': 'rutas = input().split()\n'
                               'consulta = input()\n'
                               'posicion = -1\n'
                               'for indice in range(len(rutas)):\n'
                               '    if rutas[indice] == consulta:\n'
                               '        posicion = indice\n'
                               '        break\n'
                               'print(posicion)',
                       'input': 'sol luna sol\nsol\n',
                       'output': '0',
                       'cases': [{'input': 'sol luna\nmar\n', 'output': '-1'}]}},
           {'focus': 'Saltar registros con continue',
            'objectives': ['Ignorar registros no válidos con continue y acumular únicamente los aceptados.'],
            'introduced': ['continue'],
            'required': ['continue', 'for'],
            'review': ['bucles:5'],
            'input_spec': {'lines': 1, 'allow_empty': True},
            'edge_cases': ['todos descartados', 'entrada vacía'],
            'common_mistakes': ['sumar un registro antes de descartarlo'],
            'forbidden': [],
            'lesson': {'title': 'Saltar registros con continue',
                       'explanation': 'continue salta el resto de la vuelta actual y empieza la siguiente. Colócalo antes de la '
                                      'operación que debe omitir. Aquí se descartan negativos y se suman los demás. En while '
                                      'debes actualizar la lectura antes de continuar para no repetir siempre el mismo dato.',
                       'code': 'valores = list(map(int, input().split()))\n'
                               'total = 0\n'
                               'for valor in valores:\n'
                               '    if valor < 0:\n'
                               '        continue\n'
                               '    total += valor\n'
                               'print(total)',
                       'input': '-2 3 4\n',
                       'output': '7',
                       'cases': [{'input': '-2 -1\n', 'output': '0'}]}},
           {'focus': 'Ordenar y numerar con sorted y enumerate',
            'objectives': ['Ordenar valores sin modificar la lista original y numerar el recorrido desde uno.'],
            'introduced': ['sorted', 'enumerate'],
            'required': ['sorted', 'enumerate', 'for'],
            'review': ['diccionarios:3'],
            'input_spec': {'lines': 1, 'allow_empty': True},
            'edge_cases': ['valores repetidos', 'lista vacía'],
            'common_mistakes': ['esperar que sorted cambie la lista original'],
            'forbidden': [],
            'lesson': {'title': 'Ordenar y numerar con sorted y enumerate',
                       'explanation': 'sorted(lista) devuelve una nueva lista ordenada de menor a mayor. enumerate(lista, 1) '
                                      'entrega pares de posición y valor empezando en uno. Se reciben con dos variables, igual '
                                      'que los pares de items(). Sin el segundo argumento las posiciones empiezan en cero.',
                       'code': 'valores = list(map(int, input().split()))\n'
                               'ordenados = sorted(valores)\n'
                               'for posicion, valor in enumerate(ordenados, 1):\n'
                               '    print(posicion, valor)',
                       'input': '7 2 7\n',
                       'output': '1 2\n2 7\n3 7',
                       'cases': [{'input': '\n', 'output': ''}]}},
           {'focus': 'Recorrer filas con bucles anidados',
            'objectives': ['Leer N filas de valores y recorrer cada fila con un bucle interior; producir recuento por fila y '
                           'total general.'],
            'introduced': ['nested_for'],
            'required': ['nested_for', 'for'],
            'review': ['listas:4', 'rutas:3'],
            'input_spec': {'lines': '1+N', 'count_first': True, 'allow_zero_records': True},
            'edge_cases': ['N=0', 'fila vacía', 'valores descartados'],
            'common_mistakes': ['reiniciar el total general dentro de cada fila'],
            'forbidden': [],
            'lesson': {'title': 'Recorrer filas con bucles anidados',
                       'explanation': 'Un for dentro de otro repite el recorrido interior por cada fila. Lee N y luego una línea '
                                      'por fila. El contador de la fila se reinicia dentro del bucle exterior; el total general '
                                      'se inicia antes de ambos. break solo termina el bucle más cercano.',
                       'code': 'filas = int(input())\n'
                               'total = 0\n'
                               'for _ in range(filas):\n'
                               '    positivos = 0\n'
                               '    for valor in map(int, input().split()):\n'
                               '        if valor > 0:\n'
                               '            positivos += 1\n'
                               '            total += valor\n'
                               '    print(positivos)\n'
                               'print(total)',
                       'input': '2\n1 -2 3\n0 4\n',
                       'output': '2\n1\n8',
                       'cases': [{'input': '0\n', 'output': '0'}]}}],
 'proyecto': [{'focus': 'Proyecto: registrar provisiones',
               'objectives': ['Construir el inventario de una expedición desde registros normalizados; fusionar nombres '
                              'repetidos y resumir existencias.'],
               'introduced': [],
               'required': ['dict_write', 'get', 'strip', 'upper'],
               'review': ['diccionarios:2', 'taller:3'],
               'input_spec': {'lines': '1+2*N', 'count_first': True, 'allow_zero_records': True, 'lines_per_iteration': 2},
               'edge_cases': ['N=0', 'nombres repetidos con distinto formato'],
               'common_mistakes': ['reemplazar en vez de acumular provisiones'],
               'forbidden': [],
               'lesson': {'title': 'Proyecto: registrar provisiones',
                          'explanation': 'El proyecto será una expedición. Cada misión es un programa independiente y añade una '
                                         'parte de su gestión. Primero registra provisiones: lee N, luego nombre y cantidad en '
                                         'dos líneas por registro. Normaliza nombres con strip y upper; acumula los repetidos '
                                         'con get. Informa tipos distintos y unidades totales.',
                          'code': 'inventario = {}\n'
                                  'registros = int(input())\n'
                                  'for _ in range(registros):\n'
                                  '    nombre = input().strip().upper()\n'
                                  '    cantidad = int(input())\n'
                                  '    inventario[nombre] = inventario.get(nombre, 0) + cantidad\n'
                                  'print(len(inventario), sum(inventario.values()))',
                          'input': '2\n pan \n2\nPAN\n3\n',
                          'output': '1 5',
                          'cases': [{'input': '0\n', 'output': '0 0'}]}},
              {'focus': 'Proyecto: presupuestar la expedición',
               'objectives': ['Definir una función de coste y decidir si un presupuesto cubre la lista de compras.'],
               'introduced': [],
               'required': ['def', 'return', 'dict_write', 'if'],
               'review': ['funciones:2', 'taller:2'],
               'input_spec': {'lines': '2+2*N', 'count_first': True, 'lines_per_iteration': 2},
               'edge_cases': ['presupuesto justo', 'N=0', 'saldo negativo'],
               'common_mistakes': ['mezclar precio unitario y coste total'],
               'forbidden': [],
               'lesson': {'title': 'Proyecto: presupuestar la expedición',
                          'explanation': 'La segunda parte calcula costes: una función devuelve precio por cantidad. Lee N, '
                                         'luego precio y cantidad en dos líneas por compra; al final lee presupuesto. Acumula '
                                         'cada coste. Usa un diccionario para reunir el coste y el saldo; redondea al presentar '
                                         'y decide si alcanza.',
                          'code': 'def coste(precio, cantidad):\n'
                                  '    return precio * cantidad\n'
                                  '\n'
                                  'totales = {}\n'
                                  'totales["coste"] = 0\n'
                                  'compras = int(input())\n'
                                  'for _ in range(compras):\n'
                                  '    precio = float(input())\n'
                                  '    cantidad = int(input())\n'
                                  '    totales["coste"] += coste(precio, cantidad)\n'
                                  'presupuesto = float(input())\n'
                                  'totales["saldo"] = presupuesto - totales["coste"]\n'
                                  'print(f"{totales[\'coste\']:.2f} {totales[\'saldo\']:.2f}")\n'
                                  'if totales["saldo"] >= 0:\n'
                                  '    print("Alcanza")\n'
                                  'else:\n'
                                  '    print("Falta")',
                          'input': '2\n2.5\n2\n3\n1\n10\n',
                          'output': '8.00 2.00\nAlcanza',
                          'cases': []}},
              {'focus': 'Proyecto: atender pedidos',
               'objectives': ['Procesar órdenes hasta una señal; descartar cantidades inválidas y descontar solo existencias '
                              'suficientes.'],
               'introduced': [],
               'required': ['while', 'break', 'continue', 'dict_write', 'in'],
               'review': ['rutas:1', 'rutas:2', 'rutas:3'],
               'input_spec': {'lines': 'variable', 'terminator': 'FIN', 'record': 'name quantity'},
               'edge_cases': ['FIN como primera línea', 'artículo ausente', 'existencias insuficientes'],
               'common_mistakes': ['descontar antes de comprobar existencias'],
               'forbidden': [],
               'lesson': {'title': 'Proyecto: atender pedidos',
                          'explanation': 'La tercera parte atiende órdenes. Lee una línea en cada vuelta de while; FIN detiene '
                                         'con break. En otras líneas lee nombre y cantidad con split. Omite cantidades no '
                                         'positivas con continue. Solo descuenta si el artículo existe y alcanza. Cada pedido '
                                         'válido por formato produce una respuesta.',
                          'code': 'inventario = {"PAN": 3, "AGUA": 2}\n'
                                  'while True:\n'
                                  '    linea = input().strip().upper()\n'
                                  '    if linea == "FIN":\n'
                                  '        break\n'
                                  '    partes = linea.split()\n'
                                  '    nombre = partes[0]\n'
                                  '    cantidad = int(partes[1])\n'
                                  '    if cantidad <= 0:\n'
                                  '        print("Ignorado")\n'
                                  '        continue\n'
                                  '    if nombre in inventario and inventario[nombre] >= cantidad:\n'
                                  '        inventario[nombre] -= cantidad\n'
                                  '        print("Entregado")\n'
                                  '    else:\n'
                                  '        print("No disponible")\n'
                                  'print(sum(inventario.values()))',
                          'input': 'pan 2\nagua 0\npan 2\nFIN\n',
                          'output': 'Entregado\nIgnorado\nNo disponible\n3',
                          'cases': [{'input': 'FIN\n', 'output': '5'}]}},
              {'focus': 'Proyecto: informar por zonas',
               'objectives': ['Leer filas de provisiones por zona con bucles anidados y ordenar y numerar un informe de sus '
                              'totales.'],
               'introduced': [],
               'required': ['nested_for', 'sorted', 'enumerate', 'dict_write'],
               'review': ['rutas:4', 'rutas:5', 'diccionarios:3'],
               'input_spec': {'lines': '1+2*N', 'count_first': True, 'lines_per_iteration': 2, 'allow_zero_records': True},
               'edge_cases': ['zona sin provisiones', 'nombres de zona repetidos', 'N=0'],
               'common_mistakes': ['olvidar acumular una zona repetida'],
               'forbidden': [],
               'lesson': {'title': 'Proyecto: informar por zonas',
                          'explanation': 'La cuarta parte agrupa provisiones por zona. Lee N y, por registro, el nombre de zona '
                                         'y una línea de cantidades. Recorre las cantidades con un bucle interior y suma por '
                                         'zona en un diccionario. sorted(diccionario) devuelve las claves ordenadas; enumerate '
                                         'permite numerar el informe desde uno.',
                          'code': 'zonas = {}\n'
                                  'registros = int(input())\n'
                                  'for _ in range(registros):\n'
                                  '    zona = input().strip().upper()\n'
                                  '    for cantidad in map(int, input().split()):\n'
                                  '        zonas[zona] = zonas.get(zona, 0) + cantidad\n'
                                  '    if zona not in zonas:\n'
                                  '        zonas[zona] = 0\n'
                                  'for posicion, zona in enumerate(sorted(zonas), 1):\n'
                                  '    print(posicion, zona, zonas[zona])',
                          'input': '2\nbosque\n2 3\naldea\n4\n',
                          'output': '1 ALDEA 4\n2 BOSQUE 5',
                          'cases': [{'input': '0\n', 'output': ''}]}},
              {'focus': 'Proyecto final: preparar la partida',
               'objectives': ['Integrar funciones, registros, inventario, consultas y planificación: calcular kits posibles por '
                              'recurso, elegir el límite y mostrar sobrantes.'],
               'introduced': [],
               'required': ['def', 'return', 'dict_write', 'min', 'floor_divide'],
               'review': ['proyecto:1', 'proyecto:2', 'proyecto:3', 'proyecto:4', 'fundamentos:4'],
               'input_spec': {'lines': '1+2*N',
                              'count_first': True,
                              'lines_per_iteration': 2,
                              'numeric_count': 'positive',
                              'demand': 'positive', 'names': 'unique'},
               'edge_cases': ['recurso sin existencias', 'cantidades no divisibles', 'un solo recurso'],
               'common_mistakes': ['dividir por una necesidad cero', 'elegir máximo en vez del recurso limitante'],
               'forbidden': [],
               'lesson': {'title': 'Proyecto final: preparar la partida',
                          'explanation': 'La expedición termina preparando kits. Lee N mayor que cero; para cada recurso lee su '
                                         'nombre único y después existencias y unidades necesarias por kit, siempre positivas en la '
                                         'necesidad. Una función devuelve existencias // necesidad. El mínimo de esas '
                                         'capacidades indica cuántos kits completos se pueden formar. Para cada recurso, el '
                                         'sobrante es existencias menos kits por necesidad. Muestra primero kits y luego '
                                         'recursos ordenados y sus sobrantes.',
                          'code': 'def capacidad(existencias, necesidad):\n'
                                  '    return existencias // necesidad\n'
                                  '\n'
                                  'recursos = {}\n'
                                  'capacidades = []\n'
                                  'registros = int(input())\n'
                                  'for _ in range(registros):\n'
                                  '    nombre = input().strip().upper()\n'
                                  '    datos = list(map(int, input().split()))\n'
                                  '    recursos[nombre] = datos\n'
                                  '    capacidades.append(capacidad(datos[0], datos[1]))\n'
                                  'kits = min(capacidades)\n'
                                  'print(kits)\n'
                                  'for nombre in sorted(recursos):\n'
                                  '    datos = recursos[nombre]\n'
                                  '    sobrante = datos[0] - kits * datos[1]\n'
                                  '    print(nombre, sobrante)',
                          'input': '2\npan\n7 2\nagua\n5 1\n',
                          'output': '3\nAGUA 2\nPAN 1',
                          'cases': [{'input': '1\npan\n0 2\n', 'output': '0\nPAN 0'}]}}]})

def source_features(source):
    """Construcciones observables; las llamadas no enseñadas también cuentan."""
    tree = ast.parse(source)
    nodes = list(ast.walk(tree))
    features = set()
    functions = {node.name for node in nodes if isinstance(node, ast.FunctionDef)}
    dictionaries = {target.id for node in nodes if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
                    for target in node.targets if isinstance(target, ast.Name)}
    kinds = {ast.Add: 'add', ast.Sub: 'subtract', ast.Mult: 'multiply', ast.Div: 'divide',
             ast.FloorDiv: 'floor_divide', ast.Mod: 'modulo', ast.JoinedStr: 'fstring',
             ast.Compare: 'comparison', ast.If: 'if', ast.For: 'for', ast.While: 'while',
             ast.AugAssign: 'augassign', ast.FunctionDef: 'def', ast.Return: 'return',
             ast.List: 'list_literal', ast.Dict: 'dict_literal', ast.And: 'and', ast.Or: 'or',
             ast.In: 'in', ast.NotIn: 'in', ast.Break: 'break', ast.Continue: 'continue'}
    for node in nodes:
        if type(node) in kinds:
            features.add(kinds[type(node)])
        if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp,
                             ast.Lambda, ast.Try, ast.With, ast.ClassDef, ast.Set, ast.AsyncFunctionDef)):
            features.add(type(node).__name__)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id not in functions:
                features.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                features.add(node.func.attr)
        if isinstance(node, ast.If) and node.orelse:
            features.add('elif' if isinstance(node.orelse[0], ast.If) else 'else')
        if isinstance(node, ast.Subscript):
            if isinstance(node.ctx, ast.Store):
                features.add('dict_write' if isinstance(node.value, ast.Name) and node.value.id in dictionaries else 'subscript_write')
            else:
                features.add('slice' if isinstance(node.slice, ast.Slice) else 'index')
        if isinstance(node, ast.Tuple):
            features.add('unpack' if isinstance(node.ctx, ast.Store) else 'tuple_literal')
        if isinstance(node, ast.FunctionDef) and any(
            isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == 'print'
            for child in ast.walk(node)
        ):
            features.add('print_in_function')
        if isinstance(node, ast.For) and any(isinstance(child, ast.For)
                                             for statement in node.body for child in ast.walk(statement)):
            features.add('nested_for')
    return features


def source_fits_stage(source, world_id, stage):
    entry = CURRICULUM[world_id][stage - 1]
    try:
        used = source_features(source)
        nodes = list(ast.walk(ast.parse(source)))
    except SyntaxError:
        return False
    if not used <= set(entry['allowed']) or not set(entry['required']) <= used:
        return False
    per_turn = entry['input_spec'].get('lines_per_iteration')
    if per_turn and not any(isinstance(node, (ast.For, ast.While)) and sum(
        isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == 'input'
        for child in ast.walk(node)) >= per_turn for node in nodes):
        return False
    return True


def _prepare_curriculum():
    taught = set()
    previous = None
    vocabulary = {feature for stages in CURRICULUM.values() for entry in stages
                  for feature in entry['introduced']} | {'print_in_function', 'tuple_literal', 'ListComp', 'DictComp', 'SetComp', 'GeneratorExp', 'Lambda', 'Try', 'With', 'ClassDef', 'Set', 'AsyncFunctionDef'}
    for world in WORLDS:
        for stage, entry in enumerate(CURRICULUM[world['id']], 1):
            taught.update(entry['introduced'])
            entry.update(world=world['id'], stage=stage, id=f"{world['id']}:{stage}")
            entry['prerequisites'] = list(dict.fromkeys(([previous] if previous else []) + entry['review']))
            entry['allowed'] = sorted(taught - set(entry['forbidden']))
            entry['forbidden'] = sorted(vocabulary - set(entry['allowed']))
            entry['mastery'] = {'public_tests': 2, 'hidden_tests': 4, 'hidden_must_include': entry['edge_cases']}
            previous = entry['id']


def validate_curriculum():
    from .grader import run_one
    if set(CURRICULUM) != set(WORLD_BY_ID):
        raise ValueError('Los mundos y el temario no coinciden.')
    seen = set()
    for world in WORLDS:
        entries = CURRICULUM[world['id']]
        if len(entries) != STAGES_PER_WORLD:
            raise ValueError(f"{world['id']}: faltan etapas.")
        for entry in entries:
            if not set(entry['prerequisites']) <= seen:
                raise ValueError(f"{entry['id']}: prerrequisitos inválidos.")
            lesson = entry['lesson']
            if not source_fits_stage(lesson['code'], entry['world'], entry['stage']):
                raise ValueError(f"{entry['id']}: el ejemplo excede o incumple la etapa ({source_features(lesson['code']) - set(entry['allowed'])}).")
            for case in [lesson, *lesson.get('cases', [])]:
                result = run_one(lesson['code'], case['input'])
                if result['error'] or result['actual'] != case['output'].strip():
                    raise ValueError(f"{entry['id']}: salida de ejemplo incorrecta: {result}.")
            seen.add(entry['id'])


_prepare_curriculum()
# Alias para los consumidores existentes, derivados de la única fuente.
STAGES = {world: [entry['focus'] for entry in stages] for world, stages in CURRICULUM.items()}
LESSONS = {world: {entry['stage']: entry['lesson'] for entry in stages} for world, stages in CURRICULUM.items()}
STAGE_REQUIREMENTS = {world: [' '.join(entry['objectives']) for entry in stages] for world, stages in CURRICULUM.items()}
validate_curriculum()
