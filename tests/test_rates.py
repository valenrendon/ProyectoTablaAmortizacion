import math
from amort.rates import RateSpec, tasa_periodica_normalizada, _ppya

def approx(a, b, tol=1e-9):
    return abs(a - b) <= tol

def test_nominal_24_cap_mensual_equiv_2pct_mensual():
    rs = RateSpec(valor=24.0, tipo="nominal", capitalizacion="mensual", vencimiento="vencida", base_dias=360)
    i_m = tasa_periodica_normalizada(rs, "mensual")
    assert approx(i_m, 0.02, 1e-12)

def test_ea_26824179_da_2pct_mensual():
    rs = RateSpec(valor=26.824179, tipo="efectiva", capitalizacion="anual", vencimiento="vencida", base_dias=360)
    i_m = tasa_periodica_normalizada(rs, "mensual")
    assert math.isclose(i_m, 0.02, rel_tol=0, abs_tol=1e-6)

def test_anticipada_a_vencida_mensual_2pct():
    rs = RateSpec(valor=2.0, tipo="efectiva", capitalizacion="mensual", vencimiento="anticipada", base_dias=360)
    i_m = tasa_periodica_normalizada(rs, "mensual")
    esperado = 0.02 / (1 - 0.02)
    assert math.isclose(i_m, esperado, rel_tol=0, abs_tol=1e-12)

def test_ea_2433_mensual_vs_ea_equivalente():
    rs = RateSpec(valor=24.33, tipo="efectiva", capitalizacion="anual", vencimiento="vencida", base_dias=360)
    i_m = tasa_periodica_normalizada(rs, "mensual")
    ppy = _ppya("mensual", 360)
    i_ea = (1 + i_m)**ppy - 1
    assert math.isclose(i_ea, 0.2433, rel_tol=0, abs_tol=1e-9)