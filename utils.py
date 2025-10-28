def exportar_a_csv(df, nombre_archivo):
    df.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')

def leer_abonos():
    abonos = []
    opcion = input("¿Deseas registrar abonos programados o ad-hoc? (s/n): ").strip().lower()
    if opcion == "s":
        while True:
            try:
                periodo = int(input("Periodo del abono: "))
                monto = float(input("Monto del abono: "))
                tipo = input("Tipo de recálculo (cuota o plazo): ").strip().lower()
                abonos.append({"periodo": periodo, "monto": monto, "tipo": tipo})
                otro = input("¿Agregar otro abono? (s/n): ").strip().lower()
                if otro != "s":
                    break
            except ValueError:
                print("Entrada inválida, inténtalo de nuevo.\n")
    return abonos
