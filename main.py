# main.py
from calculos import generar_tabla_amortizacion
from utils import exportar_a_csv, leer_abonos
from datetime import datetime

def main():
    print("=== Calculadora de Tabla de Amortización ===")
    
    # Entradas con validación
    while True:
        try:
            monto = float(input("Monto del préstamo: "))
            tasa_anual = float(input("Tasa anual (%): "))
            plazo_anios = int(input("Plazo (años): "))
            frecuencia = input("Frecuencia de pago (mensual, trimestral, semestral, anual): ").strip().lower()
            tipo_tasa = input("Tipo de tasa (nominal o efectiva): ").strip().lower()
            fecha_inicio = input("Fecha de inicio (dd/mm/yyyy): ").strip()
            datetime.strptime(fecha_inicio, "%d/%m/%Y")  # validación
            break
        except ValueError:
            print("❌ Entrada inválida. Inténtalo nuevamente.\n")
    
    # Leer abonos opcionales
    abonos = leer_abonos()

    # Generar tabla
    tabla = generar_tabla_amortizacion(monto, tasa_anual, plazo_anios, frecuencia, tipo_tasa, fecha_inicio, abonos)

    # Exportar resultados
    exportar_a_csv(tabla, "tabla_amortizacion.csv")

    print("\n✅ Tabla generada correctamente en 'tabla_amortizacion.csv'")
    print(tabla.head())

if __name__ == "__main__":
    main()

