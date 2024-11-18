# app.py
import streamlit as st
import requests
import json
from typing import Dict, Any
import PyPDF2
import io

class XAIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def chat_completion(
        self,
        messages: list,
        model: str = "grok-beta",
        temperature: float = 0,
        stream: bool = False
    ) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/chat/completions"
        
        payload = {
            "messages": messages,
            "model": model,
            "stream": stream,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error en la llamada a la API: {str(e)}")

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def get_system_message(option: str, pdf_text: str = "") -> str:
    system_messages = {
        "Revisar ortografía y gramática": f"""Analiza el siguiente texto y revisa su ortografía y gramática. 
        Proporciona correcciones detalladas y sugerencias de mejora.
        
        Texto del PDF:
        {pdf_text}""",
        
        "Hacer un resumen": f"""Genera un resumen conciso y coherente del siguiente texto, 
        destacando los puntos principales y las ideas clave.
        
        Texto del PDF:
        {pdf_text}""",
        
        "Chatear con el PDF": f"""Actúa como un asistente experto que ha leído y comprende 
        completamente el siguiente documento. Responde preguntas sobre su contenido 
        de manera precisa y detallada.
        
        Contenido del documento:
        {pdf_text}"""
    }
    return system_messages.get(option, "You are a helpful assistant.")

def main():
    st.set_page_config(
        page_title="X.AI Chat Interface",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 X.AI Chat Interface")
    
    # Verificar que la API key está configurada
    if 'xai_api_key' not in st.secrets:
        st.error("""
        ⚠️ No se encontró la API key en los secrets.
        
        Por favor, configura el archivo .streamlit/secrets.toml con:
        ```toml
        xai_api_key = "tu-api-key"
        ```
        """)
        return
    
    # Inicializar el cliente
    xai_client = XAIClient(st.secrets['xai_api_key'])
    
    # Configuración del chat y carga de PDF
    with st.sidebar:
        st.subheader("⚙️ Configuración")
        
        # Subida de PDF
        uploaded_file = st.file_uploader("Cargar PDF", type=['pdf'])
        
        # Menú de opciones del sistema
        system_options = [
            "Revisar ortografía y gramática",
            "Hacer un resumen",
            "Chatear con el PDF"
        ]
        selected_option = st.selectbox(
            "Selecciona una opción",
            ["Chat general"] + system_options,
            index=0
        )
        
        model = st.selectbox(
            "Modelo",
            ["grok-beta"],
            index=0
        )
        temperature = st.slider(
            "Temperatura",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1
        )
    
    # Procesar PDF si se ha subido
    if uploaded_file is not None:
        pdf_text = extract_text_from_pdf(uploaded_file)
        if 'pdf_text' not in st.session_state:
            st.session_state.pdf_text = pdf_text
            st.success("PDF cargado exitosamente!")
    
    # Inicializar el historial de chat en la sesión
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Mostrar mensajes del chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Input del usuario
    if prompt := st.chat_input("Escribe tu mensaje..."):
        # Verificar si se necesita PDF para la opción seleccionada
        if selected_option in system_options and 'pdf_text' not in st.session_state:
            st.error("Por favor, carga un PDF primero para usar esta opción.")
            return
        
        # Agregar mensaje del usuario al historial
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Preparar mensajes para la API
        system_message = get_system_message(
            selected_option,
            st.session_state.get('pdf_text', '')
        )
        
        api_messages = [
            {"role": "system", "content": system_message}
        ] + st.session_state.messages
        
        # Realizar llamada a la API
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    response = xai_client.chat_completion(
                        messages=api_messages,
                        model=model,
                        temperature=temperature
                    )
                    
                    assistant_message = response["choices"][0]["message"]["content"]
                    st.write(assistant_message)
                    
                    # Agregar respuesta al historial
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Botón para limpiar el chat
    if st.sidebar.button("🧹 Limpiar Chat"):
        st.session_state.messages = []
        if 'pdf_text' in st.session_state:
            del st.session_state.pdf_text
        st.rerun()

if __name__ == "__main__":
    main()
