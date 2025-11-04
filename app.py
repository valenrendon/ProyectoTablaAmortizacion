from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

from amort.rates import RateSpec, tasa_periodica_normalizada, _ppya
from amort.schedule import generar_tabla_frances, Abono
from amort.utils import export_csv, export_excel

UNIDADES = ["dias","semanas","quincenas","meses","bimestres","trimestres","semestres","anios"]
PERIODOS = ["diaria","semanal","quincenal","mensual","bimestral","trimestral","semestral","anual"]

# --------- Inputs ---------
def pfloat(msg: str, default: float | None = None) -> float:
    while True:
        s = input(f"{msg}{f' [{default}]' if default is not None else ''}: ").strip()
        if not s and default is not None:
            return float(default)
        try:
            return float(s.replace(",", ""))
        except ValueError:
            print("⚠️ Número inválido.")

def pint(msg: str, default: int | None = None) -> int:
    while True:
        s = input(f"{msg}{f' [{default}]' if default is not None else ''}: ").strip()
        if not s and default is not None:
            return int(default)
        try:
            return int(s)
        except ValueError:
            print("⚠️ Entero inválido.")

def pstr(msg: str, default: str | None = None) -> str | None:
    s = input(f"{msg}{f' [{default}]' if default is not None else ''}: ").strip()
    return s or default

def pyesno(msg: str, default_yes: bool = False) -> bool:
    d = "s" if default_yes else "n"
    s = input(f"{msg} (s/n) [{d}]: ").strip().lower()
    if not s:
        return default_yes
    return s in ("s","si","sí","y","yes")

def ppick(msg: str, opciones: list[str], default: str | None = None) -> str:
    opts = "/".join(opciones)
    while True:
        s = input(f"{msg} ({opts}){f' [{default}]' if default else ''}: ").strip().lower()
        if not s and default:
            return default
        if s in opciones:
            return s
        print("⚠️ Opción inválida.")

# --------- Helpers ---------
def n_from_duracion(freq_pago: str, base_dias: int, duracion: float, unidad: str) -> int:
    per_year_pago = _ppya(freq_pago, base_dias)
    per_year_unidad = {
        "dias": float(base_dias),
        "semanas": 52.0,
        "quincenas": 24.0,
        "meses": 12.0,
        "bimestres": 6.0,
        "trimestres": 4.0,
        "semestres": 2.0,
        "anios": 1.0,
    }[unidad]
    n = int(round((duracion / per_year_unidad) * per_year_pago))
    return max(1, n)

def format_miles(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in ["Cuota","Interés","Amortización","AbonoExtra","Saldo"]:
        if c in out.columns:
            out[c] = out[c].map(lambda x: f"{float(x):,.2f}")
    return out

# --------- App interactiva ---------
def run_once():
    print("\n==== Tabla de Amortización (método francés) ====\n")

    # Monto
    monto = pfloat("Monto del crédito. Ej:", 7_000_000)

    # Tipo de tasa y PERÍODO de la tasa (flexible)
    tasa_tipo = ppick("Tipo de tasa", ["nominal","efectiva"], "efectiva")
    tasa_cap  = ppick("Periodo de la tasa", PERIODOS, "anual")  # para nominal = capitalización; para efectiva = periodo de efectividad
    venc      = ppick("Vencimiento de la tasa", ["vencida","anticipada"], "vencida")

    # Valor de la tasa (etiqueta distinta según tipo)
    if tasa_tipo == "nominal":
        tasa_valor = pfloat("j nominal anual (%)", 24.0)
    else:
        tasa_valor = pfloat(f"Tasa efectiva {tasa_cap} (%)", 24.33 if tasa_cap=="anual" else 1.74)

    # Frecuencia de pago y plazo
    frecuencia = ppick("Frecuencia de pago", PERIODOS, "mensual")

    modo_plazo = ppick("¿Definir plazo por número de cuotas o por duración+unidad?",
                       ["n","duracion"], "n")
    if modo_plazo == "n":
        n_periodos = pint("Número de cuotas (N)", 24)
    else:
        duracion = pfloat("Duración (número)", 6)
        unidad   = ppick("Unidad de duración", UNIDADES, "meses")
        # base_dias se define más abajo, pero para estimar N no importa si no es diario; si es diario lo fijamos luego
        base_tmp = 360
        n_periodos = n_from_duracion(frecuencia, base_tmp, duracion, unidad)

    # Fecha de inicio (opcional)
    fecha_inicio = pstr("Fecha inicio (DD/MM/YYYY) o vacío si no quieres", "01/01/2025")
    if not fecha_inicio:
        fecha_inicio = None

    # Base de días SOLO si hay algo diario
    needs_base = (tasa_cap == "diaria") or (frecuencia == "diaria")
    base_dias = pint("Base de días (360=comercial, 365=real)", 360) if needs_base else 360

    # Abonos (opcionales)
    abonos: list[Abono] = []
    if pyesno("¿Agregar abonos extraordinarios?", False):
        while True:
            per = pint("Periodo (N) en el que se aplica", 6)
            mon = pfloat("Monto del abono", 1_000_000)
            tip = ppick("Tras el abono, ¿recalcular 'plazo' o 'cuota'?", ["plazo","cuota"], "plazo")
            abonos.append(Abono(periodo=per, monto=mon, tipo=tip))
            if not pyesno("¿Agregar otro abono?", False):
                break

    # Especificación de tasa y conversión a i_periodo objetivo (frecuencia de pago)
    rs = RateSpec(
        valor=tasa_valor,
        tipo=tasa_tipo,
        capitalizacion=tasa_cap,
        vencimiento=venc,
        base_dias=base_dias,
    )
    i_p = tasa_periodica_normalizada(rs, frecuencia)
    ppy = _ppya(frecuencia, base_dias)
    i_ea = (1 + i_p) ** ppy - 1

    print(f"\nTasa por periodo ({frecuencia}) = {i_p*100:.6f}% | EA equivalente = {i_ea*100:.6f}%")
    print(f"Plazo: {n_periodos} cuotas ({frecuencia})")

    # Generar tabla
    df = generar_tabla_frances(
        monto=monto,
        i_periodo=i_p,
        n_periodos=n_periodos,
        frecuencia=frecuencia,
        fecha_inicio=fecha_inicio,
        abonos=abonos,
    )
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    # Mostrar formateado
    out = format_miles(df)
    print("\n" + out.to_string(index=False, max_rows=None))

    # Resumen (numérico)
    tot_interes = float(pd.to_numeric(df["Interés"]).sum())
    tot_abonos  = float(pd.to_numeric(df["AbonoExtra"]).sum())
    tot_cuotas  = float(pd.to_numeric(df["Cuota"]).sum())
    tot_pagado  = tot_cuotas + tot_abonos
    print(f"\nResumen → Intereses: {tot_interes:,.2f} | Abonos: {tot_abonos:,.2f} | Total pagado: {tot_pagado:,.2f}")

    # Export automático
    outputs = Path("outputs"); outputs.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"tabla_{frecuencia}_{n_periodos}_{ts}"
    csv_path  = outputs / f"{stem}.csv"
    xlsx_path = outputs / f"{stem}.xlsx"
    export_csv(df, str(csv_path))
    export_excel(df, str(xlsx_path))
    print(f"\nArchivos guardados:\n- CSV  -> {csv_path}\n- Excel-> {xlsx_path}")

def main():
    try:
        run_once()
    except KeyboardInterrupt:
        print("\nCancelado.")
        sys.exit(1)

if __name__ == "__main__":
    main()