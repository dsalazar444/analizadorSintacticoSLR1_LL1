import streamlit as st
import requests  # para llamadas API
import json
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Analizador Sintáctico", layout="wide")

# Fondo de video y estilos
st.markdown("""
    <style>
        .stApp { background: transparent; }
        body {
            background: black;
            overflow-x: hidden;
        }
        .bg-video {
            position: fixed;
            top: 0; left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
        }
        .content {
            position: relative;
            z-index: 2;
            color: white;
        }
        .input-block {
            background-color: rgba(20, 20, 20, 0.7);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
    </style>

    <iframe class="bg-video"
        src="https://www.youtube.com/embed/hvUxFK9ZMog?autoplay=1&mute=1&controls=0&loop=1&playlist=hvUxFK9ZMog"
        frameborder="0"
        allow="autoplay; fullscreen">
    </iframe>
""", unsafe_allow_html=True)


def pedir_producciones(label_num, key_prefix):
    with st.container():
        st.markdown("<div class='content input-block'>", unsafe_allow_html=True)

        if f"{key_prefix}_confirmed" not in st.session_state:
            st.session_state[f"{key_prefix}_confirmed"] = False
        if f"{key_prefix}_count" not in st.session_state:
            st.session_state[f"{key_prefix}_count"] = 0

        if not st.session_state[f"{key_prefix}_confirmed"]:
            num = st.number_input(label_num, min_value=1, step=1, key=f"{key_prefix}_input")
            if st.button("Enviar", key=f"{key_prefix}_btn"):
                st.session_state[f"{key_prefix}_count"] = num
                st.session_state[f"{key_prefix}_confirmed"] = True
                st.session_state[f"{key_prefix}_prods"] = [""] * num

        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state[f"{key_prefix}_confirmed"]:
        st.markdown("<div class='content'>", unsafe_allow_html=True)

        for i in range(st.session_state[f"{key_prefix}_count"]):
            st.session_state[f"{key_prefix}_prods"][i] = st.text_input(
                f"Ingresa tu producción número {i+1}:", key=f"{key_prefix}_prod_{i+1}"
            )

        return True  # indica que ya están listas las producciones

    return False

# Helper para construir el objeto gramatica según estructura que espera tu lógica
def construir_gramatica_de_inputs(producciones_str_list):
    # Suponemos que la producción es tipo "A -> aB | c"
    # Parseamos para obtener:
    # terminales, no_terminales, producciones dict, inicio
    # Aquí debes ajustar según tu formato exacto y tu lógica
    no_terminales = set()
    terminales = set()
    producciones = dict()

    for prod in producciones_str_list:
        if "->" not in prod:
            continue
        nt, rhs = prod.split("->")
        nt = nt.strip()
        no_terminales.add(nt)
        rhs_alternativas = [r.strip() for r in rhs.split()] #ACA
        producciones.setdefault(nt, [])
        for alt in rhs_alternativas:
            producciones[nt].append(alt)
            # Detectar terminales (simplificado: todo char que no sea mayuscula y no sea epsilon)
            for c in alt:
                if not c.isupper() and c != "e":
                    terminales.add(c)

    if len(no_terminales) == 0:
        st.error("No se detectaron no terminales válidos.")
        return None

    inicio = list(no_terminales)[0]  # asumimos el primero como inicio

    return {
        "terminales": list(terminales),
        "no_terminales": list(no_terminales),
        "producciones": producciones,
        "inicio": inicio
    }


# ------------------------- TAB 1 t od o  LO DE LL Y SLR ------------------------
tab1, tab2 = st.tabs(["Inicio", "Eliminar RI/FC"])

with tab1:
    st.markdown("<h1 class='content'>Analizador Sintáctico</h1>", unsafe_allow_html=True)

    listo = pedir_producciones("Número de producciones", "tab1")

    if listo:
        gramatica_obj = construir_gramatica_de_inputs(st.session_state["tab1_prods"])

        if gramatica_obj:
            if st.button("Verificar tipo de gramática"):
                try:
                    response = requests.post("http://localhost:8000/analizar_gramatica", json=gramatica_obj)
                    tipos_validos = response.json()["tipos_validos"]
                except Exception as e:
                    st.error(f"Error al conectar con la API: {e}")
                    tipos_validos = []

                if not tipos_validos:
                    st.error("La gramática no es LL(1) ni SLR(1).")
                else:
                    st.success(f"La gramática es de tipo(s): {', '.join(tipos_validos)}")

                    # Guardar tipos válidos en sesión para usarlos al derivar
                    st.session_state["tipos_validos"] = tipos_validos
                    st.session_state["gramatica_obj"] = gramatica_obj

    # Si ya tenemos tipos válidos, dejamos elegir el tipo para derivar y poner la cadena
    if "tipos_validos" in st.session_state and st.session_state["tipos_validos"]:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h3 class='content'>Elige con qué tipo quieres derivar</h3>", unsafe_allow_html=True)
        tipo_derivacion = st.radio("Selecciona el tipo de gramática para derivar:", st.session_state["tipos_validos"])

        cadena = st.text_input("Ingresa la cadena a derivar:")

        if st.button("Derivar cadena"):
            if not cadena:
                st.error("Debes ingresar una cadena para derivar.")
            else:
                try:
                    data = st.session_state["gramatica_obj"].copy()
                    data.update({"tipo": tipo_derivacion, "cadena": cadena})
                    response = requests.post("http://localhost:8000/derivar_cadena", json=data)
                    resultado = response.json()

                    if tipo_derivacion == "SLR1" and resultado.get("resultado", {}).get("aceptada"):
                        st.success("La cadena fue aceptada por la gramática SLR(1).")

                        st.markdown("### Tabla ACTION")
                        tabla_action = resultado.get("tabla_ACTION", [])
                        if tabla_action:
                           # AQUI USAMAS PANDA
                            df_action = pd.DataFrame(tabla_action)
                            st.dataframe(df_action)
                        else:
                            st.info("No se encontró tabla ACTION.")

                        st.markdown("### Tabla GOTO")
                        tabla_goto = resultado.get("tabla_GOTO", [])
                        if tabla_goto:
                            df_goto = pd.DataFrame(tabla_goto)
                            st.dataframe(df_goto)
                        else:
                            st.info("No se encontró tabla GOTO.")

                    else:
                        # Código actual que tienes para mostrar mensajes simples
                        aceptada = resultado.get("resultado", {}).get("aceptada", False)
                        if aceptada:
                            st.success("La cadena se puede derivar de la gramática.")
                        else:
                            st.error("No es posible derivar esa cadena de la gramática.")
                        
                        # --- AGREGADO: Mostrar tabla LL(1) ---
                        if tipo_derivacion == "LL1":
                            tabla_parser = resultado.get("tabla_PARSER", [])
                            if tabla_parser:
                                st.markdown("### Tabla PARSER")
                                df_parser = pd.DataFrame(tabla_parser)
                                st.dataframe(df_parser)
                            else:
                                st.info("No se encontró tabla LL(1) (PARSER).")
                except Exception as e:
                    st.error(f"Error al derivar la cadena: {e}")








# ------------------------- TAB 2  todo lo de eliminar cosas ------------------------
with tab2:
    st.markdown("<h1 class='content'>Eliminar recursión por izquierda y/o factor común</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        tiene_ri = st.checkbox("Tiene RI", key="ri")
    with col2:
        tiene_fc = st.checkbox("Tiene FC", key="fc")

    listo2 = pedir_producciones("Número de no terminales", "tab2")

    if listo2:
        gramatica_obj = construir_gramatica_de_inputs(st.session_state["tab2_prods"])

        if gramatica_obj is not None:
            # Guardar la gramática en session_state para usarla luego
            st.session_state["gramatica_tab2"] = gramatica_obj

        if st.button("Transformar gramática"):
            if not tiene_ri and not tiene_fc:
                st.warning("Debes seleccionar al menos una transformación: RI o FC.")
            else:
                try:
                    # Obtener la gramática ingresada
                    gram = st.session_state[f"gramatica_tab2"]

                    payload = {
                        "terminales": gram["terminales"],
                        "no_terminales": gram["no_terminales"],
                        "producciones": gram["producciones"],
                        "inicio": gram.get("inicio", None),
                        "eliminar_ri": tiene_ri,
                        "eliminar_fc": tiene_fc
                    }

                    response = requests.post("http://localhost:8000/transformar_gramatica", json=payload)  #uso de la API

                    if response.status_code == 200:
                        data = response.json()

                        st.success("✅ Gramática transformada correctamente.")
                        st.markdown("### Nuevas producciones:")
                        for nt, prods in data["producciones"].items():
                            for p in prods:
                                st.text(f"{nt} -> {' '.join(p)}")

                        st.markdown("### Nuevos y antiguos no terminales:")
                        st.write(data["no_terminales"])

                    else:
                        st.error(f"Error al transformar la gramática: {response.json().get('error')}")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")