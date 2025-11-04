import sys
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = str(ROOT / "cli.py")

CLOSE_TOL = 0.001  # 0.1% del principal

def run_cli(args):
    cmd = [sys.executable, CLI] + list(map(str, args))
    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(ROOT), check=True)
    return cp.stdout

def extract_rows(text):
    rows = []
    in_table = False
    for line in text.splitlines():
        if not in_table and line.strip().startswith("Periodo") and "Saldo" in line:
            in_table = True
            continue
        if in_table:
            if line.strip().startswith("Resumen"):
                break
            if re.match(r"^\s*\d+\s", line):
                rows.append(line)
    return rows

def parse_last_saldo(text):
    rows = extract_rows(text)
    assert rows, f"No se detectaron filas de tabla en la salida:\n{text}"
    last = rows[-1].split()
    saldo_str = last[-1].replace(",", "")
    return float(saldo_str), rows

def parse_cuota(text, periodo):
    for line in extract_rows(text):
        if re.match(rf"^\s*{periodo}\s", line):
            parts = line.split()
            cuota = float(parts[2].replace(",", ""))
            return cuota
    raise AssertionError(f"No se encontró el periodo {periodo} en la tabla.")

# 1) Base: EA 24.33% anual, mensual, 24 cuotas
def test_base_ea_2433_mensual_24_cierra():
    P = 7_000_000
    out = run_cli([
        "--monto", P,
        "--tasa_valor", 24.33, "--tasa_tipo", "efectiva", "--tasa_cap", "anual",
        "--tasa_venc", "vencida",
        "--frecuencia", "mensual",
        "--n_periodos", 24,
        "--fecha_inicio", "01/01/2025",
    ])
    saldo_final, rows = parse_last_saldo(out)
    assert abs(saldo_final) <= P * CLOSE_TOL
    assert len(rows) == 24

# 2) Tasa anticipada (efectiva mensual 2%) → normaliza y cierra
def test_tasa_anticipada_cierra():
    P = 3_000_000
    out = run_cli([
        "--monto", P,
        "--tasa_valor", 2.0, "--tasa_tipo", "efectiva", "--tasa_cap", "mensual",
        "--tasa_venc", "anticipada",
        "--frecuencia", "mensual",
        "--n_periodos", 12,
        "--fecha_inicio", "01/02/2025",
    ])
    saldo_final, rows = parse_last_saldo(out)
    assert abs(saldo_final) <= P * CLOSE_TOL
    assert len(rows) == 12

# 3) Plazo corto (3 cuotas)
def test_plazo_corto_tres_cuotas():
    P = 900_000
    out = run_cli([
        "--monto", P,
        "--tasa_valor", 18.0, "--tasa_tipo", "efectiva", "--tasa_cap", "anual",
        "--tasa_venc", "vencida",
        "--frecuencia", "mensual",
        "--n_periodos", 3,
        "--fecha_inicio", "10/03/2025",
    ])
    saldo_final, rows = parse_last_saldo(out)
    assert abs(saldo_final) <= P * CLOSE_TOL
    assert len(rows) == 3

# 4) Plazo largo (120 cuotas)
def test_plazo_largo_ciento_veinte_cuotas():
    P = 2_000_000
    out = run_cli([
        "--monto", P,
        "--tasa_valor", 18.0, "--tasa_tipo", "efectiva", "--tasa_cap", "anual",
        "--tasa_venc", "vencida",
        "--frecuencia", "mensual",
        "--n_periodos", 120,
        "--fecha_inicio", "05/01/2025",
    ])
    saldo_final, rows = parse_last_saldo(out)
    assert abs(saldo_final) <= P * CLOSE_TOL
    assert len(rows) == 120

# 5) Abono que REDUCE PLAZO
def test_abono_reduce_plazo_disminuye_periodos():
    P = 5_000_000
    N = 24
    abonos = [{"periodo": 6, "monto": 1_800_000, "tipo": "plazo"}]
    out = run_cli([
        "--monto", P,
        "--tasa_valor", 24.0, "--tasa_tipo", "nominal", "--tasa_cap", "mensual",
        "--tasa_venc", "vencida",
        "--frecuencia", "mensual",
        "--n_periodos", N,
        "--fecha_inicio", "01/01/2025",
        "--abonos_json", json.dumps(abonos),
    ])
    saldo_final, rows = parse_last_saldo(out)
    assert abs(saldo_final) <= P * CLOSE_TOL
    assert len(rows) < N

# 6) Abono que RECALCULA CUOTA
def test_abono_recalcula_cuota_mantiene_n_y_baja_cuota():
    P = 7_000_000
    N = 24
    abonos = [{"periodo": 6, "monto": 1_000_000, "tipo": "cuota"}]
    out = run_cli([
        "--monto", P,
        "--tasa_valor", 24.33, "--tasa_tipo", "efectiva", "--tasa_cap", "anual",
        "--tasa_venc", "vencida",
        "--frecuencia", "mensual",
        "--n_periodos", N,
        "--fecha_inicio", "01/01/2025",
        "--abonos_json", json.dumps(abonos),
    ])
    saldo_final, rows = parse_last_saldo(out)
    assert abs(saldo_final) <= P * CLOSE_TOL
    assert len(rows) == N

    cuota_5 = parse_cuota(out, 5)
    cuota_7 = parse_cuota(out, 7)
    assert cuota_7 < cuota_5, "La cuota después del abono (periodo 6) debe ser menor"