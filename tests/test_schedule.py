import math
import pandas as pd
from amort.rates import RateSpec, tasa_periodica_normalizada, _ppya
from amort.schedule import generar_tabla_frances, Abono

def _i_periodo(ea_percent, freq="mensual", base=360):
    rs = RateSpec(valor=ea_percent, tipo="efectiva", capitalizacion="anual", vencimiento="vencida", base_dias=base)
    return tasa_periodica_normalizada(rs, freq)

def test_tabla_cierra_sin_abonos():
    i_m = _i_periodo(24.33, "mensual")
    df = generar_tabla_frances(monto=7_000_000, i_periodo=i_m, n_periodos=24,
                               frecuencia="mensual", fecha_inicio="01/01/2025", abonos=[])
    assert abs(float(df["Saldo"].iloc[-1])) < 1e-2
    assert (df["Amortización"] > 0).all()

def test_abono_reduce_plazo_mantiene_cuota():
    # Nominal 24% cap. mensual ≈ 2% mensual vencida
    rs = RateSpec(valor=24.0, tipo="nominal", capitalizacion="mensual", vencimiento="vencida", base_dias=360)
    i_m = tasa_periodica_normalizada(rs, "mensual")
    ab = [Abono(periodo=6, monto=1_800_000, tipo="plazo")]
    df = generar_tabla_frances(monto=5_000_000, i_periodo=i_m, n_periodos=24,
                               frecuencia="mensual", fecha_inicio="01/01/2025", abonos=ab)
    # Se reduce el número total de cuotas
    assert len(df) < 24
    # La cuota se mantiene (hasta el término)
    cuota_ini = round(float(df["Cuota"].iloc[0]), 6)
    cuota_pos = round(float(df["Cuota"].iloc[min(6, len(df)-1)]), 6)
    assert math.isclose(cuota_ini, cuota_pos, rel_tol=0, abs_tol=1e-6)
    # Cierre
    assert abs(float(df["Saldo"].iloc[-1])) < 1e-2

def test_abono_recalcula_cuota_mantiene_plazo():
    i_m = _i_periodo(24.33, "mensual")
    ab = [Abono(periodo=6, monto=1_000_000, tipo="cuota")]
    df = generar_tabla_frances(monto=7_000_000, i_periodo=i_m, n_periodos=24,
                               frecuencia="mensual", fecha_inicio="01/01/2025", abonos=ab)
    assert len(df) == 24
    # La cuota después del abono debe ser MENOR a la cuota inicial
    cuota_ini = float(df["Cuota"].iloc[0])
    cuota_post = float(df["Cuota"].iloc[6])
    assert cuota_post < cuota_ini
    assert abs(float(df["Saldo"].iloc[-1])) < 1e-2

def test_tasa_cero_cuotas_iguales():
    i_m = 0.0
    df = generar_tabla_frances(monto=900_000, i_periodo=i_m, n_periodos=9,
                               frecuencia="mensual", fecha_inicio="01/10/2025", abonos=[])
    # Todas las cuotas iguales = principal / n
    esperado = 900_000 / 9
    assert (df["Cuota"].round(2) == pd.Series([esperado]*9).round(2)).all()
    assert abs(float(df["Saldo"].iloc[-1])) < 1e-9
    assert df["Interés"].sum() == 0

def test_fechas_fin_de_mes_desde_31_enero():
    i_m = _i_periodo(18.0, "mensual")
    df = generar_tabla_frances(monto=1_000_000, i_periodo=i_m, n_periodos=6,
                               frecuencia="mensual", fecha_inicio="31/01/2025", abonos=[])
    fechas = list(df["Fecha"].astype(str).head(6))
    assert fechas == ["28/02/2025","31/03/2025","30/04/2025","31/05/2025","30/06/2025","31/07/2025"]

def test_diaria_base_360_vs_365_cierra_en_ambas():
    # Misma EA 20%, pero i_diaria 360 > i_diaria 365
    rs360 = RateSpec(valor=20.0, tipo="efectiva", capitalizacion="anual", vencimiento="vencida", base_dias=360)
    rs365 = RateSpec(valor=20.0, tipo="efectiva", capitalizacion="anual", vencimiento="vencida", base_dias=365)
    i_d360 = tasa_periodica_normalizada(rs360, "diaria")
    i_d365 = tasa_periodica_normalizada(rs365, "diaria")
    assert i_d360 > i_d365

    df360 = generar_tabla_frances(monto=1_000_000, i_periodo=i_d360, n_periodos=30,
                                  frecuencia="diaria", fecha_inicio=None, abonos=[])
    df365 = generar_tabla_frances(monto=1_000_000, i_periodo=i_d365, n_periodos=30,
                                  frecuencia="diaria", fecha_inicio=None, abonos=[])
    assert abs(float(df360["Saldo"].iloc[-1])) < 1e-2
    assert abs(float(df365["Saldo"].iloc[-1])) < 1e-2
    assert (df360["Amortización"] > 0).all() and (df365["Amortización"] > 0).all()