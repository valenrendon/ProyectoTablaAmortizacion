from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Literal, Sequence, Dict
from datetime import datetime, date, timedelta
import calendar
import math

import pandas as pd


PeriodoLiteral = Literal["diaria","semanal","quincenal","mensual","bimestral","trimestral","semestral","anual"]

@dataclass(frozen=True)
class Abono:
    periodo: int
    monto: float
    tipo: Literal["plazo","cuota"] = "plazo"


# -------------------- Utilidades de fechas --------------------

def _parse_fecha_ddmmyyyy(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    return datetime.strptime(s, "%d/%m/%Y").date()

def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    last_day = calendar.monthrange(y, m)[1]
    day = min(d.day, last_day)
    return date(y, m, day)

def _add_one_period(d: Optional[date], frecuencia: PeriodoLiteral) -> Optional[date]:
    if d is None:
        return None
    if frecuencia == "diaria":
        return d + timedelta(days=1)
    if frecuencia == "semanal":
        return d + timedelta(days=7)
    if frecuencia == "quincenal":
        return d + timedelta(days=15)
    if frecuencia == "mensual":
        return _add_months(d, 1)
    if frecuencia == "bimestral":
        return _add_months(d, 2)
    if frecuencia == "trimestral":
        return _add_months(d, 3)
    if frecuencia == "semestral":
        return _add_months(d, 6)
    if frecuencia == "anual":
        return _add_months(d, 12)
    raise ValueError(f"Frecuencia no soportada: {frecuencia!r}")

def _is_eom(d: date) -> bool:
    return d.day == calendar.monthrange(d.year, d.month)[1]

def _add_months_eom(d: date, months: int, anchor_eom: bool) -> date:
    # Si el crédito inició en fin de mes, siempre saltar al fin de mes del mes destino
    if anchor_eom:
        m = d.month - 1 + months
        y = d.year + m // 12
        m = m % 12 + 1
        last_day = calendar.monthrange(y, m)[1]
        return date(y, m, last_day)
    # Caso normal (no anclado a fin de mes)
    return _add_months(d, months)

def _add_one_period_eom(d: Optional[date], frecuencia: PeriodoLiteral, anchor_eom: bool) -> Optional[date]:
    if d is None:
        return None
    if frecuencia == "diaria":
        return d + timedelta(days=1)
    if frecuencia == "semanal":
        return d + timedelta(days=7)
    if frecuencia == "quincenal":
        return d + timedelta(days=15)
    if frecuencia == "mensual":
        return _add_months_eom(d, 1, anchor_eom)
    if frecuencia == "bimestral":
        return _add_months_eom(d, 2, anchor_eom)
    if frecuencia == "trimestral":
        return _add_months_eom(d, 3, anchor_eom)
    if frecuencia == "semestral":
        return _add_months_eom(d, 6, anchor_eom)
    if frecuencia == "anual":
        return _add_months_eom(d, 12, anchor_eom)
    raise ValueError(f"Frecuencia no soportada: {frecuencia!r}")



# -------------------- Fórmulas financieras --------------------

def _cuota_frances(P: float, i: float, n: int) -> float:
    if n <= 0:
        raise ValueError("n debe ser > 0")
    if i == 0:
        return P / n
    f = (1 + i) ** n
    return P * i * f / (f - 1)


# -------------------- Generador de tabla --------------------

def generar_tabla_frances(
    monto: float,
    i_periodo: float,
    n_periodos: int,
    frecuencia: PeriodoLiteral,
    fecha_inicio: Optional[str] = None,
    abonos: Sequence[Abono] | None = None,
) -> pd.DataFrame:
    """
    Retorna SIEMPRE un pandas.DataFrame con columnas:
    Periodo | Fecha | Cuota | Interés | Amortización | AbonoExtra | Saldo

    - tipo='plazo': mantiene cuota; reduce el número de cuotas (termina antes).
    - tipo='cuota': mantiene plazo; recalcula la cuota a partir del periodo del abono.
    """
    if monto <= 0:
        raise ValueError("monto debe ser > 0")
    if n_periodos <= 0:
        raise ValueError("n_periodos debe ser > 0")
    if i_periodo < 0:
        raise ValueError("i_periodo no puede ser negativo")

    # Mapa de abonos por periodo
    abonos_map: Dict[int, List[Abono]] = {}
    for a in (abonos or ()):
        abonos_map.setdefault(int(a.periodo), []).append(a)

    saldo = float(monto)
    i = float(i_periodo)
    n_total = int(n_periodos)
    # cuota vigente
    cuota = _cuota_frances(saldo, i, n_total)

    # fecha del primer pago = fecha_inicio + 1 periodo (si hay fecha)
    f_actual = _parse_fecha_ddmmyyyy(fecha_inicio)
# Anclar a fin de mes si la fecha de inicio es fin de mes y la frecuencia es mensual (o múltiplos de mes)
    _usa_eom = False
    if f_actual and frecuencia in {"mensual","bimestral","trimestral","semestral","anual"}:
        _usa_eom = _is_eom(f_actual)

    filas: List[dict] = []
    tol_cierre = 1e-2  # forzar cierre +- centavos

    # Bucle por periodos. Para tipo 'plazo', la cantidad real de filas puede ser < n_total.
    k = 1
    while k <= n_total and saldo > tol_cierre:
        # avanzar fecha
        f_actual = _add_one_period_eom(f_actual, frecuencia, _usa_eom)
        interes = saldo * i
        amort = cuota - interes

        if amort <= 0:
            raise ValueError("La cuota no amortiza (amortización <= 0). Revisa tasa/periodo.")

        # Si la amortización excede el saldo (última cuota cuando se acorta plazo)
        if amort > saldo:
            amort = saldo
            cuota_ef = interes + amort  # última cuota exacta
        else:
            cuota_ef = cuota

        saldo_nuevo = saldo - amort
        ab_extra = 0.0

        # Aplicar abonos del periodo k (se registran en la fila del periodo)
        if k in abonos_map and abonos_map[k]:
            for a in abonos_map[k]:
                ab_m = float(a.monto)
                if ab_m < 0:
                    raise ValueError("Abono negativo no permitido.")
                ab_extra += ab_m
                saldo_nuevo -= ab_m
            # Clamp por redondeos
            if saldo_nuevo < 0 and abs(saldo_nuevo) <= 1e-6:
                saldo_nuevo = 0.0

        # Registrar fila
        filas.append({
            "Periodo": k,
            "Fecha": f_actual.strftime("%d/%m/%Y") if f_actual else None,
            "Cuota": float(cuota_ef),
            "Interés": float(interes),
            "Amortización": float(amort),
            "AbonoExtra": float(ab_extra),
            "Saldo": float(max(saldo_nuevo, 0.0)),
        })

        saldo = saldo_nuevo

        # Si hubo abonos tipo 'cuota', recalcular cuota para los periodos restantes (manteniendo plazo)
        if k in abonos_map:
            hay_cuota = any(a.tipo == "cuota" for a in abonos_map[k])
            if hay_cuota:
                rem = n_total - k
                if saldo > tol_cierre and rem > 0:
                    cuota = _cuota_frances(saldo, i, rem)

        # Si el saldo ya es prácticamente cero, salimos
        if saldo <= tol_cierre:
            saldo = 0.0
            break

        k += 1

    # Si por redondeos quedó un residuo minúsculo, forzamos a 0 la última fila
    if filas:
        filas[-1]["Saldo"] = 0.0 if abs(filas[-1]["Saldo"]) < tol_cierre else filas[-1]["Saldo"]

    # Armar DataFrame garantizando columnas y tipos
    cols = ["Periodo","Fecha","Cuota","Interés","Amortización","AbonoExtra","Saldo"]
    df = pd.DataFrame(filas, columns=cols)

    # Asegurar tipos numéricos (útil para sumar en tests)
    for c in ["Cuota","Interés","Amortización","AbonoExtra","Saldo"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    return df