from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from m import Gramatica, RevisadorLL1, ParserLL1, LL1, ArregladorLL1,parserSLR

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utilidad para convertir producciones de la interfaz a formato de la lógica
def parse_producciones(prods: Dict[str, List[str]]) -> Dict[str, List[List[str]]]:
    """
    Convierte las producciones de la interfaz (dict[str, list[str]]) a dict[str, list[list[str]]]
    Si la producción tiene espacios, se asume que los símbolos están separados por espacio.
    Si no, cada carácter es un símbolo (para compatibilidad con la interfaz actual).
    """
    result = {}
    for nt, alternativas in prods.items():
        result[nt] = []
        for prod in alternativas:
            prod = prod.strip()
            if not prod:
                continue
            # Si los símbolos están separados por espacio, ej: "id + id $"
            if " " in prod:
                symbols = prod.split()
            else:
                # Soporta símbolos como id, E', etc.
                symbols = []
                i = 0
                while i < len(prod):
                    if i+1 < len(prod) and prod[i+1] == "'":
                        symbols.append(prod[i:i+2])
                        i += 2
                    else:
                        symbols.append(prod[i])
                        i += 1
            result[nt].append(symbols)
    return result

# GET para obtener información básica de la gramática
@app.get("/info")
def info():
    return {"status": "API de análisis de gramáticas activa"}

# POST para analizar la gramática y devolver tipo LL1/SLR1
class GramRequest(BaseModel):
    terminales: List[str]
    no_terminales: List[str]
    producciones: Dict[str, List[str]]
    inicio: Optional[str] = None

@app.post("/analizar_gramatica")
def analizar_gramatica(req: GramRequest):
    try:
        prods = parse_producciones(req.producciones)
        gr = Gramatica(len(req.no_terminales), prods)
        revisador = RevisadorLL1(gr)
        tipos_validos = []

        # Primero, revisa RI y FC
        tiene_ri = revisador.analizarRI()
        tiene_fc = revisador.analizarFC()

         # DEPURACIÓN: imprime el símbolo inicial, no terminales y producciones
        print("Simbolo inicial:", getattr(gr, "simboloInicial", None))
        print("No terminales:", getattr(gr, "noTerminales", None))
        print("Producciones:", getattr(gr, "producciones", None))
        print("Follow dict:", getattr(gr, "follow", None))

        # SLR1 se puede calcular siempre
        slr_parser = parserSLR(gr)
        if slr_parser.es_SLR:
            tipos_validos.append("SLR1")

        # LL1 solo si NO hay RI ni FC
        if not tiene_ri and not tiene_fc:
            gr.asignarFirst()
            gr.inicial_follow()
            gr.calculo_follow()
            parser = ParserLL1(gr)
            if parser.comprobarLL1():
                tipos_validos.append("LL1")

        return {
            "tipos_validos": tipos_validos,
            "tiene_ri": tiene_ri,
            "tiene_fc": tiene_fc
        }
    except Exception as e:
        print("ERROR EN analizar_gramatica:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    
# POST para derivar una cadena
class DerivarRequest(GramRequest):
    tipo: str
    cadena: str  # Puede ser "id + id $" o "id+id$"


@app.post("/derivar_cadena")
def derivar_cadena(req: DerivarRequest):
    try:
        prods = parse_producciones(req.producciones)
        gr = Gramatica(len(req.no_terminales), prods)

        cadena = req.cadena.strip()
        if " " in cadena:
            symbols = cadena.split()
        else:
            symbols = []
            i = 0
            while i < len(cadena):
                if i + 1 < len(cadena) and cadena[i + 1] == "'":
                    symbols.append(cadena[i:i + 2])
                    i += 2
                else:
                    symbols.append(cadena[i])
                    i += 1

        if req.tipo == "LL1":
            revisador = RevisadorLL1(gr)
            if revisador.analizarRI() or revisador.analizarFC():
                return JSONResponse(
                    status_code=400,
                    content={"error": "La gramática tiene recursión por izquierda o factor común y no es apta para LL(1)."}
                )
            if not symbols or symbols[-1] != '$':
                symbols.append('$')
            gr.asignarFirst()
            gr.calculo_follow()
            parser = ParserLL1(gr)
            ll1 = LL1(parser)

            #DEPURACION
            print("No terminales:", gr.noTerminales)
            print("Producciones:", gr.producciones)
            print("Tabla LL(1):", parser.parserTable)
            aceptada = ll1.derivarCad(symbols)
            # Retornamos un diccionario con estructura uniforme
            return {
                "resultado": {
                    "cadena": symbols,
                    "aceptada": aceptada
                },
                "tabla_PARSER":parser.obtener_tabla_parser()
                #Imprimimos tabla
            }   #AQUI PONEMOS LO DE LAS TABLAS  COMO en if aceptada: DEL  SLR

        elif req.tipo == "SLR1":
            parser_slr = parserSLR(gr)
            parser_slr.crear_estados()
            aceptada = parser_slr.parsear_cadena(symbols)

            if aceptada:
                return {
                    "resultado": {
                        "cadena": symbols,
                        "aceptada": True
                    },
                    "tabla_ACTION": [
                        {
                            "estado": estado,
                            "simbolo": simbolo,
                            "accion": accion if isinstance(accion, str)
                                      else f"{accion[0]} {accion[1]}" if accion[0] == "SHIFT"
                                      else f"{accion[0]} {accion[1]} → {' '.join(accion[2])}"
                        }
                        for (estado, simbolo), accion in parser_slr.tabla_action.items()
                    ],
                    "tabla_GOTO": [
                        {
                            "estado": estado,
                            "no_terminal": simbolo,
                            "destino": destino
                        }
                        for (estado, simbolo), destino in parser_slr.tabla_goto.items()
                    ]
                }
            else:
                return {
                    "resultado": {
                        "cadena": symbols,
                        "aceptada": False
                    }
                }

        else:
            return JSONResponse(status_code=400, content={"error": "Tipo de parser no soportado"})

    except Exception as e:
        print("ERROR EN derivar_cadena:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


# POST para transformar gramática eliminar RI/FC
class TransformarRequest(GramRequest):
    eliminar_ri: Optional[bool] = False
    eliminar_fc: Optional[bool] = False


@app.post("/transformar_gramatica")
def transformar_gramatica(req: TransformarRequest):
    try:
        prods = parse_producciones(req.producciones)
        gr = Gramatica(len(req.no_terminales), prods)
        revisador = RevisadorLL1(gr)
        arreglador = ArregladorLL1(revisador)
        cambios = {}
        if req.eliminar_ri:
            """
            arreglador.quitarRI  # ejecutar la función para quitar RI ---> NO SE PONEN () da error 
            cambios["ri"] = True  
            """
            resultado_ri = arreglador.administrarArreglos()
            cambios["ri"] = resultado_ri
        if req.eliminar_fc:
            cambios["fc"] = arreglador.quitarFactorComun()
        return {
            "producciones": gr.producciones,
            "no_terminales": list(gr.noTerminales),
            "cambios": cambios
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
