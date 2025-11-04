import re
from cli import main as cli_main

def test_cli_smoke(capsys):
    argv = [
        "--monto","100000",
        "--tasa_valor","12","--tasa_tipo","efectiva","--tasa_cap","anual",
        "--tasa_venc","vencida",
        "--frecuencia","mensual",
        "--n_periodos","3",
        "--preview","3"
    ]
    cli_main(argv)
    out = capsys.readouterr().out
    assert "Tasa por periodo (mensual)" in out
    assert "Plazo: 3 cuotas (mensual)" in out
    assert "Resumen" in out
    assert re.search(r"\bPeriodo\b.*\bCuota\b.*\bInter[eé]s\b", out)