import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Auto vs Uber | Análisis de TCO", layout="wide")

st.title("🚗 Auto vs Uber")
st.markdown("Analizando la conveniencia financiera de tener un vehículo propio frente al uso de aplicaciones de transporte.")

@st.cache_data
def load_data():
    return pd.read_csv("base_lista_para_streamlit.csv")

df = load_data()

# --- NUEVO: FUNCIÓN PARA TRAER EL DÓLAR EN VIVO ---
@st.cache_data(ttl=3600) # Guarda el dato por 1 hora para no saturar la API
def obtener_dolar_mep():
    try:
        url = "https://dolarapi.com/v1/dolares/bolsa"
        respuesta = requests.get(url)
        if respuesta.status_code == 200:
            data = respuesta.json()
            # Retornamos el valor de venta y solo la fecha sin la hora para que quede prolijo
            return float(data['venta']), data['fechaActualizacion'][:10]
    except Exception as e:
        pass
    # Valor de contingencia por si se cae internet
    return 1250.0, "Sin conexión"

precio_mep_vivo, fecha_mep = obtener_dolar_mep()

# --- 2. BARRA LATERAL ---
st.sidebar.header("0. Configuración de Moneda")
moneda = st.sidebar.selectbox("Visualizar Dashboard en:", ["USD (Dólares)", "ARS (Pesos)"])

# Usamos la variable en vivo como valor por defecto
tipo_cambio = st.sidebar.number_input(
    "Cotización Dólar MEP (ARS):",
    value=precio_mep_vivo,
    step=10.0,
    help="Ingresá el tipo de cambio actual para realizar las conversiones en tiempo real."
)
st.sidebar.caption(f"💡 *Ref: Dólar MEP vivo: ${precio_mep_vivo:,.2f} (Actualizado: {fecha_mep})*")

st.sidebar.markdown("---")
st.sidebar.header("1. Selección del Vehículo")
modelo_elegido = st.sidebar.selectbox("Elegí un Modelo:", df['Modelo'].unique())
provincia = st.sidebar.selectbox("Provincia de Radicación:", ["Entre Ríos", "CABA", "Buenos Aires", "Santa Fe", "Resto del País"])

st.sidebar.markdown("---")
st.sidebar.header("2. Perfil de Uso y OPEX Frecuente")
km_anuales = st.sidebar.slider("Kilómetros estimados por año:", min_value=5000, max_value=40000, value=15000, step=1000)
precio_litro = st.sidebar.number_input("Precio Combustible (USD por Litro):", value=1.10, step=0.05, help="Para mantener la estabilidad del modelo frente a la inflación local, los inputs base se cargan en valor dólar.")
precio_service = st.sidebar.number_input("Costo de Service (cada 10k km en USD):", value=150, step=10)
cochera_mensual = st.sidebar.number_input("Cochera Mensual (USD):", value=0, step=10)

with st.sidebar.expander("🛠️ Mantenimiento Pesado (Amortizado)"):
    costo_cubiertas = st.number_input("4 Cubiertas (cada 60k km en USD):", value=800, step=50)
    costo_distribucion = st.number_input("Correa y Bomba (cada 60k km en USD):", value=500, step=50)
    costo_amortiguadores = st.number_input("Amortiguadores (cada 60k km en USD):", value=400, step=50)
    costo_tren_delantero = st.number_input("Tren Delantero (cada 100k km en USD):", value=600, step=50)

st.sidebar.markdown("---")
st.sidebar.header("3. Alternativa de Movilidad")
precio_uber_km = st.sidebar.number_input("Precio estimado de Uber/Cabify (USD por Km):", value=0.45, step=0.05)


# --- 3. CONFIGURACIÓN DINÁMICA DE ARQUITECTURA BIMONETARIA ---
if moneda == "ARS (Pesos)":
    factor_pantalla = tipo_cambio
    lbl = "ARS"
    signo = "$"
else:
    factor_pantalla = 1.0
    lbl = "USD"
    signo = "USD"

st.success(f"🏆 **Analizando Flota:** {modelo_elegido} - Vehículo de Referencia del Mercado")


# --- 4. MOTOR DE CÁLCULO DINÁMICO ---
# Ordenamos por Versión y luego por Año para aislar el cálculo matemático
df_filtrado = df[df['Modelo'] == modelo_elegido].sort_values(['Version', 'Año'], ascending=[True, False]).copy()

df_filtrado['Precio_USD'] = df_filtrado['Precio'] / tipo_cambio

def calcular_patente_dinamica(row, prov):
    precio = row['Precio_USD']
    antiguedad = row['Antigüedad']
    version = str(row['Version']).upper()
    if antiguedad >= 15: return 0
    es_hibrido = any(kw in version for kw in ['HEV', 'HYBRID', 'HIBRIDO', 'EQ', 'MHEV'])
    if prov == "Entre Ríos":
        alicuota = 0.025
        if es_hibrido:
            if antiguedad == 0: return 0
            elif antiguedad == 1: return precio * alicuota * 0.50
            elif antiguedad == 2: return precio * alicuota * 0.80
        return precio * alicuota
    elif prov == "CABA": return 0 if es_hibrido else (precio * 0.040)
    elif prov == "Buenos Aires": return precio * 0.045
    elif prov == "Santa Fe": return 0 if es_hibrido else (precio * 0.020)
    else: return precio * 0.022

df_filtrado['Costo_Patente_Anual'] = df_filtrado.apply(lambda r: calcular_patente_dinamica(r, provincia), axis=1)
df_filtrado['Costo_Seguro_Anual'] = df_filtrado['Precio_USD'] * 0.035

# Cálculo aislado: diff(-1) restará solo contra el año anterior de la MISMA versión
df_filtrado['Perdida_Anual_USD'] = df_filtrado.groupby('Version')['Precio_USD'].diff(periods=-1)
df_filtrado['Tasa_Depreciacion_Pct'] = (df_filtrado['Perdida_Anual_USD'] / df_filtrado['Precio_USD']) * 100

df_filtrado['Costo_Combustible_Anual'] = (km_anuales / 100) * 9 * precio_litro
df_filtrado['Costo_Service_Anual'] = (km_anuales / 10000) * precio_service
df_filtrado['Costo_Cochera_Anual'] = cochera_mensual * 12
df_filtrado['Costo_Mantenimiento_Pesado_Anual'] = km_anuales * ((costo_cubiertas + costo_distribucion + costo_amortiguadores) / 60000 + costo_tren_delantero / 100000)

tasa_desgaste = 0.05
df_filtrado['Multiplicador_Edad'] = (1 + tasa_desgaste) ** df_filtrado['Antigüedad']
df_filtrado['Costo_Service_Anual'] = df_filtrado['Costo_Service_Anual'] * df_filtrado['Multiplicador_Edad']
df_filtrado['Costo_Mantenimiento_Pesado_Anual'] = df_filtrado['Costo_Mantenimiento_Pesado_Anual'] * df_filtrado['Multiplicador_Edad']
df_filtrado['Uso_Regular_Anual'] = df_filtrado['Costo_Combustible_Anual'] + df_filtrado['Costo_Service_Anual'] + df_filtrado['Costo_Cochera_Anual']

df_filtrado['TCO_Total_Anual'] = (
    df_filtrado['Perdida_Anual_USD'].fillna(0) + df_filtrado['Costo_Patente_Anual'] +
    df_filtrado['Costo_Seguro_Anual'] + df_filtrado['Uso_Regular_Anual'] + df_filtrado['Costo_Mantenimiento_Pesado_Anual']
)

# Columnas de despliegue
df_filtrado['Precio_Disp'] = df_filtrado['Precio_USD'] * factor_pantalla
df_filtrado['Perdida_Disp'] = df_filtrado['Perdida_Anual_USD'] * factor_pantalla
df_filtrado['Patente_Disp'] = df_filtrado['Costo_Patente_Anual'] * factor_pantalla
df_filtrado['Seguro_Disp'] = df_filtrado['Costo_Seguro_Anual'] * factor_pantalla
df_filtrado['Uso_Disp'] = df_filtrado['Uso_Regular_Anual'] * factor_pantalla
df_filtrado['Maint_Pesado_Disp'] = df_filtrado['Costo_Mantenimiento_Pesado_Anual'] * factor_pantalla

# --- 5. BUSCADOR DEL MEJOR PERÍODO ---
mejor_periodo = None
min_dep_acumulada_pct = float('inf')

for i, row in df_filtrado.iterrows():
    año_inicio = row['Año']
    año_fin = año_inicio - 3
    if año_fin in df_filtrado['Año'].values:
        precio_inicio = row['Precio_USD']
        precio_fin = df_filtrado[df_filtrado['Año'] == año_fin]['Precio_USD'].values[0]
        dep_pct = ((precio_inicio - precio_fin) / precio_inicio) * 100
        if dep_pct < min_dep_acumulada_pct:
            min_dep_acumulada_pct = dep_pct
            mejor_periodo = (año_inicio, año_fin)


# --- 6. VISUALIZACIONES PRINCIPALES ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Curva de Valor Patrimonial", help="Los precios representan los valores de referencia del mercado automotor para unidades usadas en estado estándar. Fuente base: Cámara del Comercio Automotor (CCA).")

    fig1 = px.line(df_filtrado, x='Año', y='Precio_Disp', markers=True, custom_data=['Perdida_Disp'])
    fig1.update_traces(
        line=dict(color='#1f77b4', width=3), marker=dict(size=8),
        hovertemplate=f"<b>Año: %{{x}}</b><br>Precio: {signo} %{{y:,.0f}}<br>Pérdida próximo año: {signo} %{{customdata[0]:,.0f}}<extra></extra>"
    )
    fig1.update_layout(
        xaxis_title="<b>Año de Fabricación</b>", yaxis_title=f"<b>Precio ({lbl})</b>", font=dict(size=14),
        hovermode="x unified", xaxis=dict(autorange="reversed", showgrid=True), yaxis=dict(showgrid=True)
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Análisis de Período de Retención", help="Mide la destrucción porcentual del capital inmovilizado. La Tasa Marginal Anual se calcula dividiendo la pérdida proyectada para el año siguiente sobre el precio de mercado actual del vehículo.")

    min_yr = int(df_filtrado['Año'].min())
    max_yr = int(df_filtrado['Año'].max())
    rango_seleccionado = st.slider("Seleccioná el período de retención a analizar:", min_value=min_yr, max_value=max_yr, value=(max_yr - 4, max_yr))
    año_venta, año_compra = rango_seleccionado
    anios_retencion = año_compra - año_venta

    if anios_retencion > 0:
        precio_compra = df_filtrado[df_filtrado['Año'] == año_compra]['Precio_USD'].values[0]
        precio_venta = df_filtrado[df_filtrado['Año'] == año_venta]['Precio_USD'].values[0]
        dep_acum_usd = precio_compra - precio_venta
        dep_acum_disp = dep_acum_usd * factor_pantalla
        dep_acum_pct = (dep_acum_usd / precio_compra) * 100
        promedio_anual_pct = dep_acum_pct / anios_retencion
    else:
        dep_acum_disp = 0; dep_acum_pct = 0; promedio_anual_pct = 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Años de Retención", f"{anios_retencion} años")
    m2.metric("Depreciación Acumulada", f"{dep_acum_pct:.1f}%", f"- {signo} {dep_acum_disp:,.0f}", delta_color="inverse")
    m3.metric("Promedio Anual", f"{promedio_anual_pct:.1f}% / año")

    df_tasas = df_filtrado.dropna(subset=['Tasa_Depreciacion_Pct']).copy()
    df_tasas['Color'] = df_tasas['Año'].apply(lambda x: '#ff7f0e' if año_venta <= x <= año_compra else '#d3d3d3')

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df_tasas['Año'], y=df_tasas['Tasa_Depreciacion_Pct'],
        marker_color=df_tasas['Color'], marker_line_color='black', marker_line_width=1,
        customdata=df_tasas[['Precio_Disp', 'Perdida_Disp']],
        hovertemplate=f"<b>Año: %{{x}}</b><br>Pérdida Marginal: %{{y:.1f}}%<br>{signo} %{{customdata[1]:,.0f}}<extra></extra>"
    ))

    fig2.update_layout(
        xaxis_title="<b>Año de Fabricación</b>", yaxis_title="<b>Depreciación Marginal (%)</b>",
        font=dict(size=14), xaxis=dict(autorange="reversed", type='category'),
        showlegend=False, height=250, margin=dict(t=30, b=0)
    )
    st.plotly_chart(fig2, use_container_width=True)

    if mejor_periodo:
        st.success(f"🏆 **El mejor período histórico de 3 años:** Comprar modelo **{mejor_periodo[0]}** y retener hasta que alcance la antigüedad del **{mejor_periodo[1]}**. La pérdida total de capital es de solo **{min_dep_acumulada_pct:.1f}%**.")

st.markdown("---")

# --- 7. GRÁFICO APILADO (TCO) ---
st.subheader(f"Estructura del TCO Anualizado", help="TCO (Total Cost of Ownership). Suma el CAPEX (Depreciación patrimonial) más el OPEX (Gastos operativos). El modelo asume un incremento compuesto del 5% anual en los costos de mantenimiento para penalizar la retención de activos envejecidos.")

col3, col4 = st.columns([2, 1])

with col3:
    df_marginal = df_filtrado.dropna(subset=['Perdida_Anual_USD'])
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=df_marginal['Año'], y=df_marginal['Perdida_Disp'], name='Depreciación (CAPEX)', marker_color='#d62728', hovertemplate=f"<b>Depreciación:</b> {signo} %{{y:,.0f}}<extra></extra>"))
    fig3.add_trace(go.Bar(x=df_marginal['Año'], y=df_marginal['Seguro_Disp'], name='Seguro', marker_color='#1f77b4', hovertemplate=f"<b>Seguro:</b> {signo} %{{y:,.0f}}<extra></extra>"))
    fig3.add_trace(go.Bar(x=df_marginal['Año'], y=df_marginal['Patente_Disp'], name=f'Patente', marker_color='#2ca02c', hovertemplate=f"<b>Patente:</b> {signo} %{{y:,.0f}}<extra></extra>"))
    fig3.add_trace(go.Bar(x=df_marginal['Año'], y=df_marginal['Uso_Disp'], name='Nafta+Service+Cochera', marker_color='#9467bd', hovertemplate=f"<b>Uso Regular:</b> {signo} %{{y:,.0f}}<extra></extra>"))
    fig3.add_trace(go.Bar(x=df_marginal['Año'], y=df_marginal['Maint_Pesado_Disp'], name='Amort. Pesada', marker_color='#bcbd22', hovertemplate=f"<b>Mant. Pesado:</b> {signo} %{{y:,.0f}}<extra></extra>"))

    fig3.update_layout(
        barmode='stack', xaxis_title="<b>Año de Fabricación</b>", yaxis_title=f"<b>Gasto Total Anual ({lbl})</b>",
        font=dict(size=14), xaxis=dict(autorange="reversed", type='category'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    costo_uber_anual_disp = km_anuales * precio_uber_km * factor_pantalla
    st.metric(label="📊 Alternativa Dinámica (Uber/Cabify)", value=f"{signo} {costo_uber_anual_disp:,.0f}", help="Costo de oportunidad calculado multiplicando la tarifa plana ingresada por los kilómetros anuales del usuario.")

    tco_promedio_auto_disp = df_marginal['TCO_Total_Anual'].mean() * factor_pantalla
    st.metric(label="🚗 TCO Promedio Flota", value=f"{signo} {tco_promedio_auto_disp:,.0f}", help="Promedio del Costo Total Anual de todas las añadas disponibles del modelo analizado.")

    if tco_promedio_auto_disp > costo_uber_anual_disp:
        st.error("❌ Conviene usar apps de movilidad para este kilometraje.")
    else:
        st.success("✅ Conviene comprar (TCO inferior).")

st.markdown("---")

# --- 8. ANEXO METODOLÓGICO Y TABLA DINÁMICA AÑO A AÑO ---
with st.expander("📚 Notas Metodológicas y Especificaciones de Flota (Leer antes de analizar)"):
    st.markdown(f"""
    **Origen de los Datos & Conversión Dinámica:**
    Los precios base en pesos originales son extraídos y actualizados mensualmente de forma automática desde la guía oficial de **Autocosmos**.
    Al seleccionar visualización en Dólares, el sistema realiza la conversión en tiempo real dividiendo el precio por la cotización del Dólar MEP extraída en vivo desde DolarAPI.

    **Flota de Referencia Analizada (Top 20 Argentina):**
    El modelo evalúa más de 2700 registros históricos correspondientes a los vehículos de mayor liquidez del mercado:
    * **Pick-ups:** Toyota Hilux, VW Amarok, Ford Ranger, Nissan Frontier.
    * **SUVs:** Corolla Cross, Tracker, Taos, Renegade, HR-V, 2008.
    * **Pasajeros:** Cronos, 208, Yaris, Polo, Corolla, Cruze, Sandero.
    * **Premium y Lujo:** Mercedes-Benz GLC 300, Audi Q5, BMW X3.
    * **Utilitarios e Históricos:** Kangoo, VW Gol, EcoSport.
    """)

st.subheader("Matriz de Exploración Anual (Personalizable)")
st.markdown("Seleccioná la versión específica de cada año para evaluar su evolución financiera. Los datos se recalculan en tiempo real.")

# 1. Armamos el encabezado de nuestra tabla fabricada a medida
col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([1, 4, 2, 2, 2])
col_h1.markdown("**Año**")
col_h2.markdown("**Versión**")
col_h3.markdown(f"**Precio ({lbl})**")
col_h4.markdown(f"**Pérdida ({lbl})**")
col_h5.markdown("**Depreciación (%)**")
st.markdown("---")

# 2. Extraemos los años únicos disponibles para este modelo, ordenados de más nuevo a más viejo
años_disponibles = sorted(df_filtrado['Año'].unique(), reverse=True)

# 3. Bucle para construir cada fila dinámicamente
for año in años_disponibles:
    # Aislamos los datos de ese año en particular
    df_año = df_filtrado[df_filtrado['Año'] == año]
    versiones_año = df_año['Version'].unique()
    
    # Creamos las 5 columnas de la fila
    c1, c2, c3, c4, c5 = st.columns([1, 4, 2, 2, 2])
    
    with c1:
        st.write(f"**{año}**")
        
    with c2:
        # Selector clave: Usamos f"select_{año}" en el key para que Streamlit sepa que cada desplegable es independiente
        version_elegida = st.selectbox(
            "Versión", 
            options=versiones_año, 
            label_visibility="collapsed", 
            key=f"select_{año}"
        )
        
    # Extraemos la fila exacta de datos según la versión que el usuario dejó en el selector
    datos_fila = df_año[df_año['Version'] == version_elegida].iloc[0]
    
    with c3:
        st.write(f"{signo} {datos_fila['Precio_Disp']:,.0f}")
        
    with c4:
        # Validación para evitar errores si es el año más antiguo y no tiene contra qué calcular pérdida
        if pd.isna(datos_fila['Perdida_Disp']):
            st.write("-")
        else:
            st.write(f"{signo} {datos_fila['Perdida_Disp']:,.0f}")
            
    with c5:
        if pd.isna(datos_fila['Tasa_Depreciacion_Pct']):
            st.write("-")
        else:
            st.write(f"{datos_fila['Tasa_Depreciacion_Pct']:.1f}%")
            
st.markdown("---")
