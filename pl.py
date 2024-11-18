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
        temperature: float = 0.5,
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

def main():
    st.set_page_config(
        page_title="Adaptador de Filosofía para Jóvenes",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Adaptador de Filosofía para Jóvenes")
    
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
    
    # Configuración del sidebar
    with st.sidebar:
        st.subheader("📚 Opciones de Adaptación")
        
        # Subida de PDF
        uploaded_file = st.file_uploader("Cargar obra filosófica (PDF)", type=['pdf'])
        
        if 'text_loaded' in st.session_state and st.session_state.text_loaded:
            st.success("✅ Texto cargado")
            
            if 'chapter_count' in st.session_state:
                st.write(f"Capítulos identificados: {st.session_state.chapter_count}")
        
        # Botón para reiniciar
        if st.button("🔄 Comenzar Nueva Adaptación"):
            for key in ['messages', 'text_loaded', 'chapter_count', 'text_content']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Mensaje del sistema para el asistente
    SYSTEM_MESSAGE = """Eres un filósofo profesional especializado en adaptar grandes obras de la filosofía a un público juvenil.
    Tu objetivo es hacer que conceptos filosóficos complejos sean accesibles y emocionantes para jóvenes lectores.

    Sigue este proceso:
    1. Primero pide al usuario que suba el archivo PDF con la obra filosófica.
    2. Una vez recibido el texto, analízalo y divídelo en capítulos temáticos.
    3. Presenta al usuario un resumen de los capítulos identificados.
    4. Pide al usuario que especifique qué capítulos quiere que sean adaptados.
    5. Por cada capítulo solicitado, crea una versión adaptada que:
       - Use lenguaje claro y accesible
       - Incluya ejemplos modernos y relevantes
       - Incorpore elementos narrativos atractivos
       - Mantenga la esencia filosófica del texto original
       - Incluya preguntas de reflexión al final

    Si es tu primer mensaje, pide amablemente al usuario que suba el archivo PDF de la obra filosófica que desea adaptar."""
    
    # Inicializar el historial de chat en la sesión
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Procesar PDF si se ha subido
    if uploaded_file is not None and 'text_loaded' not in st.session_state:
        with st.spinner("Procesando el texto..."):
            text_content = extract_text_from_pdf(uploaded_file)
            st.session_state.text_content = text_content
            st.session_state.text_loaded = True
            st.rerun()
    
    # Mostrar mensajes del chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Input del usuario
    if prompt := st.chat_input("Escribe tu mensaje..."):
        # Agregar mensaje del usuario al historial
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Preparar mensajes para la API
        api_messages = [
            {"role": "system", "content": SYSTEM_MESSAGE}
        ] + st.session_state.messages
        
        # Si hay texto cargado, incluirlo en el contexto
        if 'text_content' in st.session_state:
            api_messages.append({
                "role": "system",
                "content": f"Este es el texto de la obra filosófica:\n\n{st.session_state.text_content}"
            })
        
        # Realizar llamada a la API
        with st.chat_message("assistant"):
            with st.spinner("Analizando..."):
                try:
                    response = xai_client.chat_completion(
                        messages=api_messages,
                        model=model,
                        temperature=0.5
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

if __name__ == "__main__":
    main()
