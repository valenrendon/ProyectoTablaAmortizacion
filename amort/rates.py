# Conversión de tasas: nominal a efectiva, anticipada a vencida, y equivalencias entre frecuencias.
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Dict

Freq = Literal["diaria","semanal","quincenal","mensual","bimestral","trimestral","semestral","anual"]
TasaTipo = Literal["nominal","efectiva"]
Vencimiento = Literal["vencida","anticipada"]
BaseDias = Literal[360,365]

PERIODOS_POR_ANO: Dict[Freq, float] = {
    "diaria": 360.0,      # por defecto 360; si base 365, se reescala
    "semanal": 52.0,
    "quincenal": 24.0,
    "mensual": 12.0,
    "bimestral": 6.0,
    "trimestral": 4.0,
    "semestral": 2.0,
    "anual": 1.0,
}

def _ppya(freq: Freq, base_dias: BaseDias) -> float:
    """Periodos por año efectivos considerando base de días para diaria."""
    if freq == "diaria":
        return float(base_dias)
    return PERIODOS_POR_ANO[freq]

@dataclass
class RateSpec:
    valor: float  # p.ej. 18.0 -> 18%
    tipo: TasaTipo  # "nominal" o "efectiva"
    capitalizacion: Freq  # frecuencia de capitalización si nominal; si efectiva, referencia del periodo de la tasa
    vencimiento: Vencimiento = "vencida"  # 'anticipada' descuenta al inicio
    base_dias: BaseDias = 360

    def as_decimal(self) -> float:
        return self.valor / 100.0

def nominal_to_effective_periodic(j: float, m_comp: float, p_target: float) -> float:
    """
    j: tasa nominal anual (decimal) con m_comp capitalizaciones por año.
    p_target: pagos por año deseados.
    Retorna i_p (efectiva por periodo de pago) como decimal.
    """
    i_eff_anual = (1.0 + j / m_comp) ** m_comp - 1.0
    return (1.0 + i_eff_anual) ** (1.0 / p_target) - 1.0

def effective_equivalent(i_eff_ref: float, p_ref: float, p_target: float) -> float:
    """Convierte i_eff_ref (efectiva por periodo ref) a i_eff_target (por periodo target)."""
    i_eff_anual = (1.0 + i_eff_ref) ** p_ref - 1.0
    return (1.0 + i_eff_anual) ** (1.0 / p_target) - 1.0

def _a_vencida(i: float, vencimiento: str) -> float:
    """Convierte tasa del mismo periodo: anticipada -> vencida; si ya es vencida, la deja igual."""
    return i / (1.0 - i) if vencimiento == "anticipada" else i

def tasa_periodica_normalizada(rs: RateSpec, periodo_objetivo: str) -> float:
    """
    Convierte la tasa de 'rs' al periodo de pago objetivo (siempre vencida):
    - Soporta nominal (j) y efectiva, y tasas anticipadas/vencidas.
    - Respeta la base de días para periodos 'diaria'.
    """
    p_ref = _ppya(rs.capitalizacion, rs.base_dias)         # pagos/año de la tasa de entrada
    p_obj = _ppya(periodo_objetivo, rs.base_dias)          # pagos/año del periodo objetivo

    if rs.tipo == "nominal":
        # j nominal anual -> i_ref (por periodo de capitalización), luego a vencida
        j = rs.valor / 100.0
        i_ref = _a_vencida(j / p_ref, rs.vencimiento)      # periodic_ref (vencida)
        i_ea  = (1.0 + i_ref) ** p_ref - 1.0               # a efectiva anual
    else:  # efectiva
        # rs.valor ya es efectiva del periodo de capitalización -> a vencida y a EA
        i_ref = _a_vencida(rs.valor / 100.0, rs.vencimiento)
        i_ea  = (1.0 + i_ref) ** p_ref - 1.0

    # EA -> periódica objetivo (vencida)
    return (1.0 + i_ea) ** (1.0 / p_obj) - 1.0