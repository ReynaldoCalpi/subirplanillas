import io
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Transformador de Planilla a Póliza Contable",
    page_icon="📊",
    layout="wide",
)

st.title("Generador de Líneas de Registro Contable desde Planilla")
st.markdown(
    "Sube tu archivo de planilla mensual para generar el archivo de salida con el formato de póliza de diario (Cargos y Abonos)."
)

# 1. Sección de Carga de Archivos
st.sidebar.header("1. Carga de Datos")
uploaded_file = st.sidebar.file_uploader(
    "Selecciona el archivo de Planilla (Excel o CSV)", type=["xlsx", "xls", "csv"]
)

# Configuración de cuentas contables estándar (configurable)
st.sidebar.header("2. Parámetros Contables")
cuenta_salarios = st.sidebar.text_input(
    "Cuenta Gasto Salarios", value="5101-01"
)
cuenta_isss_patronal = st.sidebar.text_input(
    "Cuenta Gasto ISSS Patronal", value="5102-01"
)
cuenta_afp_patronal = st.sidebar.text_input(
    "Cuenta Gasto AFP Patronal", value="5102-02"
)
cuenta_insaforp = st.sidebar.text_input(
    "Cuenta Gasto INSAFORP", value="5102-03"
)
cuenta_isss_por_pagar = st.sidebar.text_input(
    "Cuenta Pasivo ISSS Retenido/Por Pagar", value="2103-01"
)
cuenta_afp_por_pagar = st.sidebar.text_input(
    "Cuenta Pasivo AFP Por Pagar", value="2103-02"
)
cuenta_renta_por_pagar = st.sidebar.text_input(
    "Cuenta Pasivo Retención Renta", value="2104-01"
)
cuenta_bancos = st.sidebar.text_input(
    "Cuenta Bancos (Neto a Pagar)", value="1101-01"
)

if uploaded_file is not None:
  try:
    # Leer el archivo base
    if uploaded_file.name.endswith(".csv"):
      df_planilla = pd.read_csv(uploaded_file)
    else:
      df_planilla = pd.read_excel(uploaded_file)

    st.subheader("Vista Previa de la Planilla Original")
    st.dataframe(df_planilla.head())

    # Mapeo de columnas interactivas
    st.subheader("Mapeo de Columnas")
    col1, col2, col3 = st.columns(3)

    columnas_disponibles = list(df_planilla.columns)

    with col1:
      col_empleado = st.selectbox(
          "Columna: Nombre / Código Empleado", columnas_disponibles
      )
      col_salario_bruto = st.selectbox(
          "Columna: Salario Bruto / Ordinario", columnas_disponibles
      )

    with col2:
      col_isss = st.selectbox("Columna: ISSS Laboral (3%)", columnas_disponibles)
      col_afp = st.selectbox("Columna: AFP Laboral (7.25%)", columnas_disponibles)

    with col3:
      col_renta = st.selectbox("Columna: Renta Retenida", columnas_disponibles)
      col_neto = st.selectbox("Columna: Neto a Pagar", columnas_disponibles)

    if st.button("Generar Líneas de Registro Contable"):
      # Procesamiento y acumulación para póliza resumen (o detallada por empleado según prefieras)
      # Aquí generamos el asiento resumen mensual por naturaleza de cuenta

      total_bruto = df_planilla[col_salario_bruto].sum()
      total_isss_lab = df_planilla[col_isss].sum()
      total_afp_lab = df_planilla[col_afp].sum()
      total_renta = df_planilla[col_renta].sum()
      total_neto = df_planilla[col_neto].sum()

      # Cálculo de patronales estándar SV (estimación automática si no vienen en planilla)
      # Nota: Se puede ajustar si la planilla ya trae las columnas patronales
      total_isss_pat = total_bruto * 0.075
      total_afp_pat = total_bruto * 0.0775
      total_insaforp_pat = total_bruto * 0.01

      # Construcción del DataFrame de salida (Líneas de Registro)
      registros = [
          {
              "Codigo_Cuenta": cuenta_salarios,
              "Nombre_Cuenta": "Sueldos y Salarios (Gastos)",
              "Debe": round(total_bruto, 2),
              "Haber": 0.0,
              "Concepto": "PIM: Registro de planilla de sueldos",
          },
          {
              "Codigo_Cuenta": cuenta_isss_patronal,
              "Nombre_Cuenta": "ISSS Patronal",
              "Debe": round(total_isss_pat, 2),
              "Haber": 0.0,
              "Concepto": "PIM: Cuota patronal ISSS",
          },
          {
              "Codigo_Cuenta": cuenta_afp_patronal,
              "Nombre_Cuenta": "AFP Patronal",
              "Debe": round(total_afp_pat, 2),
              "Haber": 0.0,
              "Concepto": "PIM: Cuota patronal AFP",
          },
          {
              "Codigo_Cuenta": cuenta_insaforp,
              "Nombre_Cuenta": "INSAFORP",
              "Debe": round(total_insaforp_pat, 2),
              "Haber": 0.0,
              "Concepto": "PIM: Aporte INSAFORP",
          },
          {
              "Codigo_Cuenta": cuenta_isss_por_pagar,
              "Nombre_Cuenta": "ISSS por Pagar (Laboral + Patronal)",
              "Debe": 0.0,
              "Haber": round(total_isss_lab + total_isss_pat, 2),
              "Concepto": "PIM: Retenciones y aportes ISSS",
          },
          {
              "Codigo_Cuenta": cuenta_afp_por_pagar,
              "Nombre_Cuenta": "AFP por Pagar (Laboral + Patronal)",
              "Debe": 0.0,
              "Haber": round(total_afp_lab + total_afp_pat, 2),
              "Concepto": "PIM: Retenciones y aportes AFP",
          },
          {
              "Codigo_Cuenta": cuenta_renta_por_pagar,
              "Nombre_Cuenta": "Retención de Renta por Pagar",
              "Debe": 0.0,
              "Haber": round(total_renta, 2),
              "Concepto": "PIM: Retención de impuesto sobre la renta",
          },
          {
              "Codigo_Cuenta": cuenta_bancos,
              "Nombre_Cuenta": "Bancos / Efectivo y Equivalentes",
              "Debe": 0.0,
              "Haber": round(total_neto, 2),
              "Concepto": "PIM: Pago de planilla de sueldos",
          },
      ]

      df_poliza = pd.DataFrame(registros)

      # Cuadre de partida
      suma_debe = df_poliza["Debe"].sum()
      suma_haber = df_poliza["Haber"].sum()

      st.subheader("Resultado: Póliza de Diario Generada")
      st.dataframe(df_poliza, use_container_width=True)

      col_a, col_b = st.columns(2)
      col_a.metric(
          label="Total Cargos (Debe)", value=f"${suma_debe:,.2f}"
      )
      col_b.metric(
          label="Total Abonos (Haber)", value=f"${suma_haber:,.2f}"
      )

      if abs(suma_debe - suma_haber) < 0.05:
        st.success("¡Partida cuadrada correctamente!")
      else:
        st.error(
            "Advertencia: La partida presenta una diferencia entre Debe y"
            " Haber. Revisa los parámetros."
        )

      # Exportar a Excel
      output = io.BytesIO()
      with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_poliza.to_excel(writer, index=False, sheet_name="Lineas_Registro")
      processed_data = output.getvalue()

      st.download_button(
          label="📥 Descargar Excel de Línea de Registro",
          data=processed_data,
          file_name="poliza_planilla_salarios.xlsx",
          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      )

  except Exception as e:
    st.error(
        f"Ocurrió un error al procesar el archivo. Verifica el formato: {e}"
    )
else:
  st.info("Por favor, sube un archivo de planilla en la barra lateral.")
