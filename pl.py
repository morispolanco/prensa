import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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

# Mapeo de secciones a sus URLs correspondientes
secciones_urls = {
    "Nacional": "https://www.prensalibre.com/nacional/",
    "Internacional": "https://www.prensalibre.com/internacional/",
    "Economía": "https://www.prensalibre.com/economia/",
    "Deportes": "https://www.prensalibre.com/deportes/",
    "Cultura": "https://www.prensalibre.com/cultura/",
    "Opinión": "https://www.prensalibre.com/opinion/",
    "Tecnología": "https://www.prensalibre.com/tecnologia/",
    "Salud": "https://www.prensalibre.com/salud/",
    "Educación": "https://www.prensalibre.com/educacion/",
    "Otros": "https://www.prensalibre.com/"
}

# Función para obtener el contenido de la sección
def obtener_contenido(seccion):
    url = secciones_urls.get(seccion)
    if not url:
        st.error(f"La sección '{seccion}' no tiene una URL mapeada.")
        return None

    st.write(f"Accediendo a la URL: {url}")  # Mensaje de depuración

    # Añadir encabezados para simular un navegador real
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/90.0.4430.93 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            st.error(f"No se pudo obtener el contenido de la sección {seccion}. (Estado: {response.status_code})")
            return None
        soup = BeautifulSoup(response.text, 'html.parser')

        # **Importante**: Actualiza estos selectores según la estructura actual de PrensaLibre.com
        # Después de inspeccionar la página, ajusta los selectores a continuación

        # Ejemplo de selector: <h2 class="headline">
        articulos = soup.find_all('h2', class_='headline')  # Actualiza según la inspección

        if not articulos:
            st.warning("No se encontraron artículos con el selector especificado. Verifica los selectores en el código.")
            return None

        texto_completo = ""
        enlaces_encontrados = []  # Para depuración

        for articulo in articulos[:5]:  # Limitar a los primeros 5 artículos para ejemplo
            enlace_tag = articulo.find('a')
            if not enlace_tag or not enlace_tag.get('href'):
                st.warning("Un artículo no contiene un enlace válido.")
                continue
            enlace = enlace_tag['href']
            enlace_completo = urljoin(url, enlace)
            enlaces_encontrados.append(enlace_completo)

            resp_art = requests.get(enlace_completo, headers=headers)
            if resp_art.status_code == 200:
                soup_art = BeautifulSoup(resp_art.text, 'html.parser')
                parrafos = soup_art.find_all('p')
                for p in parrafos:
                    texto_completo += p.get_text() + "\n"
            else:
                st.warning(f"No se pudo acceder al artículo: {enlace_completo} (Estado: {resp_art.status_code})")

        if st.checkbox("Mostrar enlaces extraídos"):
            st.write("**Enlaces encontrados:**")
            for enlace in enlaces_encontrados:
                st.write(enlace)

        if st.checkbox("Mostrar HTML bruto de la sección"):
            st.write("**HTML de la sección:**")
            st.write(soup.prettify())

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
seccion_seleccionada = st.sidebar.selectbox("Secciones", list(secciones_urls.keys()))

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
