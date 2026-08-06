import requests
import pandas as pd
import time
import random
import datetime
import io

# 1. Configuración Inicial
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
anio_actual = datetime.datetime.now().year
lista_dataframes_totales = []

print("🚀 Iniciando el Motor de Extracción de Datos (Autocosmos)...")

# 2. Diccionario Maestro de la Flota Definitivo (Con todas las correcciones de URLs)
flota = [
    # --- Autos de Pasajeros ---
    {"marca": "fiat", "modelo": "cronos", "display": "Cronos", "inicio": 2018, "fin": anio_actual},
    {"marca": "peugeot", "modelo": "208", "display": "208", "inicio": 2013, "fin": anio_actual},
    {"marca": "toyota", "modelo": "yaris", "display": "Yaris", "inicio": 2016, "fin": anio_actual},
    {"marca": "volkswagen", "modelo": "polo", "display": "Polo", "inicio": 2018, "fin": anio_actual},
    {"marca": "toyota", "modelo": "corolla", "display": "Corolla", "inicio": 2010, "fin": anio_actual},
    {"marca": "chevrolet", "modelo": "cruze", "display": "Cruze", "inicio": 2010, "fin": 2023},
    {"marca": "renault", "modelo": "sandero", "display": "Sandero", "inicio": 2010, "fin": anio_actual},
    
    # --- SUVs y Crossovers ---
    {"marca": "toyota", "modelo": "corolla-cross", "display": "Corolla Cross", "inicio": 2021, "fin": anio_actual},
    {"marca": "chevrolet", "modelo": "tracker", "display": "Tracker", "inicio": 2013, "fin": anio_actual},
    {"marca": "volkswagen", "modelo": "taos", "display": "Taos", "inicio": 2021, "fin": anio_actual},
    {"marca": "jeep", "modelo": "renegade", "display": "Renegade", "inicio": 2016, "fin": anio_actual},
    {"marca": "honda", "modelo": "hr-v", "display": "HR-V", "inicio": 2015, "fin": anio_actual},
    {"marca": "peugeot", "modelo": "2008", "display": "2008", "inicio": 2016, "fin": anio_actual},
    
    # --- Pick-ups (URLs corregidas) ---
    {"marca": "toyota", "modelo": "hilux-pick---up", "display": "Hilux", "inicio": 2010, "fin": anio_actual},
    {"marca": "volkswagen", "modelo": "amarok-pick---up", "display": "Amarok", "inicio": 2012, "fin": anio_actual},
    {"marca": "ford", "modelo": "ranger-pick---up", "display": "Ranger", "inicio": 2012, "fin": anio_actual},
    {"marca": "nissan", "modelo": "frontier-pick---up", "display": "Frontier", "inicio": 2010, "fin": anio_actual},
    
    # --- Utilitarios Livianos (Divididos por versión de URL) ---
    {"marca": "renault", "modelo": "kangoo", "display": "Kangoo", "inicio": 2010, "fin": 2018},
    {"marca": "renault", "modelo": "kangoo-ii-express", "display": "Kangoo", "inicio": 2018, "fin": anio_actual},
    {"marca": "renault", "modelo": "kangoo-ii-version-pasajeros", "display": "Kangoo", "inicio": 2018, "fin": anio_actual},
    
    # --- Históricos de alta liquidez ---
    {"marca": "volkswagen", "modelo": "gol-trend", "display": "Gol", "inicio": 2012, "fin": 2022},
    {"marca": "ford", "modelo": "ecosport", "display": "EcoSport", "inicio": 2010, "fin": 2012},
    {"marca": "ford", "modelo": "ecosport-kinetic-design-attraction", "display": "EcoSport", "inicio": 2013, "fin": 2021},

    # --- Segmento Premium / Lujo ---
    {"marca": "mercedes-benz", "modelo": "glc-300", "display": "GLC 300", "inicio": 2016, "fin": anio_actual},
    {"marca": "audi", "modelo": "q-5", "display": "Q5", "inicio": 2010, "fin": anio_actual},
    {"marca": "bmw", "modelo": "x3", "display": "X3", "inicio": 2010, "fin": anio_actual}
]

# 3. Bucle Principal de Extracción
for auto in flota:
    marca = auto["marca"]
    modelo = auto["modelo"]
    nombre_display = auto["display"]
    
    años_a_buscar = range(auto["inicio"], auto["fin"] + 1)
    
    print(f"\n--- Procesando: {nombre_display} (URL: {modelo}) ({auto['inicio']} - {auto['fin']}) ---")
    
    for año in años_a_buscar:
        url = f"https://www.autocosmos.com.ar/guiadeprecios?Marca={marca}&Modelo={modelo}&A={año}"
        
        try:
            respuesta = requests.get(url, headers=headers)
            
            if respuesta.status_code == 200:
                # El io.StringIO soluciona el cartel de "FutureWarning" de Pandas
                tablas = pd.read_html(io.StringIO(respuesta.text))
                
                if len(tablas) > 0:
                    df_temp = tablas[0]
                    
                    # Limpieza y Estandarización
                    df_temp.columns = ['Version', 'Precio', 'Accion']
                    df_temp = df_temp[['Version', 'Precio']].copy()
                    
                    # Formateo numérico
                    df_temp['Precio'] = df_temp['Precio'].astype(str).str.replace('$', '', regex=False)
                    df_temp['Precio'] = df_temp['Precio'].str.replace('.', '', regex=False)
                    df_temp['Precio'] = pd.to_numeric(df_temp['Precio'].str.strip(), errors='coerce')
                    df_temp = df_temp.dropna(subset=['Precio'])
                    
                    # Generación de variables analíticas necesarias para app.py
                    df_temp.insert(0, 'Marca', marca.capitalize())
                    df_temp.insert(1, 'Modelo', nombre_display)
                    df_temp.insert(2, 'Año', año)
                    df_temp['Antigüedad'] = anio_actual - año  
                    
                    lista_dataframes_totales.append(df_temp)
                    print(f"✅ {año} capturado ({len(df_temp)} versiones)")
                else:
                    print(f"⚠️ Año {año}: Sin datos tabulados.")
            else:
                print(f"❌ Error HTTP {respuesta.status_code} en {año}.")
                
        except Exception as e:
            print(f"⏭️ Salteando {año} por error de lectura o estructura de la web.")
            
        # Pausa aleatoria para emular comportamiento humano y evitar bloqueos
        time.sleep(random.uniform(1.2, 3.1))

# 4. Consolidación y Exportación
print("\n🛠️ Consolidando la base de datos maestra...")

if len(lista_dataframes_totales) > 0:
    df_final = pd.concat(lista_dataframes_totales, ignore_index=True)
    
    # Exportación al archivo exacto que lee Streamlit
    nombre_archivo = "base_lista_para_streamlit.csv"
    df_final.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
    
    print(f"\n🎉 ¡ÉXITO! Base actualizada con {len(df_final)} registros.")
    print(f"💾 Guardado como '{nombre_archivo}'. El dashboard se actualizará automáticamente.")
else:
    print("\n🚨 Error Crítico: No se logró recolectar ningún dato. Revisar conexión o selectores HTML.")
