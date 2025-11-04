from __future__ import annotations
import argparse, sys, json
import pandas as pd

from amort.rates import RateSpec, _ppya, tasa_periodica_normalizada
from amort.schedule import generar_tabla_frances, Abono

UNIDADES = ["dias","semanas","quincenas","meses","bimestres","trimestres","semestres","anios"]
PERIODOS = ["diaria","semanal","quincenal","mensual","bimestral","trimestral","semestral","anual"]

def build_parser():
    p = argparse.ArgumentParser(description="Tabla de Amortización (método francés)")
    # Crédito y tasa
    p.add_argument("--monto", type=float, required=True)
    p.add_argument("--tasa_valor", type=float, required=True, help="Porcentaje (ej. 24.33)")
    p.add_argument("--tasa_tipo", choices=["nominal","efectiva"], required=True)
    p.add_argument("--tasa_cap", choices=PERIODOS, required=True)
    p.add_argument("--tasa_venc", choices=["vencida","anticipada"], default="vencida")
    p.add_argument("--base_dias", type=int, choices=[360,365], default=360)

    # Plazo como N cuotas o duración+unidad
    p.add_argument("--n_periodos", type=int, default=None, help="Número de cuotas (N)")
    p.add_argument("--duracion", type=float, default=None, help="Cantidad del plazo (ej. 6)")
    p.add_argument("--duracion_unidad", choices=UNIDADES, default=None, help="Unidad (meses, trimestres, etc.)")

    # Pago y fechas
    p.add_argument("--frecuencia", choices=PERIODOS, required=True)
    p.add_argument("--fecha_inicio", type=str, help="DD/MM/YYYY", default=None)

    # Extras
    p.add_argument("--abonos_json", type=str, help='[{"periodo":6,"monto":1000,"tipo":"plazo"}]')
    p.add_argument("--export_csv", type=str)
    p.add_argument("--export_xlsx", type=str)
    p.add_argument("--preview", type=int, default=0, help="Solo N filas (0=todas)")
    p.add_argument("--miles", action="store_true", help="Formatear valores con separador de miles")
    return p

def n_from_duracion(freq_pago: str, base_dias: int, duracion: float, unidad: str) -> int:
    """Convierte 'duracion + unidad' a número de cuotas según la frecuencia de pago."""
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

def format_miles(df: pd.DataFrame, use_miles: bool) -> pd.DataFrame:
    if not use_miles:
        return df
    out = df.copy()
    for c in ["Cuota","Interés","Amortización","AbonoExtra","Saldo"]:
        if c in out.columns:
            out[c] = out[c].map(lambda x: f"{float(x):,.2f}")
    return out

def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    # --- Validaciones ---
    if args.monto <= 0:
        parser.error("monto debe ser > 0")
    if args.tasa_valor < 0:
        parser.error("tasa_valor no puede ser negativa")

    # Resolver n_periodos (N) o duración+unidad
    if args.n_periodos is not None:
        n_periodos = args.n_periodos
        if n_periodos <= 0:
            parser.error("n_periodos debe ser > 0")
    else:
        if args.duracion is None or args.duracion_unidad is None:
            parser.error("Debes indicar --n_periodos o (--duracion y --duracion_unidad).")
        n_periodos = n_from_duracion(args.frecuencia, args.base_dias, args.duracion, args.duracion_unidad)

    # Especificación de tasa
    rs = RateSpec(
        valor=args.tasa_valor,
        tipo=args.tasa_tipo,
        capitalizacion=args.tasa_cap,
        vencimiento=args.tasa_venc,
        base_dias=args.base_dias,
    )

    # Transparencia: tasa periódica y EA equivalente
    i_p = tasa_periodica_normalizada(rs, args.frecuencia)
    ppy = _ppya(args.frecuencia, args.base_dias)
    i_ea = (1 + i_p) ** ppy - 1
    print(f"Tasa por periodo ({args.frecuencia}) = {i_p*100:.6f}% | EA equivalente = {i_ea*100:.6f}%")
    print(f"Plazo: {n_periodos} cuotas ({args.frecuencia})")

    # Abonos
    abonos = []
    if args.abonos_json:
        try:
            raw = json.loads(args.abonos_json)
            for a in raw:
                tipo = a.get("tipo","plazo")
                if tipo not in ("plazo","cuota"):
                    parser.error("Cada abono debe tener tipo 'plazo' o 'cuota'.")
                abonos.append(Abono(periodo=int(a["periodo"]), monto=float(a["monto"]), tipo=tipo))
        except Exception as e:
            raise SystemExit(f"--abonos_json inválido: {e}")

    # Tabla (asegurar DataFrame)
    tabla = generar_tabla_frances(
        monto=args.monto,
        i_periodo=i_p,
        n_periodos=n_periodos,
        frecuencia=args.frecuencia,
        fecha_inicio=args.fecha_inicio,
        abonos=abonos,
    )
    df = tabla if isinstance(tabla, pd.DataFrame) else pd.DataFrame(tabla)

    # Impresión
    out = format_miles(df, args.miles)
    if args.preview and args.preview > 0:
        print(out.head(args.preview).to_string(index=False))
    else:
        print(out.to_string(index=False, max_rows=None))

    # Resumen (con df numérico, no con 'out' formateado)
    tot_interes = float(pd.to_numeric(df["Interés"]).sum())
    tot_abonos  = float(pd.to_numeric(df["AbonoExtra"]).sum())
    tot_cuotas  = float(pd.to_numeric(df["Cuota"]).sum())
    tot_pagado  = tot_cuotas + tot_abonos
    if args.miles:
        print(f"\nResumen → Intereses: {tot_interes:,.2f} | Abonos: {tot_abonos:,.2f} | Total pagado: {tot_pagado:,.2f}")
    else:
        print(f"\nResumen → Intereses: {tot_interes:.2f} | Abonos: {tot_abonos:.2f} | Total pagado: {tot_pagado:.2f}")

    # Export
    if args.export_csv:
        from amort.utils import export_csv
        export_csv(df, args.export_csv)
        print(f"CSV -> {args.export_csv}")
    if args.export_xlsx:
        from amort.utils import export_excel
        export_excel(df, args.export_xlsx)
        print(f"Excel -> {args.export_xlsx}")

if __name__ == "__main__":
    main()