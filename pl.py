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
        temperature: float = 0.7,  # Aumentado para más creatividad
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

def main():
    st.set_page_config(
        page_title="Escritor de Novelas Juveniles",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 Escritor de Novelas Juveniles")
    
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
    
    # Configuración del chat
    with st.sidebar:
        st.subheader("📖 Tu Novela")
        if 'chapter_count' not in st.session_state:
            st.session_state.chapter_count = 0
            
        st.write(f"Capítulos escritos: {st.session_state.chapter_count}")
        
        # Configuración del modelo
        model = st.selectbox(
            "Modelo",
            ["grok-beta"],
            index=0
        )
        
        if st.button("🔄 Empezar Nueva Novela"):
            st.session_state.messages = []
            st.session_state.chapter_count = 0
            st.rerun()
    
    # Mensaje del sistema para el asistente escritor
    SYSTEM_MESSAGE = """Eres un escritor experto de novelas juveniles. Me ayudarás a escribir una novela juvenil de aventuras.
    Para ello, escribirás un capítulo a la vez y luego propondrás 3 opciones diferentes y emocionantes para el siguiente capítulo.
    
    Sigue estas reglas:
    1. Si es el primer mensaje, preséntate y pide detalles sobre el protagonista y el tipo de aventura que queremos crear.
    2. Cuando escribas un capítulo, hazlo de forma emocionante y detallada, con diálogos y descripciones vívidas.
    3. Después de cada capítulo, propón 3 opciones diferentes para continuar la historia.
    4. Si el usuario escribe "capítulo final", escribe un final épico y satisfactorio para la historia.
    5. Mantén un tono apropiado para el público juvenil.
    6. Los capítulos deben tener una longitud moderada (aproximadamente 500-800 palabras).
    
    Cuando presentes las opciones, hazlo así:
    OPCIONES PARA EL SIGUIENTE CAPÍTULO:
    A) [Primera opción emocionante]
    B) [Segunda opción intrigante]
    C) [Tercera opción sorprendente]
    
    Elige una opción escribiendo A, B o C, o escribe "capítulo final" si quieres terminar la historia."""
    
    # Inicializar el historial de chat en la sesión
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Mostrar mensajes del chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Input del usuario
    if prompt := st.chat_input("Escribe tu mensaje o elección..."):
        # Agregar mensaje del usuario al historial
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Preparar mensajes para la API
        api_messages = [
            {"role": "system", "content": SYSTEM_MESSAGE}
        ] + st.session_state.messages
        
        # Realizar llamada a la API
        with st.chat_message("assistant"):
            with st.spinner("Escribiendo..."):
                try:
                    response = xai_client.chat_completion(
                        messages=api_messages,
                        model=model,
                        temperature=0.7
                    )
                    
                    assistant_message = response["choices"][0]["message"]["content"]
                    st.write(assistant_message)
                    
                    # Agregar respuesta al historial
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    
                    # Incrementar contador de capítulos si se detecta un nuevo capítulo
                    if any(keyword in prompt.lower() for keyword in ['a)', 'b)', 'c)', 'capítulo']):
                        st.session_state.chapter_count += 1
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
