# app.py
import streamlit as st
import requests
import json
from typing import Dict, Any

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
        """
        Realiza una llamada a la API de chat completions
        """
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
    
    # Configuración del chat
    with st.sidebar:
        st.subheader("⚙️ Configuración")
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
        system_message = st.text_area(
            "Mensaje del sistema",
            value="You are a test assistant.",
            height=100
        )
    
    # Inicializar el historial de chat en la sesión
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
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
        st.rerun()

if __name__ == "__main__":
    main()
