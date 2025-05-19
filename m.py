class Gramatica:
    def __init__(self, cantNoTerminales,producciones):
        #porque en Python no se puede solo declara una variable
        self.terminales=set()
        #set, para que no hayan elementos repetidos, con los noterminales de la gramática 
        
        self.noTerminales=set()
        self.cantNoTerminales=cantNoTerminales
        self.simboloInicial='S'
        self.vacio='e'
        #Diccionario con las producciones de la gramática, será pasado desde la interfaz con la api al constructor.
        self.producciones=producciones
        self.first={}
        self.follow={}
        self.recorrerProducciones()
    

    def recorrerProducciones(self):
        for clave,valor in self.producciones.items():
            self.añadirNoTerminal(str(clave))

            for x in valor:
                for simbolo in x:
                    if str(simbolo) != 'e':
                        if str(simbolo).isupper():
                            self.añadirNoTerminal(str(simbolo))
                        else:
                            self.añadirTerminal(str(simbolo))

    def asignarFirst(self):
        # Inicializa FIRST para todos los símbolos
        for simbolo in (self.noTerminales | self.terminales):
            self.first[simbolo] = set()
            if simbolo in self.terminales:
                self.first[simbolo].add(simbolo)
        cambio = True
        while cambio:
            cambio = False
            for noTerminal in self.noTerminales:
                for produccion in self.producciones[noTerminal]:
                    contiene_vacio = True
                    for simbolo in produccion:
                        if simbolo == self.vacio:
                            # Si encuentras epsilon, solo marcas que la producción puede ser vacía
                            break
                        antes = len(self.first[noTerminal])
                        self.first[noTerminal].update(self.first[simbolo] - {self.vacio})
                        if self.vacio not in self.first[simbolo]:
                            contiene_vacio = False
                            break
                        despues = len(self.first[noTerminal])
                    if contiene_vacio:
                        if self.vacio not in self.first[noTerminal]:
                            self.first[noTerminal].add(self.vacio)
                            cambio = True
                    if len(self.first[noTerminal]) > antes:
                        cambio = True
        self.convertirALista()

    def convertirALista(self):
        for clave,valor in self.first.items():
            self.first[clave]=list(valor)

    def añadirTerminal(self, terminal):
        self.terminales.add(terminal)

        
    def añadirNoTerminal(self, noTerminal):
        self.noTerminales.add(noTerminal)
    """
    #Solo mientras testeamos porque la lógica no debe imprimir nada, esto debería ir en la interfaz.
    def imprimirGramatica(self):
        print(f"Gramatica:\nTerminales: {self.terminales}\nNo terminales: {self.noTerminales}\nCantidad de no terminales: {self.cantNoTerminales}\nSimbolo inicial: {self.simboloInicial}\nVacio:{self.vacio}\nProducciones: {self.producciones} ")
    """

    def inicial_follow(self):
        for noT in self.noTerminales:   #vamos a crear los sets de follow para cada no terminal
            self.follow[noT] = set()
        self.follow[self.simboloInicial].add('$') #para el simiblo incial de 1 agregamos el $ al follow
        print("Follow después de inicialización: ", self.follow)  #testeo ahora c borra

    def calculo_follow(self):  
        self.inicial_follow()  #vamos a inicializar el follow antes de calcularlo y poner el $
        
        def obtener_FIRST_de_cadena(alpha):  
                resultado = set()
                for simbolo in alpha:
                        # Convertimos a conjunto para poder hacer operaciones de conjuntos
                        first_simbolo = set(self.first[simbolo])
                        resultado |= first_simbolo - {self.vacio}
                        if self.vacio not in first_simbolo:
                            return resultado
                resultado.add(self.vacio)
                return resultado

        cambio = True
        while cambio:
            cambio = False
            for A, producciones in self.producciones.items():  #recorremos las producciones de la gramatica, A es la cabeza de la derivacion 
                for prod in producciones:   #las producciones son listas de cadenas como aA bB 
                    for i in range(len(prod)):  #i de contador para recorrerla como  por ejemplo en  aA, bB el i es 0 1
                        B = prod[i]   #B es el simbolo que queremos calcular el follow
                        if B in self.noTerminales:   #si es no temrinal 
                            alpha = prod[i+1:]   #miramos lo que le sigue que seria alpha 
                            if alpha:
                                first_alpha = obtener_FIRST_de_cadena(alpha)   #obtnemos el primero del que le sigue a b
                                sin_vacio = first_alpha - {self.vacio}   #le quitamos el vacio a alpha 
                                if not sin_vacio.issubset(self.follow[B]):  #si los simbolos de first alpha sin el vacio NO ESTAN EN el follow de B
                                    self.follow[B].update(sin_vacio)  #actualizamos el follow de B con el first de ALPHA sin epsilon
                                    cambio = True
                                if self.vacio in first_alpha: #pero si esta e en el first de ALPHA 
                                    if not self.follow[A].issubset(self.follow[B]): #Si FOLLOW[A] no es subconjunto de FOLLOW[B]
                                        self.follow[B].update(self.follow[A]) #ENTONCES actualizamos el follow de B con el follow de A
                                        cambio = True
                            else: #si alpha es vacio, significa que no hay nada a la derecha de B -> tenemos que agregar el follow de A al follow de B
                                if not self.follow[A].issubset(self.follow[B]):
                                    self.follow[B].update(self.follow[A])  #agregamos FOLLOW[A] a FOLLOW[B]
                                    cambio = True
        return self.follow

class RevisadorLL1:
    #Encargado de IDENTIFICAR si la gramatica tiene RI o FC
    def __init__(self,gramatica):
        self.gramatica=gramatica
        self.noTerminalesRI=set()
        self.noTerminalesFC=set()
        self.tieneRI=self.analizarRI()
        self.tieneFC=self.analizarFC()
        #Almacenarán no terminales que produzcan RI o FC
        

    def analizarRI(self):
        resultado=False
        for noTerminal,producciones in self.gramatica.producciones.items():
            if (self.comprobarRI(noTerminal,producciones)):
                self.noTerminalesRI.add(noTerminal)
                resultado=True
        return resultado

    def analizarFC(self):
        resultado=False
        for noTerminal,producciones in self.gramatica.producciones.items():
            if (self.comprobarFC(producciones)):
                self.noTerminalesFC.add(noTerminal)
                resultado=True
        return resultado
        
    def comprobarFC(self,producciones):
        for i in range(1,len(producciones)):
            if producciones[i][0] == producciones[0][0]:
                return True
        return False
    
    def comprobarRI(self, noTerminal, producciones, visitados=None):
        if visitados is None:
            visitados = set()
        visitados.add(noTerminal)
        for produccion in producciones:
            if not produccion:
                continue
            if produccion[0] == noTerminal:
                return True
            elif produccion[0] in self.gramatica.noTerminales and produccion[0] not in visitados:
                if self.comprobarRI(produccion[0], self.gramatica.producciones[produccion[0]], visitados):
                    return True
        return False

class ArregladorLL1:
    # Encargado de, si la gramatica tiene FC o RI, eliminarla si es posible.
    def __init__(self, revisador):
        self.revisador = revisador
        self.quitarRI = self.administrarArreglos()
        self.quitarFC = None

    def administrarArreglos(self):
        if self.revisador.tieneRI:
            for noTerminal in self.revisador.noTerminalesRI:
                alpha, beta = self.obtenerAuxiliaresRI(noTerminal)
                if len(beta) == 0:
                    return False
                else:
                    self.eliminarRI(alpha, beta, noTerminal)
                    return True

    def obtenerAuxiliaresRI(self, noTerminal):
        alpha = []
        beta = []
        for produccion in self.revisador.gramatica.producciones[noTerminal]:
            # Si el primer elemento es el noTerminal -> esa unidad de produccion tiene RI
            if produccion[0] == noTerminal:
                # alpha es el resto de la producción (sin el primer símbolo)
                alpha.append(produccion[1:])
            else:
                beta.append(produccion)
        return alpha, beta

    def eliminarRI(self, alphas, betas, noTerminal):
        # Vaciamos los elementos del valor (lista)
        self.revisador.gramatica.producciones[noTerminal].clear()
        nuevoNoTerminal = noTerminal + "'"
        self.revisador.gramatica.producciones[nuevoNoTerminal] = []
        for beta in betas:
            # Añadimos betaA' a las producciones del no terminal
            self.revisador.gramatica.producciones[noTerminal].append(beta + [nuevoNoTerminal])
        for alpha in alphas:
            # Añadimos alphaA' a las producciones del nuevo no terminal
            self.revisador.gramatica.producciones[nuevoNoTerminal].append(alpha + [nuevoNoTerminal])
        # Añadimos el vacio
        self.revisador.gramatica.producciones[nuevoNoTerminal].append([self.revisador.gramatica.vacio])
        # Añadimos nuevo ~t a noTerminales
        self.revisador.gramatica.noTerminales.add(nuevoNoTerminal)

    def quitarFactorComun(self):
        cambios = False
        for noTerminal in list(self.revisador.gramatica.producciones.keys()):
            producciones = self.revisador.gramatica.producciones[noTerminal]
            if len(producciones) < 2:
                continue
            # Agrupa producciones por su primer símbolo
            prefijos = {}
            for prod in producciones:
                if len(prod) == 0:
                    continue
                prefijo = prod[0]
                prefijos.setdefault(prefijo, []).append(prod)
            # Busca prefijos comunes (más de una producción con el mismo prefijo)
            for prefijo, prods in prefijos.items():
                if len(prods) > 1:
                    cambios = True
                    nuevoNoTerminal = noTerminal + "_FC"
                    # Quita las producciones con el prefijo común
                    self.revisador.gramatica.producciones[noTerminal] = [
                        p for p in producciones if p[0] != prefijo
                    ]
                    # Añade la nueva producción factorizada
                    self.revisador.gramatica.producciones[noTerminal].append([prefijo, nuevoNoTerminal])
                    # Crea el nuevo no terminal con las producciones sin el prefijo
                    self.revisador.gramatica.producciones[nuevoNoTerminal] = [
                        p[1:] if len(p) > 1 else [self.revisador.gramatica.vacio] for p in prods
                    ]
                    self.revisador.gramatica.noTerminales.add(nuevoNoTerminal)
        return cambios


class ParserLL1:
    def __init__(self, gramatica):
        #Por medio de este atributo podrá acceder a los elementos de la gramatica
        self.gramatica=gramatica
        self.parserTable={}
        self.mandarNoTerminales()

    def mandarNoTerminales(self):
        # Inicializa la tabla
        for noTerminal in self.gramatica.noTerminales:
            self.parserTable[noTerminal] = {}
        # Para cada no terminal y cada producción
        for noTerminal, producciones in self.gramatica.producciones.items():
            for produccion in producciones:
                # Calcula el FIRST de la producción completa
                firsts = self.obtenerFirstDeProduccion(produccion)
                for terminal in firsts - {self.gramatica.vacio}:
                    # Asigna la producción a la celda correspondiente
                    self.parserTable[noTerminal].setdefault(terminal, []).append(produccion)
                # Si el vacío está en el FIRST, agrega la producción en las posiciones de FOLLOW
                if self.gramatica.vacio in firsts:
                    for terminal in self.gramatica.follow[noTerminal]:
                        self.parserTable[noTerminal].setdefault(terminal, []).append(produccion)
    
    def obtenerFirstDeProduccion(self, produccion):
        # Calcula el FIRST de una producción completa (puede ser útil fuera de la clase también)
        resultado = set()
        for simbolo in produccion:
            if simbolo != self.gramatica.vacio:
                simbolo_first = set(self.gramatica.first[simbolo])
                resultado |= simbolo_first - {self.gramatica.vacio}
                if self.gramatica.vacio not in simbolo_first:
                    break
        else:
            resultado.add(self.gramatica.vacio)
        return resultado
    
    def obtener_tabla_parser(self):
        # Obtiene todos los terminales presentes en la tabla
        terminales = set()
        for fila in self.parserTable.values():
            terminales.update(fila.keys())
        terminales = sorted(terminales)
        tabla = []
        for nt in self.parserTable:
            for t in terminales:
                prods = self.parserTable[nt].get(t, [])
                if prods:
                    # Convierte la lista de producciones a string
                    prod_str = ' | '.join([' '.join(prod) for prod in prods])
                    tabla.append({
                        "No terminal": nt,
                        "Terminal": t,
                        "Produccion": prod_str
                    })
        return tabla

    def comprobarLL1(self):
        for noTerminal, fila in self.parserTable.items():
            for terminal, prods in fila.items():
                #Porque basta con que haya uno que tenga varias producciones (es
                #decir, puede ser producido por varias reglas) para que deje de
                #ser una LL1
                if len(prods) != 1:
                    return False
        return True

class LL1:
    def __init__(self,parserLL1):
        self.parserLL1=parserLL1
        #self.esLL1=self.derivarCad()

    #cadena llefga [['int'].['+'],['int],['$']]

    def derivarCad(self, cadena):
        pila = ['$', 'S']
        while len(pila) > 0:
            cima = pila[-1]
            actual = cadena[0] if cadena else None      
            if cima == actual:
                pila.pop()
                cadena.pop(0)
            elif cima in self.parserLL1.gramatica.terminales:
                return False
            elif cima in self.parserLL1.parserTable and actual in self.parserLL1.parserTable[cima]:
                produccion = self.parserLL1.parserTable[cima][actual]
                pila.pop()
                regla = produccion[0]
                if regla != self.parserLL1.gramatica.vacio:
                    for simbolo in reversed(regla):
                        pila.append(simbolo)
            elif cima == self.parserLL1.gramatica.vacio:
                pila.pop()
            else:
                return False
        return cadena == [] and pila == []

#----------------------- SLR---------------------
class parserSLR:
    def __init__(self, gramatica):
        self.gramatica = self._convertir_gramatica(gramatica)
        # Calcula los conjuntos FIRST y FOLLOW antes de crear los estados
        self.gramatica.recorrerProducciones()
        self.gramatica.asignarFirst()
        self.gramatica.calculo_follow()
        self.gramatica_aumentada = self.aumentarGramatica()
        self.estados = []
        self.transiciones = {}
        self.tabla_goto = {}
        self.tabla_action = {}
        self.crear_estados()
        self.imprimir_tablas()
        # self.parsear_cadena()  # Solo llama esto si tienes una cadena de entrada
    
    def _convertir_gramatica(self, gramatica):
            nueva_prods = {}
            for no_terminal, producciones in gramatica.producciones.items():
                nuevas = []
                for prod in producciones:
                    # Convierte 'e' en ('e',) si es string o lista
                    if prod == 'e' or prod == ('e',) or prod == ['e']:
                        nuevas.append(('e',))
                    else:
                        nuevas.append(tuple(prod))  # Asegura que todas sean tuplas
                nueva_prods[no_terminal] = nuevas
            return Gramatica(gramatica.cantNoTerminales, nueva_prods)
    
    def aumentarGramatica(self): # Creamos la nueva producción S' → S 
        producciones_originales = self.gramatica.producciones.copy()
        simbolo_inicio = next(iter(producciones_originales))
        producciones_aumentadas = {"S'": [(simbolo_inicio,)]}
        producciones_aumentadas.update(producciones_originales)
        gramatica_aumentada = Gramatica(     # aqui creamos la nueva gramática con S' como símbolo inicial
            self.gramatica.cantNoTerminales + 1, 
            producciones_aumentadas
        )

        self.simbolo_inicio_aumentado = "S'"
        return gramatica_aumentada   #como no me da la gramtica en si, la imprimimos en el main

    def closure(self, items):
        closure = set(items)
        while True:
            nuevos_items = set()
            for noT, prod in closure:
                if '.' in prod:
                    i = prod.index('.')
                    if i + 1 < len(prod):
                        simbolo_siguiente = prod[i + 1]
                        # Si el símbolo después del punto es un no terminal
                        if simbolo_siguiente in self.gramatica.producciones:
                            for p in self.gramatica.producciones[simbolo_siguiente]:
                                # Preparamos la nueva producción con el punto al inicio
                                # Omitimos epsilon como símbolo si la producción es solo epsilon
                                if p == ('e',) or p == ['e']:
                                    nueva_prod = ('.',)  # Producción vacía con punto
                                else:
                                    nueva_prod = ('.',) + tuple(p)
                                nuevo_item = (simbolo_siguiente, nueva_prod)
                                if nuevo_item not in closure:
                                    nuevos_items.add(nuevo_item)
            if not nuevos_items:
                break
            closure.update(nuevos_items)
        return closure

    def goto(self, items, simbolo):
        nuevos_items = set()
        for noT, prod in items:
            if '.' in prod:
                i = prod.index('.')
                # Verificamos que el símbolo después del punto sea el que buscamos
                if i + 1 < len(prod) and prod[i + 1] == simbolo:
                    # Movemos el punto un lugar a la derecha
                    nueva_prod = list(prod)
                    nueva_prod[i], nueva_prod[i + 1] = nueva_prod[i + 1], nueva_prod[i]
                    nuevos_items.add((noT, tuple(nueva_prod)))
        if nuevos_items:
            return tuple(sorted(self.closure(nuevos_items)))
        else:
            return None

    def estado_id(self, estado):
        for i, e in enumerate(self.estados):
            if e == estado:
                return i
        return None
    
    def imprimir_tablas(self):
        print(" TABLA ACTION:")
        for clave, valor in sorted(self.tabla_action.items()):
            estado, simbolo = clave
            print(f"  ACTION[{estado}, '{simbolo}'] = {valor}")

        print(" TABLA GOTO:")
        for clave, valor in sorted(self.tabla_goto.items()):
            estado, simbolo = clave
            print(f"  GOTO[{estado}, '{simbolo}'] = {valor}")

    
    def crear_estados(self):
        self.estados = []
        self.transiciones = {}
        self.tabla_action = {}
        self.tabla_goto = {}

        i0 = self.closure({("S'", ('.', self.gramatica.simboloInicial))})
        self.estados.append(i0)

        cambios = True
        while cambios:
            cambios = False
            nuevos_estados = []

            for estado in self.estados:
                for simbolo in self.gramatica.terminales | self.gramatica.noTerminales:
                    nuevo_estado = self.goto(estado, simbolo)
                    if nuevo_estado and nuevo_estado not in self.estados and nuevo_estado not in nuevos_estados:
                        self.transiciones[(self.estado_id(estado), simbolo)] = len(self.estados) + len(nuevos_estados)
                        nuevos_estados.append(nuevo_estado)

            if nuevos_estados:
                self.estados.extend(nuevos_estados)
                cambios = True

        #  ACTION y GOTO
        self.es_SLR = True
        conflictos = []

        for i, estado in enumerate(self.estados):
            for lhs, rhs in estado:
                if rhs[-1] == '.':  # REDUCCIÓN o ACEPTACIÓN
                    if lhs == "S'" and rhs == (self.gramatica.simboloInicial, '.'):
                        self.tabla_action[(i, '$')] = 'ACEPTAR'
                    else:
                        for a in self.gramatica.follow[lhs]:
                            clave = (i, a)
                            if clave in self.tabla_action:
                                self.es_SLR = False
                                conflictos.append(clave)
                            self.tabla_action[clave] = ('REDUCIR', lhs, rhs[:-1])
                else:
                    punto = rhs.index('.')
                    if punto + 1 < len(rhs):
                        simbolo = rhs[punto + 1]
                        destino = self.goto(estado, simbolo)
                        if destino and destino in self.estados:
                            j = self.estado_id(destino)
                            if simbolo in self.gramatica.terminales:
                                clave = (i, simbolo)
                                if clave in self.tabla_action:
                                    self.es_SLR = False
                                    conflictos.append(clave)
                                self.tabla_action[clave] = ('SHIFT', j)
                            else:
                                self.tabla_goto[(i, simbolo)] = j

        self.imprimir_tablas()

        if self.es_SLR:
            print(" La gramática es SLR(1).")
        else:
            print(" La gramática NO es SLR(1) por conflictos en:", conflictos)


    def parsear_cadena(self, cadena):
        entrada = list(cadena) + ['$']  # La cadena de entrada + símbolo fin
        pila = [0]  # Pila con estado inicial
        i = 0  # índice en la entrada

        while True:
            estado = pila[-1]
            simbolo = entrada[i]

            accion = self.tabla_action.get((estado, simbolo))

            if accion is None:
                # OMO NO HAY ACCION APRA ESTE SIMOBLO ENTONCES rechazo
                return False

            if accion == 'ACEPTAR':
                return True

            elif accion[0] == 'SHIFT':
                # Desplazar símbolo y estado a la pila
                pila.append(simbolo)
                pila.append(accion[1])
                i += 1

            elif accion[0] == 'REDUCIR':
                lhs, rhs = accion[1], accion[2]
                if rhs != ('e',):
                    # Para producciones normales, sacar 2*|rhs| elementos de la pila
                    for _ in range(2 * len(rhs)):
                        pila.pop()
                # Para epsilon, no se hace pop porque no consume nada

                estado_actual = pila[-1]
                pila.append(lhs)

                goto_estado = self.tabla_goto.get((estado_actual, lhs))
                if goto_estado is None:
                    # No hay transición goto → rechazo
                    return False
                pila.append(goto_estado)

            else:
                # Acción inválida ENTONCES rechazo
                return False


    def probar_cadena(self, cadena):
        if self.parsear_cadena(cadena):
            print("YES: la cadena es válida según la gramática.")
        else:
            print("NO: la cadena fue rechazada por la gramática.")

"""
    def main():

    gramatica= Gramatica(3,{
    'S': [['T', 'E\'']],
    'E\'': [['+', 'T', 'E\''], ['e']],
    'T': [['int']]
    })
    
    Gramatica(4,{
        'S': [['B','l']],
        'B':[['Z'],['e']],
        'Z':[['k'],['e']]
    })

    
    Gramatica(4,{
        'S': [['A', 'C', 'B'], ['C', 'b', 'B'], ['B', 'a']],
        'A': [['d', 'a'], ['B', 'C']],
        'B': [['g'], ['e']],
        'C': [['h'], ['e']]
        })
    
    Gramatica(5,{
    'E': [['T', "E'"]],
    "E'": [['+', 'T', "E'"], ['e']],
    'T': [['F', "T'"]],
    "T'": [['*', 'F', "T'"], ['e']],
    'F': [['(', 'E', ')'], ['id']]
        })
    
    gramatica.imprimirGramatica()
    revisador=RevisadorLL1(gramatica)
    parser = ParserLL1(gramatica)
    ll1=LL1(parser)
    #arreglador=ArregladorLL1(revisador)
    print(f"en main: {revisador.tieneRI}, sus ~T: {revisador.noTerminalesRI}")
    print(f"en main, FC: {revisador.tieneFC}, sus ~T: {revisador.noTerminalesFC}")
    #print(f"se puedo quitar RI? {arreglador.quitarFC}")
    #print(f"nueva gramatuca: {gramatica.imprimirGramatica()}")
    print(f"first de gramatica: {gramatica.first}")
    print(f"follow de gramatica:{gramatica.follow} ")
    print(f"Parser Table: {parser.parserTable}")

    print("--------")
    parser.imprimirParserTable()
    esLL1=parser.comprobarLL1()
    print(esLL1)
    cadena = ['int', '+', 'int', '+', 'int', '$']  #TRUE
    #cadena = ['int', '$'] #TRUE
    #cadena = ['+', 'int', '$'] #FALSE
    result=ll1.derivarCad(cadena)
    print(result)
    
    print("PARTE DE SLR")
    gram =Gramatica(3,{
        "S": [("A", "B")],
        "A": [("a", "A"), ("d")],
        "B": [("b", "B", "c"), ('e')]
    })   #


    item_inicial = {("S´", (".", "S"))}  #ESTOS SI SE PONEN COMO TUPLA PORQUE YA SE ADAPTO DENTRO DE SUS METODOS
    item_testeo = {("S", (".", "A", "B"))}

    gram.recorrerProducciones()
    gram.asignarFirst()
    print("FIRST:", gram.first)
    gram.calculo_follow()
    print("FOLLOW:", gram.follow)
    testeo=parserSLR(gram)
    testeo.probar_cadena("adbc")

    #testear FC
    #arreglador = ArregladorLL1(revisador)
    #arreglador.quitarFactorComun()
    #gramatica.imprimirGramatica()

    testear RI
    arreglador = ArregladorLL1(revisador)
    

if __name__=="__main__":
    main()
    
"""