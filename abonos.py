import pandas as pd
import numpy as np

def aplicar_abonos(tabla, tasa_periodica, tipo_recalculo):
    """
    Aplica abonos programados o ad-hoc y recalcula la tabla.
    tipo_recalculo: 'cuota' o 'plazo'
    """
    abonos = input("¿Deseas ingresar abonos? (s/n): ").strip().lower()
    if abonos != "s":
        return tabla

    while True:
        periodo = int(input("Periodo del abono: "))
        monto_abono = float(input("Monto del abono: "))

        # Aplicar el abono al saldo del período indicado
        saldo_actual = tabla.loc[periodo - 1, "Saldo"]
        nuevo_saldo = saldo_actual - monto_abono
        tabla.loc[periodo - 1, "Saldo"] = max(nuevo_saldo, 0)

        # Recalcular tabla a partir del siguiente periodo
        if tipo_recalculo == "cuota":
            tabla = recalcular_cuota(tabla, tasa_periodica, periodo)
        elif tipo_recalculo == "plazo":
            tabla = recalcular_plazo(tabla, tasa_periodica, periodo)
        else:
            print("⚠️ Tipo de recálculo no reconocido. Se mantiene el saldo actual.")

        continuar = input("¿Agregar otro abono? (s/n): ").strip().lower()
        if continuar != "s":
            break

    return tabla


def recalcular_cuota(tabla, tasa_periodica, periodo):
    """Recalcula la cuota manteniendo el plazo (reducción de cuota)."""
    saldo_restante = tabla.loc[periodo - 1, "Saldo"]
    n_restante = len(tabla) - periodo
    if n_restante <= 0:
        return tabla

    nueva_cuota = saldo_restante * (tasa_periodica * (1 + tasa_periodica) ** n_restante) / ((1 + tasa_periodica) ** n_restante - 1)
    datos = []
    saldo = saldo_restante

    for k in range(1, n_restante + 1):
        interes = saldo * tasa_periodica
        amort = nueva_cuota - interes
        saldo -= amort
        datos.append([periodo + k, round(nueva_cuota, 2), round(interes, 2), round(amort, 2), round(max(saldo, 0), 2)])

    nueva_tabla = pd.DataFrame(datos, columns=["Periodo", "Cuota", "Interés", "Amortización", "Saldo"])
    return pd.concat([tabla.iloc[:periodo], nueva_tabla], ignore_index=True)


def recalcular_plazo(tabla, tasa_periodica, periodo):
    """Recalcula reduciendo el plazo (mantiene la misma cuota)."""
    saldo_restante = tabla.loc[periodo - 1, "Saldo"]
    cuota = tabla.loc[periodo - 1, "Cuota"]

    saldo = saldo_restante
    datos = []
    k = 0

    while saldo > 0:
        interes = saldo * tasa_periodica
        amort = cuota - interes
        saldo -= amort
        k += 1
        datos.append([periodo + k, round(cuota, 2), round(interes, 2), round(amort, 2), round(max(saldo, 0), 2)])

    nueva_tabla = pd.DataFrame(datos, columns=["Periodo", "Cuota", "Interés", "Amortización", "Saldo"])
    return pd.concat([tabla.iloc[:periodo], nueva_tabla], ignore_index=True)

