
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulador de Consumo A/C", layout="centered")
st.title("Simulador de Consumo de Energía de Aire Acondicionado")

st.markdown("""
Esta aplicación estima el consumo energético total diario (en kWh) de un aire acondicionado, considerando:
- Temperatura exterior horaria definida manualmente o desde archivo
- Temperatura interior de consigna (Set Point)
- Franja horaria de uso
- Temperatura set point opcional por hora

**Fórmula del COP estimado:**
$$COP = \\max(2.5 - 0.05 \\cdot (T_{ext} - T_{int}), 1.0)$$

**Consumo horario:**
$$E = \\frac{P_{t\\'ermica}}{COP}$$
""")

st.sidebar.header("Opciones")
cargar_csv = st.sidebar.checkbox("Cargar temperaturas desde CSV")
definir_set_point_por_hora = st.sidebar.checkbox("¿Set point por hora?")

T_ext, T_int_por_hora = [], []

if cargar_csv:
    archivo = st.sidebar.file_uploader("Subir archivo CSV", type="csv")
    if archivo:
        df = pd.read_csv(archivo)
        if "T_ext" in df.columns and "T_int" in df.columns:
            T_ext = df["T_ext"].tolist()
            T_int_por_hora = df["T_int"].tolist()
        else:
            st.error("El archivo debe tener columnas 'T_ext' y 'T_int'")
else:
    st.subheader("Definición manual de temperaturas")
    cols = st.columns(6)
    for i in range(24):
        with cols[i % 6]:
            T_ext.append(st.number_input(f"T_ext {i}:00", min_value=10.0, max_value=45.0, value=30.0, step=0.5, key=f"T_ext_{i}"))
    
    if definir_set_point_por_hora:
        for i in range(24):
            with cols[i % 6]:
                T_int_por_hora.append(st.number_input(f"T_int {i}:00", min_value=18.0, max_value=30.0, value=24.0, step=0.5, key=f"T_int_{i}"))
    else:
        T_int = st.slider("Selecciona la temperatura set point interior (°C)", 20, 30, 24)
        T_int_por_hora = [T_int] * 24

P_termica = st.number_input("Potencia térmica del equipo (kW)", value=3.52, step=0.1)

st.subheader("Franja horaria de uso")
inicio = st.number_input("Hora de inicio (0-23)", 0, 23, 8)
fin = st.number_input("Hora de fin (0-23)", 0, 23, 20)

horas = np.arange(24)
uso = [(i >= inicio or i <= fin) if inicio > fin else (inicio <= i <= fin) for i in horas]
COP = [max(2.5 - 0.05 * (T_ext[i] - T_int_por_hora[i]), 1.0) for i in horas]
consumo_horario = [P_termica / COP[i] if uso[i] else 0 for i in horas]
consumo_total = sum(consumo_horario)

cop_medio = np.mean([COP[i] for i in horas if uso[i]])
if cop_medio < 1.5:
    st.info("⚠️ El COP promedio es bajo. Considera subir el set point o mejorar el aislamiento.")

result_df = pd.DataFrame({
    "Hora": horas,
    "T_ext (°C)": T_ext,
    "T_int (°C)": T_int_por_hora,
    "COP": np.round(COP, 2),
    "Consumo horario (kWh)": np.round(consumo_horario, 2)
})
st.subheader("Resultados por hora")
st.dataframe(result_df.set_index("Hora"))

st.download_button(
    "📥 Descargar CSV",
    data=result_df.to_csv(index=False),
    file_name="consumo_ac.csv",
    mime="text/csv"
)

st.subheader("Gráficos")
fig, ax1 = plt.subplots()
ax1.plot(horas, T_ext, label="T_ext (°C)", color="orange")
ax1.plot(horas, T_int_por_hora, label="T_int (°C)", color="blue", linestyle="--")
ax1.set_ylabel("Temperatura (°C)")
ax1.set_xlabel("Hora")
ax1.legend(loc="upper left")

for i in horas:
    if uso[i]:
        ax1.axvspan(i - 0.5, i + 0.5, color="green", alpha=0.1)

ax2 = ax1.twinx()
ax2.plot(horas, consumo_horario, label="Consumo (kWh)", color="green")
ax2.set_ylabel("Consumo horario (kWh)")
ax2.legend(loc="upper right")

st.pyplot(fig)

st.success(f"✅ Consumo total estimado: {consumo_total:.2f} kWh/día")
