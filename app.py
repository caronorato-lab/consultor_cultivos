import streamlit as st
import pandas as pd

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
# Esto tiene que ir de primerito. Le da el título a la pestaña del navegador y la pone ancha.
st.set_page_config(
    page_title="Chismoso Agrícola",
    page_icon="🚜",
    layout="wide"
)

# ==========================================
# FUNCIONES CACHEADAS (EL MOTOR TURBO)
# ==========================================
# El decorador @st.cache_data es la vida. Evita que el servidor lea el Excel
# cada vez que el usuario respira o cambia un filtro.
@st.cache_data
def cargar_datos(archivo):
    # Ya no necesitamos el try/except gigante del script original porque 
    # Streamlit maneja las excepciones en la interfaz de forma más limpia.
    df = pd.read_excel(archivo)
    
    # --- LIMPIEZA PREVENTIVA ---
    # Lo mismo que tenías: mayúsculas y sin espacios para evitar líos
    df['Depto_Buscador'] = df['Departamento'].astype(str).str.upper().str.strip()
    df['Cultivo_Buscador'] = df['Cultivo'].astype(str).str.upper().str.strip()
    return df

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
def main():
    # Título sabroso
    st.title("🚜 EL CHISMOSO AGRÍCOLA COLOMBIANO 🚜")
    st.markdown("Bienvenido al lugar donde los datos del campo no se pueden esconder. Filtra y chismosea a gusto.")
    
    # Intentamos cargar el archivo local que subiste a GitHub
    nombre_archivo = '20250617_BaseAgricola20192024.xlsx'
    
    try:
        # Mostramos un spinner mientras lee el bodoque de datos la primera vez
        with st.spinner('Cargando la base de datos... Dale un ratico, que esto pesa...'):
            df = cargar_datos(nombre_archivo)
            archivo_cargado = True
    except FileNotFoundError:
        # Si no lo encuentra (por ej. si GitHub bloqueó el archivo por pesado)
        st.warning(f"🚨 ¡Paila! No encontré el archivo '{nombre_archivo}' en el servidor.")
        st.info("Pero tranqui, puedes subirlo manualmente aquí abajo:")
        archivo_subido = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])
        
        if archivo_subido is not None:
            with st.spinner('Procesando el archivo que acabas de subir...'):
                df = cargar_datos(archivo_subido)
                archivo_cargado = True
        else:
            archivo_cargado = False
            st.stop() # Detenemos la app hasta que haya datos

    if archivo_cargado:
        # Si llegamos aquí, tenemos datos. ¡A jugar!
        
        # Sacamos departamentos únicos
        deptos_unicos = sorted(df['Depto_Buscador'].dropna().unique())
        
        # --- BARRA LATERAL (SIDEBAR) ---
        st.sidebar.header("🔍 Filtros de Búsqueda")
        
        # 1. Selector de Departamento
        depto_elegido = st.sidebar.selectbox(
            "1. Elige el Departamento:", 
            options=deptos_unicos,
            index=0 # Por defecto agarra el primero
        )
        
        # Filtramos la base solo para el departamento elegido
        df_depto = df[df['Depto_Buscador'] == depto_elegido]
        cultivos_unicos = sorted(df_depto['Cultivo_Buscador'].dropna().unique())
        
        # 2. Selector de Cultivo (Se actualiza dinámicamente según el depto)
        cultivo_elegido = st.sidebar.selectbox(
            f"2. ¿Qué buscas en {depto_elegido}?", 
            options=cultivos_unicos
        )

        # Recuperamos los nombres bonitos originales
        nombre_bonito_cultivo = df_depto[df_depto['Cultivo_Buscador'] == cultivo_elegido]['Cultivo'].iloc[0]
        nombre_bonito_depto = df_depto['Departamento'].iloc[0]

        # --- PROCESAMIENTO DE DATOS ---
        df_final = df_depto[df_depto['Cultivo_Buscador'] == cultivo_elegido].copy()

        cols_numericas = ['Área sembrada (ha)', 'Área cosechada (ha)', 'Producción (t)']
        for col in cols_numericas:
            df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)

        # Agrupamos por Año
        resumen = df_final.groupby('Año')[cols_numericas].sum().reset_index()

        # Recalculamos rendimiento (La verdad matemática, como bien dijiste)
        resumen['Rendimiento (t/ha)'] = resumen.apply(
            lambda row: round(row['Producción (t)'] / row['Área cosechada (ha)'], 2) if row['Área cosechada (ha)'] > 0 else 0.0,
            axis=1
        )

        # --- MOSTRAR RESULTADOS ---
        st.markdown("---")
        st.subheader(f"📊 Reporte de {nombre_bonito_cultivo} en {nombre_bonito_depto}")
        
        if resumen.empty or resumen[cols_numericas].sum().sum() == 0:
            st.error("Mmm, raro. No hay datos numéricos válidos para este cruce. El Excel está pelado en esta parte.")
        else:
            # Vamos a poner un par de métricas rápidas del último año registrado para descrestar
            ultimo_ano = resumen['Año'].max()
            datos_ultimo_ano = resumen[resumen['Año'] == ultimo_ano].iloc[0]
            
            st.markdown(f"**Resumen rápido del año {ultimo_ano}:**")
            col1, col2, col3, col4 = st.columns(4)
            
            # Usamos st.metric que se ve súper pro en la interfaz
            col1.metric("Área Sembrada", f"{datos_ultimo_ano['Área sembrada (ha)']:,.0f} ha")
            col2.metric("Área Cosechada", f"{datos_ultimo_ano['Área cosechada (ha)']:,.0f} ha")
            col3.metric("Producción", f"{datos_ultimo_ano['Producción (t)']:,.0f} t")
            col4.metric("Rendimiento", f"{datos_ultimo_ano['Rendimiento (t/ha)']} t/ha")
            
            st.markdown("<br>", unsafe_allow_html=True) # Un saltico de línea
            
            # Gráfico de barras para la producción (porque una tabla sola es aburrida)
            st.markdown("**Evolución de la Producción en el tiempo:**")
            st.bar_chart(data=resumen, x='Año', y='Producción (t)', color="#2e7b32")
            
            # Finalmente, la tabla con todos los fierros
            st.markdown("**Tabla detallada:**")
            # En Streamlit los DataFrames se ven geniales de forma nativa
            st.dataframe(
                resumen, 
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Año": st.column_config.NumberColumn(format="%d"),
                    "Área sembrada (ha)": st.column_config.NumberColumn(format="%,.2f"),
                    "Área cosechada (ha)": st.column_config.NumberColumn(format="%,.2f"),
                    "Producción (t)": st.column_config.NumberColumn(format="%,.2f")
                }
            )
            
            st.success("¡Listo el pollo! (O bueno, el cultivo). Cambia los filtros en la barra lateral para seguir chismoseando.")

if __name__ == "__main__":
    main()