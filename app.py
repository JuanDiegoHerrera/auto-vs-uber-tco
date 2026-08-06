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
@st.cache_data(ttl=3600)
def obtener_dolar_mep():
    try:
        url = "https://dolarapi.com/v1/dolares/bolsa"
        respuesta = requests.get(url)
        if respuesta.status_code == 200:
            data = respuesta.json()
            return float(data['venta']), data['fechaActualizacion'][:10]
    except Exception as e:
        pass
    return 1250.0, "Sin conexión"

precio_mep_vivo, fecha_mep = obtener_dolar_mep()

# --- 2. BARRA LATERAL ---
st.sidebar.header("0. Configuración de Moneda")
moneda = st.sidebar.selectbox("Visualizar Dashboard en:", ["USD (Dólares)", "ARS (Pesos)"])

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
precio_litro = st.sidebar.number_input("Precio Combustible (USD por Litro):", value=1.10, step=0.05)
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

# --- 4. MOTOR DE CÁLCULO BASE (ENFOQUE DE MEDIANA DE MERCADO) ---
# 1. Filtramos solo el modelo que eligió el usuario
df_modelo = df[df['Modelo'] == modelo_elegido].copy()

# 2. LA MAGIA ESTADÍSTICA: Agrupamos por año y sacamos la mediana del precio original
df_filtrado = df_modelo.groupby('Año')['Precio'].median().reset_index()

# 3. Ordenamos cronológicamente (del más nuevo al más viejo)
df_filtrado = df_filtrado.sort_values('Año', ascending=False).reset_index(drop=True)

# 4. Asignamos un nombre genérico a la versión para que la tabla y funciones de abajo no rompan
df_filtrado['Version'] = f"{modelo_elegido} (Precio Medio de Mercado)"

# 5. Calculamos el valor en dólares
df_filtrado['Precio_USD'] = df_filtrado['Precio'] / tipo_cambio

# 6. Como ahora hay una sola fila por año, la pérdida es simplemente restar contra la fila de abajo
df_filtrado['Perdida_Anual_USD'] = df_filtrado['Precio_USD'] - df_filtrado['Precio_USD'].shift(-1)
df_filtrado['Tasa_Depreciacion_Pct'] = (df_filtrado['Perdida_Anual_USD'] / df_filtrado['Precio_USD']) * 100

# 7. Para el cálculo de patente y mantenimiento, necesitamos recrear la columna de Antigüedad
año_actual = 2025 # O el año base que estés tomando
df_filtrado['Antigüedad'] = año_actual - df_filtrado['Año']

# --- 6. VISUALIZACIONES PRINCIPALES ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Curva de Valor Patrimonial")
    fig1 = px.line(df_graficos, x='Año', y='Precio_Disp', markers=True, custom_data=['Perdida_Disp'])
    fig1.update_traces(
        line=dict(color='#1f77b4', width=3), marker=dict(size=8),
        hovertemplate=f"<b>Año: %{{x}}</b><br>Precio: {signo} %{{y:,.0f}}<br>Pérdida cruzada al año ant.: {signo} %{{customdata[0]:,.0f}}<extra></extra>"
    )
    fig1.update_layout(
        xaxis_title="<b>Año de Fabricación</b>", yaxis_title=f"<b>Precio ({lbl})</b>", font=dict(size=14),
        hovermode="x unified", 
        xaxis=dict(autorange="reversed", showgrid=True, type='category'), # Soluciona el eje invertido y los decimales
        yaxis=dict(showgrid=True)
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Análisis de Período de Retención")
    min_yr = int(df_graficos['Año'].min())
    max_yr = int(df_graficos['Año'].max())
    
    if min_yr == max_yr:
        st.warning("⚠️ Flota con 1 solo año de registro.")
    else:
        rango_max_posible = min(4, max_yr - min_yr)
        rango_seleccionado = st.slider("Período de retención a analizar:", min_value=min_yr, max_value=max_yr, value=(max_yr - rango_max_posible, max_yr))
        año_venta, año_compra = rango_seleccionado
        anios_retencion = año_compra - año_venta

        if anios_retencion > 0:
            precio_compra = df_graficos[df_graficos['Año'] == año_compra]['Precio_USD'].values[0]
            precio_venta = df_graficos[df_graficos['Año'] == año_venta]['Precio_USD'].values[0]
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

    df_tasas = df_graficos.dropna(subset=['Tasa_Depreciacion_Pct']).copy()
    if not df_tasas.empty and 'año_venta' in locals():
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
            font=dict(size=14), 
            xaxis=dict(autorange="reversed", type='category'),
            showlegend=False, height=250, margin=dict(t=30, b=0)
        )
        st.plotly_chart(fig2, use_container_width=True)

    if mejor_periodo:
        st.success(f"🏆 **El mejor período histórico:** Comprar modelo **{mejor_periodo[0]}** y retener hasta el **{mejor_periodo[1]}**.")

# --- 7. GRÁFICO APILADO (TCO) ---
st.subheader(f"Estructura del TCO Anualizado")
col3, col4 = st.columns([2, 1])

with col3:
    df_marginal = df_graficos.dropna(subset=['Perdida_Anual_USD'])
    fig3 = go.Figure()
    
    if not df_marginal.empty:
        fig3.add_trace(go.Bar(x=df_marginal['Año'], y=df_marginal['Perdida_Disp'], name='Depreciación', marker_color='#d62728', hovertemplate=f"<b>Depreciación:</b> {signo} %{{y:,.0f}}<extra></extra>"))
        fig3.add_trace(go.Bar(x=df_marginal['Año'], y=df_marginal['Seguro_Disp'], name='Seguro', marker_color='#1f77b4', hovertemplate=f"<b>Seguro:</b> {signo} %{{y:,.0f}}<extra></extra>"))
        fig3.add_trace(go.Bar(x=df_marginal['Año'], y=df_marginal['Patente_Disp'], name=f'Patente', marker_color='#2ca02c', hovertemplate=f"<b>Patente:</b> {signo} %{{y:,.0f}}<extra></extra>"))
        fig3.add_trace(go.Bar(x=df_marginal['Año'], y=df_marginal['Uso_Disp'], name='Uso Regular', marker_color='#9467bd', hovertemplate=f"<b>Uso Regular:</b> {signo} %{{y:,.0f}}<extra></extra>"))
        fig3.add_trace(go.Bar(x=df_marginal['Año'], y=df_marginal['Maint_Pesado_Disp'], name='Amort. Pesada', marker_color='#bcbd22', hovertemplate=f"<b>Mant. Pesado:</b> {signo} %{{y:,.0f}}<extra></extra>"))

        fig3.update_layout(
            barmode='stack', xaxis_title="<b>Año de Fabricación</b>", yaxis_title=f"<b>Gasto Total Anual ({lbl})</b>",
            font=dict(size=14), xaxis=dict(autorange="reversed", type='category'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig3, use_container_width=True)

with col4:
    costo_uber_anual_disp = km_anuales * precio_uber_km * factor_pantalla
    st.metric(label="📊 Alternativa Dinámica (Uber/Cabify)", value=f"{signo} {costo_uber_anual_disp:,.0f}")

    if not df_marginal.empty:
        tco_promedio_auto_disp = df_marginal['TCO_Total_Anual'].mean() * factor_pantalla
        st.metric(label="🚗 TCO Promedio Flota", value=f"{signo} {tco_promedio_auto_disp:,.0f}")

        if tco_promedio_auto_disp > costo_uber_anual_disp:
            st.error("❌ Conviene usar apps de movilidad para este kilometraje.")
        else:
            st.success("✅ Conviene comprar (TCO inferior).")

