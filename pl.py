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

# Definir los selectores en un diccionario para facilitar futuras actualizaciones
selectores = {
    'lista_articulos': {'tag': 'h2', 'class': 'ArticleListing__title'},  # Selector de titulares
    'contenido_articulo': {'tag': 'div', 'class': 'ArticleBody'},        # Selector del contenido del artículo
}

# Función para obtener el contenido de la sección
def obtener_contenido(seccion):
    url = secciones_urls.get(seccion)
    if not url:
        st.error(f"La sección '{seccion}' no tiene una URL mapeada.")
        return None

    st.write(f"🔍 Accediendo a la URL: {url}")  # Mensaje de depuración

    try:
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"No se pudo obtener el contenido de la sección {seccion}. (Estado: {response.status_code})")
            return None
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extraer artículos usando los selectores definidos
        articulos = soup.find_all(selectores['lista_articulos']['tag'], class_=selectores['lista_articulos']['class'])

        if not articulos:
            st.warning("⚠️ No se encontraron artículos con el selector especificado. Verifica los selectores en el código.")
            # Mostrar HTML para depuración
            if st.checkbox("Mostrar HTML de la sección para depuración"):
                st.code(soup.prettify(), language='html')
            return None

        texto_completo = ""
        enlaces_encontrados = []  # Para depuración

        for articulo in articulos[:5]:  # Limitar a los primeros 5 artículos para ejemplo
            enlace_tag = articulo.find('a')
            if enlace_tag and 'href' in enlace_tag.attrs:
                enlace = enlace_tag['href']
                enlace_completo = urljoin(url, enlace)
                enlaces_encontrados.append(enlace_completo)

                resp_art = requests.get(enlace_completo)
                if resp_art.status_code == 200:
                    soup_art = BeautifulSoup(resp_art.text, 'html.parser')
                    # Ajustar el selector del contenido del artículo
                    contenido_articulo = soup_art.find(selectores['contenido_articulo']['tag'], class_=selectores['contenido_articulo']['class'])
                    if contenido_articulo:
                        parrafos = contenido_articulo.find_all('p')
                        for p in parrafos:
                            texto_completo += p.get_text() + "\n"
                    else:
                        st.warning(f"⚠️ No se pudo extraer el contenido del artículo: {enlace_completo}")
                else:
                    st.warning(f"⚠️ No se pudo acceder al artículo: {enlace_completo} (Estado: {resp_art.status_code})")
            else:
                st.warning("⚠️ No se encontró el enlace en el artículo.")

        # Opcional: Mostrar enlaces extraídos
        if st.checkbox("🔗 Mostrar enlaces extraídos"):
            st.write("**Enlaces encontrados:**")
            for enlace in enlaces_encontrados:
                st.markdown(f"- [{enlace}]({enlace})")

        if not texto_completo:
            st.warning("⚠️ No se encontró contenido para analizar.")
        return texto_completo
    except Exception as e:
        st.error(f"❌ Error al obtener el contenido: {e}")
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
            st.error(f"❌ Error en la API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"❌ Error al conectar con la API: {e}")
        return None

# Interfaz de usuario
st.sidebar.header("📂 Seleccione una sección")
seccion_seleccionada = st.sidebar.selectbox("Secciones", list(secciones_urls.keys()))

if st.sidebar.button("🔍 Analizar"):
    with st.spinner("📥 Obteniendo contenido..."):
        contenido = obtener_contenido(seccion_seleccionada)
    if contenido:
        st.subheader(f"📑 Contenido de la sección: {seccion_seleccionada}")
        st.text_area("📝 Texto a analizar", contenido, height=300)

        if st.button("✅ Revisar Ortografía y Gramática"):
            with st.spinner("🔄 Analizando texto..."):
                informe = analizar_texto(contenido)
            if informe:
                st.subheader("📄 Informe de Revisión")
                st.write(informe)
