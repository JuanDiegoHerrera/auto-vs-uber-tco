# Auto vs Uber: Simulador de Costo Total de Propiedad (TCO) y Análisis de Depreciación Bimonetaria

Este proyecto consiste en un framework analítico interactivo desarrollado en **Python** con **Streamlit** y **Plotly**. Su propósito es optimizar la toma de decisiones microeconómicas mediante la evaluación de la conveniencia financiera de adquirir un vehículo propio frente al uso de plataformas de transporte (*Mobility as a Service - MaaS*), integrando dinámicas de depreciación patrimonial, estructuras de costos operativos de ciclo largo y marcos regulatorios impositivos de Argentina.

## 📌 Contexto Económico y Planteo del Problema

La evaluación tradicional de adquisición de un activo automotor suele limitarse al análisis estático del precio de compra. Este modelo aborda el problema desde una perspectiva integral de **Finanzas Corporativas** y **Organización Industrial**, dividiendo los flujos de fondos proyectados en dos dimensiones críticas:

1. **CAPEX (Capital Expenditure):** La inversión inicial y la destrucción de valor patrimonial derivada de la **Tasa de Depreciación Marginal Interanual**. El vehículo se modela como un activo de capital sujeto a obsolescencia y desgaste de mercado.
2. **OPEX (Operating Expenditure):** Los costos operativos divididos en flujos frecuentes (combustible, cocheras, seguros) y flujos diferidos (mantenimiento pesado), vinculados directamente a la tasa de utilización (kilómetros recorridos por año).

El objetivo principal es determinar de manera personalizada el **punto de equilibrio operativo (*Break-Even Point*)** donde el Costo Total de Propiedad (TCO) anualizado intersecta la curva de costo variable de la alternativa MaaS (Uber/Cabify).

---

## 🛠️ Especificaciones Técnicas y Modelado Matemático

### 1. Amortización de Costos de Ciclo Largo (Mantenimiento Pesado)
Para evitar distorsiones o "saltos" artificiales en los flujos de caja anuales debido a gastos mayores que ocurren en períodos prolongados, el framework implementa un criterio de **Amortización Devengada por Kilómetro**. Gastos como la sustitución de neumáticos (cada 60.000 km), kit de distribución y bomba de agua (cada 60.000 km), amortiguadores (cada 60.000 km) y componentes del tren delantero (cada 100.000 km) se transforman en una tasa de costo variable por kilómetro rodado:

$$\text{Costo Variable Pesado por Km} = \frac{\text{Costo Neumáticos}}{60000} + \frac{\text{Costo Distribución}}{60000} + \frac{\text{Costo Amortiguadores}}{60000} + \frac{\text{Costo Tren Delantero}}{100000}$$

### 2. Coeficiente de Penalidad por Envejecimiento Mecánico
Asumir costos de mantenimiento constantes a lo largo del tiempo introduce un sesgo optimista en activos envejecidos. Para neutralizarlo, el modelo aplica una tasa de incremento compuesto del **5% anual basado en la antigüedad**, reflejando el incremento exponencial en la probabilidad de fallas estructurales e imprevistos fuera de garantía:

$$\text{OPEX Ajustado}_t = \text{OPEX Base} \times (1 + 0.05)^{\text{Antigüedad}_t}$$

### 3. Motor Impositivo y Regulación Fiscal Dinámica
El simulador incorpora la legislación tributaria automotriz de las principales jurisdicciones argentinas (Entre Ríos, CABA, Buenos Aires, Santa Fe, Resto del País). Cuenta con un sistema de detección automática de motorizaciones ecológicas mediante reconocimiento de patrones de texto (`HEV`, `Hybrid`, `MHEV`), aplicando exenciones fiscales avanzadas en tiempo real. Para la provincia de **Entre Ríos**, implementa el esquema de beneficio escalonado según la **Ley 11.247** (100% de exención en Año 0, 50% de bonificación en Año 1, y 20% en Año 2).

### 4. Análisis de Período de Retención (*Holding Period*)
A través de un control interactivo de rango temporal (*double-ended slider*), el usuario puede simular ventanas específicas de tenencia del activo (ej. comprar un usado con 2 años de antigüedad y retenerlo por 4 años). La aplicación calcula dinámicamente la **Depreciación Porcentual Acumulada** y la **Tasa Promedio Anualizada** de esa ventana, iluminando los años seleccionados en el gráfico interactivo mediante código dinámico de Plotly:

$$\text{Depreciación Acumulada \%} = \frac{\text{Precio Compra} - \text{Precio Venta}}{\text{Precio Compra}} \times 100$$

$$\text{Tasa Promedio Anual} = \frac{\text{Depreciación Acumulada \%}}{\text{Años de Retención}}$$

### 5. Algoritmo de Minería para Optimización de Reemplazo (*Sweet Spot*)
El backend escanea de forma iterativa toda la matriz histórica del vehículo buscando la ventana óptima de 3 años de uso que minimice la destrucción de capital en términos porcentuales, emitiendo un veredicto automatizado para guiar la estrategia de recambio de activo.

### 6. Arquitectura Bimonetaria Dinámica con API en Vivo
Dado el contexto bimonetario de Argentina, donde los vehículos se cotizan en dólares pero los flujos de OPEX se cancelan en moneda local, la aplicación se conecta en tiempo real con **DolarAPI** para extraer la cotización del **Dólar MEP (Bolsa)**. El usuario puede conmutar el dashboard completo entre pesos y dólares de forma instantánea; el motor recalcula todas las métricas, etiquetas y tooltips automáticamente para evitar distorsiones inflacionarias.

---

## 📈 Metodología de Integración del TCO

Para cada año de fabricación del vehículo seleccionado, el costo total anual proyectado se compone de la siguiente sumatoria de variables homogeneizadas:

$$\text{TCO Total Anual}_t = \text{Depreciación Marginal}_t + \text{Patente}_t + \text{Seguro}_t + \text{OPEX Frecuente}_t + \text{OPEX Pesado Amortizado}_t$$

Donde:
- **Depreciación Marginal:** $Precio_t - Precio_{t-1}$ (pérdida patrimonial interanual del período).
- **Seguro:** Modelado como proxy financiero equivalente al 3.5% anual del valor de mercado del activo.
- **Patente:** Alícuota provincial aplicada sobre el precio de mercado, corregida por bonificación verde si corresponde.
- **OPEX Frecuente:** Consumo de combustible (estimado sobre un patrón mixto de 9L/100km) + Cocheras + Mantenimiento frecuente (cambio de aceite y filtros cada 10.000 km).

El modelo contrasta este resultado contra el **Costo de la Alternativa MaaS Dinámica**:

$$\text{Costo Anual Uber} = \text{Kilómetros Anuales} \times \text{Precio Uber por Km}$$

---

## 📊 Stack Tecnológico Utilizado

* **Python 3.x:** Lenguaje principal de procesamiento de datos, scraping y backend.
* **Streamlit:** Framework para el diseño de la interfaz de usuario y despliegue de la web app.
* **GitHub Actions:** Orquestación de CI/CD para la automatización mensual del pipeline de datos (*cron jobs*).
* **Plotly Express & Graph Objects:** Biblioteca gráfica para la creación de charts interactivos, mapas de capas apiladas y tooltips dinámicos.
* **Pandas & NumPy:** Motores analíticos para la extracción HTML, reindexación de series, limpieza de datos y transformaciones de tipo de cambio.
* **Requests:** Conectividad con endpoints de API externas (DolarAPI) y ejecución de peticiones HTTP para el web scraping.
---
## 📋 Especificaciones de la Flota de Referencia

Para asegurar la consistencia, liquidez y comparabilidad del modelo a lo largo de la serie temporal (2010 - Actualidad), el pipeline extrae los datos del **Top 20 de vehículos más patentados de Argentina**, abarcando cuatro segmentos clave del mercado:

* **Segmento Pick-ups (Alta retención de valor):** Toyota Hilux, Volkswagen Amarok, Ford Ranger, Nissan Frontier.
* **Segmento SUVs y Crossovers:** Toyota Corolla Cross, Chevrolet Tracker, Volkswagen Taos, Jeep Renegade, Honda HR-V, Peugeot 2008.
* **Segmento Autos de Pasajeros:** Fiat Cronos, Peugeot 208, Toyota Yaris, Volkswagen Polo, Toyota Corolla, Chevrolet Cruze, Renault Sandero.
* **Segmento Utilitarios y Vehículos Históricos (Alta liquidez en usados):** Renault Kangoo, Volkswagen Gol, Ford EcoSport.
* **Segmento Premium y Alta Gama (Tecnología y Lujo):** Mercedes-Benz GLC 300, Audi Q5, BMW X3.
---
## ⚙️ Arquitectura de Datos y Automatización (Data Pipeline)

Este proyecto cuenta con un motor de datos 100% autónomo construido en Python, diseñado para evitar la obsolescencia de los precios y mantener el rigor analítico del modelo de TCO.

* **Extracción (Web Scraping):** El script `scraper.py` recorre mensualmente la guía de precios oficial de Autocosmos.
* **Transformación y Limpieza:** El código procesa dinámicamente las inconsistencias de las URLs (ej: denominaciones específicas de pick-ups o versiones descatalogadas) y unifica la información, calculando en tiempo real la variable de antigüedad.
* **Volumen de Datos:** La base consolida de manera automatizada más de 2700 registros históricos con sus respectivas cotizaciones de mercado.
* **Automatización en la Nube (CI/CD):** Mediante el uso de **GitHub Actions**, un *cron job* ejecuta la extracción el día 1 de cada mes. 
* **Despliegue Continuo:** El servidor sobreescribe automáticamente el archivo CSV maestro del repositorio. Esta acción impacta de manera inmediata en la interfaz visual de Streamlit, garantizando que los usuarios siempre operen con los valores de mercado más recientes sin requerir intervención humana.


---

## 🔮 Limitaciones del Modelo y Próximos Pasos (V2.0)

* **Incorporación del Costo de Oportunidad del Capital Inmovilizado:** Desarrollar un módulo financiero que evalúe el rendimiento marginal de colocar el capital equivalente al valor de compra del vehículo en instrumentos de renta fija conservadora (ej. **Obligaciones Negociables - ONs** corporativas en USD con tasas de interés nominales del 8%-9% anual). Esto sumaría el costo de oportunidad financiero directo a favor de la alternativa de servicios de transporte (MaaS), ya que el capital no utilizado en el activo físico generaría flujos de fondos positivos para financiar el OPEX de movilidad.
* **Análisis de Elasticidad y Sensibilidad Tarifaria:** Desarrollar una matriz de sensibilidad indexada que cruce variaciones en el precio del litro de combustible y variaciones en la tarifa por kilómetro de las aplicaciones de transporte para identificar zonas de indiferencia económica de forma automatizada.
