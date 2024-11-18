# app.py
import streamlit as st
import requests
from bs4 import BeautifulSoup
from language_tool_python import LanguageTool
import pandas as pd
import plotly.express as px
import time

class WebContentChecker:
    def __init__(self, language='es'):
        self.language_tool = LanguageTool(language)
    
    def get_web_content(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.decompose()
                
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            raise Exception(f"Error al obtener contenido web: {str(e)}")
    
    def check_text(self, text):
        matches = self.language_tool.check(text)
        return matches
    
    def format_errors(self, matches):
        formatted_errors = []
        for match in matches:
            error = {
                'mensaje': match.message,
                'contexto': match.context,
                'sugerencias': match.replacements if match.replacements else ['Sin sugerencias'],
                'categoria': match.category,
                'offset': match.offset,
                'longitud': match.errorLength
            }
            formatted_errors.append(error)
        return formatted_errors
    
    def analyze_url(self, url):
        try:
            content = self.get_web_content(url)
            matches = self.check_text(content)
            errors = self.format_errors(matches)
            
            return {
                'url': url,
                'total_errores': len(errors),
                'errores': errors,
                'contenido': content
            }
        finally:
            self.language_tool.close()

def create_error_statistics(errors):
    if not errors:
        return pd.DataFrame()
    
    # Crear DataFrame con errores
    df = pd.DataFrame([{'categoria': error['categoria']} for error in errors])
    
    # Contar errores por categoría
    error_counts = df['categoria'].value_counts().reset_index()
    error_counts.columns = ['Categoría', 'Cantidad']
    
    return error_counts

def main():
    st.set_page_config(
        page_title="Spell Checker Web",
        page_icon="📝",
        layout="wide"
    )
    
    st.title("📝 Analizador de Ortografía y Gramática")
    st.write("Analiza la ortografía y gramática de cualquier página web")
    
    # Sidebar para configuración
    st.sidebar.title("⚙️ Configuración")
    language = st.sidebar.selectbox(
        "Selecciona el idioma",
        options=['es', 'en'],
        format_func=lambda x: 'Español' if x == 'es' else 'English'
    )
    
    # Input URL
    url = st.text_input("🌐 Ingresa la URL de la página web", "")
    
    if st.button("🔍 Analizar"):
        if url:
            try:
                with st.spinner('Analizando la página web...'):
                    checker = WebContentChecker(language=language)
                    results = checker.analyze_url(url)
                
                # Mostrar resultados en pestañas
                tab1, tab2, tab3 = st.tabs(["📊 Resumen", "📝 Errores Detallados", "📄 Contenido"])
                
                with tab1:
                    # Métricas principales
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Total de Errores", results['total_errores'])
                    
                    with col2:
                        palabras = len(results['contenido'].split())
                        st.metric("Total de Palabras", palabras)
                    
                    # Gráfico de errores por categoría
                    st.subheader("Distribución de Errores por Categoría")
                    error_stats = create_error_statistics(results['errores'])
                    if not error_stats.empty:
                        fig = px.bar(
                            error_stats,
                            x='Categoría',
                            y='Cantidad',
                            color='Cantidad',
                            color_continuous_scale='Viridis'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No se encontraron errores para mostrar en el gráfico")
                
                with tab2:
                    if results['errores']:
                        for i, error in enumerate(results['errores'], 1):
                            with st.expander(f"Error #{i}: {error['categoria']}", expanded=i==1):
                                st.write("**Mensaje:**", error['mensaje'])
                                st.write("**Contexto:**", error['contexto'])
                                st.write("**Sugerencias:**", ", ".join(error['sugerencias']))
                    else:
                        st.success("¡No se encontraron errores!")
                
                with tab3:
                    st.subheader("Contenido Analizado")
                    st.text_area("Texto extraído de la página web:", 
                               value=results['contenido'], 
                               height=300,
                               disabled=True)
                    
            except Exception as e:
                st.error(f"Error al analizar la URL: {str(e)}")
        else:
            st.warning("Por favor, ingresa una URL para analizar")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>Desarrollado con ❤️ usando Streamlit</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
