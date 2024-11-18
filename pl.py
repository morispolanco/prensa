import streamlit as st
import requests
from bs4 import BeautifulSoup

# Configuración de la página
st.set_page_config(
    page_title="Revisor de PrensaLibre",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📝 Revisor de Ortografía y Gramática para PrensaLibre.com")

# Obtener la clave de API desde los secretos de Streamlit
API_KEY = st.secrets["api"]["key"]
API_URL = "https://api.x.ai/v1/chat/completions"

# Definir las secciones del periódico
secciones = [
    "Nacional",
    "Internacional",
    "Economía",
    "Deportes",
    "Cultura",
    "Opinión",
    "Tecnología",
    "Salud",
    "Educación",
    "Otros"
]

# Función para obtener el contenido de la sección
def obtener_contenido(seccion):
    url = f"https://www.prensalibre.com/{seccion.lower()}/"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"No se pudo obtener el contenido de la sección {seccion}.")
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        articulos = soup.find_all('div', class_='headline')  # Ajustar según la estructura real
        texto_completo = ""
        for articulo in articulos[:5]:  # Limitar a los primeros 5 artículos para ejemplo
            enlace = articulo.find('a')['href']
            resp_art = requests.get(enlace)
            if resp_art.status_code == 200:
                soup_art = BeautifulSoup(resp_art.text, 'html.parser')
                parrafos = soup_art.find_all('p')
                for p in parrafos:
                    texto_completo += p.get_text() + "\n"
        if not texto_completo:
            st.warning("No se encontró contenido para analizar.")
        return texto_completo
    except Exception as e:
        st.error(f"Error al obtener el contenido: {e}")
        return None

# Función para analizar el texto usando la API de X
def analizar_texto(texto):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    data = {
        "messages": [
            {
                "role": "system",
                "content": "You are a test assistant."
            },
            {
                "role": "user",
                "content": f"Revisa el siguiente texto en español y proporciona un informe detallado de los errores ortográficos y gramaticales, así como sugerencias de mejora:\n\n{texto}"
            }
        ],
        "model": "grok-beta",          # Modelo especificado
        "stream": False,               # Streaming deshabilitado
        "temperature": 0               # Temperatura configurada a 0
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            st.error(f"Error en la API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error al conectar con la API: {e}")
        return None

# Interfaz de usuario
st.sidebar.header("Seleccione una sección")
seccion_seleccionada = st.sidebar.selectbox("Secciones", secciones)

if st.sidebar.button("Analizar"):
    with st.spinner("Obteniendo contenido..."):
        contenido = obtener_contenido(seccion_seleccionada)
    if contenido:
        st.subheader(f"Contenido de la sección: {seccion_seleccionada}")
        st.text_area("Texto a analizar", contenido, height=300)

        if st.button("Revisar Ortografía y Gramática"):
            with st.spinner("Analizando texto..."):
                informe = analizar_texto(contenido)
            if informe:
                st.subheader("Informe de Revisión")
                st.write(informe)
