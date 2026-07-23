import io
import pandas as pd
import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="Generador de Póliza de Diario Detallada - RI Consultores",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Generador Automatizado de Póliza de Diario Multidimensional")
st.markdown(
    "Transforma tu planilla extensa en un archivo de líneas de registro"
    " contable desglosado por **Centro de Costo y Dimensiones**."
)

# ==========================================
# 1. BARRA LATERAL: CONFIGURACIÓN Y PARÁMETROS
# ==========================================
st.sidebar.header("1. Carga de Planilla")
uploaded_file = st.sidebar.file_uploader(
    "Sube tu archivo de planilla (Excel o CSV)", type=["xlsx", "xls", "csv"]
)

st.sidebar.header("2. Catálogo de Cuentas Contables (Base)")
cuenta_salarios_base = st.sidebar.text_input(
    "Cuenta Base Gasto Salarios", value="5101-01"
)
cuenta_isss_pat_base = st.sidebar.text_input(
    "Cuenta Base ISSS Patronal", value="5102-01"
)
cuenta_afp_pat_base = st.sidebar.text_input(
    "Cuenta Base AFP Patronal", value="5102-02"
)
cuenta_insaforp_base = st.sidebar.text_input(
    "Cuenta Base INSAFORP", value="5102-03"
)

st.sidebar.header("3. Cuentas de Pasivos y Bancos")
cuenta_isss_por_pagar = st.sidebar.text_input(
    "Cuenta Pasivo ISSS (Lab + Pat)", value="2103-01"
)
cuenta_afp_por_pagar = st.sidebar.text_input(
    "Cuenta Pasivo AFP (Lab + Pat)", value="2103-02"
)
cuenta_renta_por_pagar = st.sidebar.text_input(
    "Cuenta Retención Renta por Pagar", value="2104-01"
)
cuenta_bancos = st.sidebar.text_input(
    "Cuenta Bancos (Neto a Pagar)", value="1101-01"
)

# ==========================================
# 2. PROCESAMIENTO PRINCIPAL
# ==========================================
if uploaded_file is not None:
  try:
    # Lectura del archivo según extensión
    if uploaded_file.name.endswith(".csv"):
      df_planilla = pd.read_csv(uploaded_file)
    else:
      df_planilla = pd.read_excel(uploaded_file)

    st.subheader("Vista Previa de la Planilla Original")
    st.dataframe(df_planilla.head(10), use_container_width=True)

    st.markdown("---")
    st.subheader("Mapeo de Columnas de tu Planilla")
    col1, col2, col3, col4 = st.columns(4)

    columnas_disponibles = list(df_planilla.columns)

    with col1:
      col_cc = st.selectbox(
          "Columna: Centro de Costo",
          columnas_disponibles,
          index=(
              0 if len(columnas_disponibles) > 0 else None
          ),
      )
      col_sucursal = st.selectbox(
          "Columna: Sucursal / Dimensión",
          columnas_disponibles,
          index=(
              min(1, len(columnas_disponibles) - 1)
              if len(columnas_disponibles) > 1
              else 0
          ),
      )

    with col2:
      col_salario_bruto = st.selectbox(
          "Columna: Salario Bruto",
          columnas_disponibles,
          index=(
              min(2, len(columnas_disponibles) - 1)
              if len(columnas_disponibles) > 2
              else 0
          ),
      )
      col_neto = st.selectbox(
          "Columna: Neto a Pagar",
          columnas_disponibles,
          index=(
              min(3, len(columnas_disponibles) - 1)
              if len(columnas_disponibles) > 3
              else 0
          ),
      )

    with col3:
      col_isss_lab = st.selectbox(
          "Columna: ISSS Laboral",
          columnas_disponibles,
          index=(
              min(4, len(columnas_disponibles) - 1)
              if len(columnas_disponibles) > 4
              else 0
          ),
      )
      col_afp_lab = st.selectbox(
          "Columna: AFP Laboral",
          columnas_disponibles,
          index=(
              min(5, len(columnas_disponibles) - 1)
              if len(columnas_disponibles) > 5
              else 0
          ),
      )

    with col4:
      col_renta = st.selectbox(
          "Columna: Renta Retenida",
          columnas_disponibles,
          index=(
              min(6, len(columnas_disponibles) - 1)
              if len(columnas_disponibles) > 6
              else 0
          ),
      )
      fecha_asiento = st.text_input("Fecha del Asiento (YYYY-MM-DD)", value="2026-07-31")
      no_asiento = st.text_input("Número de Asiento / Póliza", value="AS-2026-07-001")

    st.markdown("---")

    if st.button(
        "🚀 Generar Póliza Contable Extensa y Multidimensional",
        type="primary",
        use_container_width=True,
    ):
      # Asegurar tipos numéricos
      for col in [
          col_salario_bruto,
          col_isss_lab,
          col_afp_lab,
          col_renta,
          col_neto,
      ]:
        df_planilla[col] = pd.to_numeric(df_planilla[col], errors="fill_value").fillna(0)

      # Agrupar por Centro de Costo y Sucursal para manejar planillas extensas limpiamente
      agrupado = (
          df_planilla.groupby([col_cc, col_sucursal])
          .agg(
              Bruto=(col_salario_bruto, "sum"),
              Isss_Lab=(col_isss_lab, "sum"),
              Afp_Lab=(col_afp_lab, "sum"),
              Renta=(col_renta, "sum"),
              Neto=(col_neto, "sum"),
          )
          .reset_index()
      )

      lineas_poliza = []

      # Totales generales para pasivos y bancos
      gran_total_isss_lab = agrupado["Isss_Lab"].sum()
      gran_total_afp_lab = agrupado["Afp_Lab"].sum()
      gran_total_renta = agrupado["Renta"].sum()
      gran_total_neto = agrupado["Neto"].sum()

      gran_total_isss_pat = 0.0
      gran_total_afp_pat = 0.0
      gran_total_insaforp = 0.0

      # 1. Generación de líneas de Gasto y Patronales por cada Centro de Costo / Dimensión
      for _, row in agrupado.iterrows():
        cc = str(row[col_cc])
        suc = str(row[col_sucursal])
        bruto = row["Bruto"]

        # Cálculos patronales estándar de El Salvador (sobre el bruto o base aplicable)
        isss_pat = bruto * 0.075
        afp_pat = bruto * 0.0775
        insaforp = bruto * 0.01

        gran_total_isss_pat += isss_pat
        gran_total_afp_pat += afp_pat
        gran_total_insaforp += insaforp

        # Línea: Gasto Salarios
        lineas_poliza.append({
            "Fecha": fecha_asiento,
            "Tipo_Doc": "PD",
            "No_Asiento": no_asiento,
            "Codigo_Cuenta": f"{cuenta_salarios_base}-{cc}",
            "Nombre_Cuenta": f"Sueldos y Salarios - {cc}",
            "Centro_Costo": cc,
            "Dimension_Sucursal": suc,
            "Debe": round(bruto, 2),
            "Haber": 0.0,
            "Concepto": f"Planilla de Sueldos - {cc} ({suc})",
        })

        # Línea: Gasto ISSS Patronal
        lineas_poliza.append({
            "Fecha": fecha_asiento,
            "Tipo_Doc": "PD",
            "No_Asiento": no_asiento,
            "Codigo_Cuenta": f"{cuenta_isss_pat_base}-{cc}",
            "Nombre_Cuenta": f"ISSS Patronal - {cc}",
            "Centro_Costo": cc,
            "Dimension_Sucursal": suc,
            "Debe": round(isss_pat, 2),
            "Haber": 0.0,
            "Concepto": f"Cuota patronal ISSS - {cc}",
        })

        # Línea: Gasto AFP Patronal
        lineas_poliza.append({
            "Fecha": fecha_asiento,
            "Tipo_Doc": "PD",
            "No_Asiento": no_asiento,
            "Codigo_Cuenta": f"{cuenta_afp_pat_base}-{cc}",
            "Nombre_Cuenta": f"AFP Patronal - {cc}",
            "Centro_Costo": cc,
            "Dimension_Sucursal": suc,
            "Debe": round(afp_pat, 2),
            "Haber": 0.0,
            "Concepto": f"Cuota patronal AFP - {cc}",
        })

        # Línea: Gasto INSAFORP
        lineas_poliza.append({
            "Fecha": fecha_asiento,
            "Tipo_Doc": "PD",
            "No_Asiento": no_asiento,
            "Codigo_Cuenta": f"{cuenta_insaforp_base}-{cc}",
            "Nombre_Cuenta": f"INSAFORP - {cc}",
            "Centro_Costo": cc,
            "Dimension_Sucursal": suc,
            "Debe": round(insaforp, 2),
            "Haber": 0.0,
            "Concepto": f"Aporte INSAFORP - {cc}",
        })

      # 2. Generación de líneas de Pasivos y Bancos (Acumulados generales)
      total_isss_por_pagar = gran_total_isss_lab + gran_total_isss_pat
      total_afp_por_pagar = gran_total_afp_lab + gran_total_afp_pat

      lineas_poliza.append({
          "Fecha": fecha_asiento,
          "Tipo_Doc": "PD",
          "No_Asiento": no_asiento,
          "Codigo_Cuenta": cuenta_isss_por_pagar,
          "Nombre_Cuenta": "ISSS por Pagar (Laboral + Patronal)",
          "Centro_Costo": "GENERAL",
          "Dimension_Sucursal": "GENERAL",
          "Debe": 0.0,
          "Haber": round(total_isss_por_pagar, 2),
          "Concepto": "Acumulado obligaciones ISSS mes",
      })

      lineas_poliza.append({
          "Fecha": fecha_asiento,
          "Tipo_Doc": "PD",
          "No_Asiento": no_asiento,
          "Codigo_Cuenta": cuenta_afp_por_pagar,
          "Nombre_Cuenta": "AFP por Pagar (Laboral + Patronal)",
          "Centro_Costo": "GENERAL",
          "Dimension_Sucursal": "GENERAL",
          "Debe": 0.0,
          "Haber": round(total_afp_por_pagar, 2),
          "Concepto": "Acumulado obligaciones AFP mes",
      })

      lineas_poliza.append({
          "Fecha": fecha_asiento,
          "Tipo_Doc": "PD",
          "No_Asiento": no_asiento,
          "Codigo_Cuenta": cuenta_renta_por_pagar,
          "Nombre_Cuenta": "Retención de Renta por Pagar",
          "Centro_Costo": "GENERAL",
          "Dimension_Sucursal": "GENERAL",
          "Debe": 0.0,
          "Haber": round(gran_total_renta, 2),
          "Concepto": "Retención de Impuesto sobre la Renta empleados",
      })

      lineas_poliza.append({
          "Fecha": fecha_asiento,
          "Tipo_Doc": "PD",
          "No_Asiento": no_asiento,
          "Codigo_Cuenta": cuenta_bancos,
          "Nombre_Cuenta": "Bancos / Efectivo y Equivalentes",
          "Centro_Costo": "GENERAL",
          "Dimension_Sucursal": "GENERAL",
          "Debe": 0.0,
          "Haber": round(gran_total_neto, 2),
          "Concepto": "Pago neto de planilla de sueldos",
      })

      df_poliza = pd.DataFrame(lineas_poliza)

      # Validación de cuadre
      suma_debe = df_poliza["Debe"].sum()
      suma_haber = df_poliza["Haber"].sum()

      st.success("¡Póliza multidimensional generada con éxito!")

      col_m1, col_m2 = st.columns(2)
      col_m1.metric(label="Total Cargos (Debe)", value=f"${suma_debe:,.2f}")
      col_m2.metric(label="Total Abonos (Haber)", value=f"${suma_haber:,.2f}")

      if abs(suma_debe - suma_haber) > 0.05:
        st.warning(
            "⚠️ Hay una diferencia entre el Debe y el Haber. Revisa los"
            " montos o cálculos patronales."
        )

      st.subheader("Vista Previa de la Póliza Final")
      st.dataframe(df_poliza, use_container_width=True)

      # Exportar a Excel con formato limpio
      output = io.BytesIO()
      with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_poliza.to_excel(writer, index=False, sheet_name="Poliza_Detallada")
      processed_data = output.getvalue()

      st.download_button(
          label="📥 Descargar Póliza en Excel (Estructura Amplia)",
          data=processed_data,
          file_name="poliza_detallada_multidimensional.xlsx",
          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      )

  except Exception as e:
    st.error(f"Error procesando el archivo: {e}")
else:
  st.info("👈 Por favor, carga tu archivo de planilla en la barra lateral.")
