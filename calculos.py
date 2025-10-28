# calculos.py
import pandas as pd
from datetime import datetime, timedelta

def tasa_equivalente(tasa_anual, frecuencia, tipo_tasa):
    frecuencia_dict = {"mensual": 12, "bimestral": 6, "trimestral": 4, "semestral": 2, "anual": 1}
    n = frecuencia_dict.get(frecuencia, 12)
    if tipo_tasa == "efectiva":
        i = (1 + tasa_anual / 100) ** (1 / n) - 1
    else:
        i = (tasa_anual / 100) / n
    return i, n

def calcular_fecha_pago(fecha_inicio, frecuencia, periodo):
    fecha = datetime.strptime(fecha_inicio, "%d/%m/%Y")
    meses = {"mensual": 1, "bimestral": 2, "trimestral": 3, "semestral": 6, "anual": 12}
    delta = meses.get(frecuencia, 1) * periodo
    return fecha + pd.DateOffset(months=delta)

def generar_tabla_amortizacion(monto, tasa_anual, plazo_anios, frecuencia, tipo_tasa, fecha_inicio, abonos=[]):
    i, n = tasa_equivalente(tasa_anual, frecuencia, tipo_tasa)
    total_periodos = plazo_anios * n
    cuota = monto * (i * (1 + i) ** total_periodos) / ((1 + i) ** total_periodos - 1)

    saldo = monto
    tabla = []
    
    for periodo in range(1, total_periodos + 1):
        interes = saldo * i
        amortizacion = cuota - interes
        saldo -= amortizacion
        
        # Revisar abonos en este periodo
        for abono in abonos:
            if abono["periodo"] == periodo:
                saldo -= abono["monto"]
                if abono.get("tipo", "cuota") == "plazo":
                    # recalcular cuota para nuevo saldo manteniendo mismo plazo
                    total_periodos -= periodo
                    if total_periodos > 0:
                        cuota = saldo * (i * (1 + i) ** total_periodos) / ((1 + i) ** total_periodos - 1)
        
        tabla.append({
            "Periodo": periodo,
            "Fecha de Pago": calcular_fecha_pago(fecha_inicio, frecuencia, periodo).strftime("%d/%m/%Y"),
            "Cuota": round(cuota, 2),
            "Interés": round(interes, 2),
            "Amortización": round(amortizacion, 2),
            "Saldo": round(max(saldo, 0), 2)
        })

        if saldo <= 0:
            break

    return pd.DataFrame(tabla)
