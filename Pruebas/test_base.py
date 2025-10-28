# pruebas/test_base.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from calculos import generar_tabla_amortizacion
from datetime import datetime

def test_cierre_correcto():
    tabla = generar_tabla_amortizacion(10000, 12, 1, "mensual", "nominal", "01/01/2025")
    saldo_final = tabla.iloc[-1]["Saldo"]
    assert abs(saldo_final) < 10, f" El saldo final no cierra correctamente: {saldo_final}"

def test_abono_aplicado():
    abonos = [{"periodo": 6, "monto": 1000, "tipo": "plazo"}]
    tabla = generar_tabla_amortizacion(10000, 12, 1, "mensual", "nominal", "01/01/2025", abonos)
    assert tabla.iloc[-1]["Saldo"] < 5, " El saldo no se redujo correctamente con abono."

def test_fechas_pago():
    tabla = generar_tabla_amortizacion(10000, 12, 1, "mensual", "nominal", "01/01/2025")
    fechas = tabla["Fecha de Pago"].tolist()
    assert datetime.strptime(fechas[0], "%d/%m/%Y"), "Fechas inválidas en tabla."

if __name__ == "__main__":
    test_cierre_correcto()
    test_abono_aplicado()
    test_fechas_pago()
    print(" Todas las pruebas se ejecutaron correctamente.")

