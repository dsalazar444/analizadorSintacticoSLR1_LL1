# analizadorSintacticoSLR1_LL1

## Integrants:

Daniela Salazar Amaya y Laura Indabur García

## Requirements: This code was run in:

- Operating sistem: Windows
- Proggraming language: Python 3.12.7
- Tools used: FastAPI and Streamlit frameworks

## How to run it:

To run the code, you need to install FastAPI and Streamlit. You can do this in your command prompt using the following commands:


```bash
#Install fastAPI and Uvicorn:
pip install fastapi uvicorn

#Install Streamlit
pip install streamlit
```
Once you have both frameworks installed, navigate to the folder where your code is located:


```bash
cd project_location
```
Run this command:


```bash
uvicorn api:app --reload
```
Then, in another command prompt window (in the same folder), run:

```bash
streamlit run interfaz.py
```

To stop either program, press Control + C.
