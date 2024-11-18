import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Configuración de la página
st.set_page_config(
    page_title="📝 Revisor de PrensaLibre",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📝 Revisor de Ortografía y Gramática para PrensaLibre.com")

# Obtener la clave de API desde los secretos de Streamlit
API_KEY = st.secrets["api"]["key"]
API_URL = "https://api.x.ai/v1/chat/completions"

# Definir los selectores en un diccionario para facilitar futuras actualizaciones
selectores = {
    'contenido_articulo': {'tag': 'div', 'class': 'ArticleBody'},  # Selector del contenido del artículo
    # Puedes añadir más selectores si es necesario
}

def es_url_prensalibre(url):
    """
    Verifica si la URL pertenece a PrensaLibre.com
    """
    try:
        parsed_url = urlparse(url)
        return "prensalibre.com" in parsed_url.netloc
    except:
        return False

def obtener_contenido_articulo(url):
    """
    Extrae el contenido textual de un artículo dado su URL.
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            st.error(f"No se pudo acceder a la URL proporcionada. (Estado: {response.status_code})")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extraer el contenido del artículo usando el selector definido
        contenido_articulo = soup.find(selectores['contenido_articulo']['tag'], class_=selectores['contenido_articulo']['class'])
        if not contenido_articulo:
            st.error("⚠️ No se pudo encontrar el contenido del artículo con los selectores especificados.")
            # Opcional: Mostrar HTML para depuración
            if st.checkbox("📄 Mostrar HTML para depuración"):
                st.code(soup.prettify(), language='html')
            return None

        # Extraer todos los párrafos del contenido del artículo
        parrafos = contenido_articulo.find_all('p')
        texto_completo = "\n".join([p.get_text() for p in parrafos])

        if not texto_completo.strip():
            st.warning("⚠️ El artículo no contiene texto para analizar.")
            return None

        return texto_completo

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error en la solicitud HTTP: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Error al procesar el contenido del artículo: {e}")
        return None

def analizar_texto(texto):
    """
    Envía el texto a la API de X para su análisis de ortografía y gramática.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    data = {
        "messages": [
            {
                "role": "system",
                "content": "You are a grammar and spelling assistant."
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
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            st.error(f"❌ Error en la API: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error en la solicitud a la API: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Error al procesar la respuesta de la API: {e}")
        return None

# Interfaz de usuario
st.sidebar.header("📂 Analizar Artículo")
url_usuario = st.sidebar.text_input("🔗 Pega la URL de un artículo de PrensaLibre.com", "")

if st.sidebar.button("🔍 Analizar Artículo"):
    if not url_usuario:
        st.sidebar.warning("⚠️ Por favor, pega una URL para analizar.")
    elif not es_url_prensalibre(url_usuario):
        st.sidebar.error("❌ La URL proporcionada no pertenece a PrensaLibre.com.")
    else:
        with st.spinner("📥 Obteniendo contenido del artículo..."):
            contenido = obtener_contenido_articulo(url_usuario)
        if contenido:
            st.subheader("📑 Contenido del Artículo")
            st.text_area("📝 Texto a analizar", contenido, height=300)

            if st.button("✅ Revisar Ortografía y Gramática"):
                with st.spinner("🔄 Analizando texto..."):
                    informe = analizar_texto(contenido)
                if informe:
                    st.subheader("📄 Informe de Revisión")
                    st.write(informe)
