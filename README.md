# Tabla de Amortización – Método Francés  
**Trabajo Final – Ingeniería Financiera (UPB, 2025-2)**

**Integrantes**
- Juan José Molina Zapata  
- Valentina Rendón Claro

---

## 📌 Descripción

Herramienta en **Python** para generar tablas de amortización por **método francés** con **conversión completa de tasas**:

- **Nominal ↔ Efectiva**
- **Vencida ↔ Anticipada** (se normaliza a vencida para el cálculo)
- **Cualquier capitalización**: `diaria, semanal, quincenal, mensual, bimestral, trimestral, semestral, anual`
- **Base de días**: `360` o `365` *(aplica únicamente a la tasa diaria)*

Admite **abonos extraordinarios**:

- `tipo="plazo"` → **mantiene la cuota** y **reduce el número de cuotas**.  
- `tipo="cuota"` → **mantiene el plazo** y **recalcula la cuota** desde el periodo del abono.

Incluye **exportación a CSV/Excel**, **anclaje a fin de mes** y **pruebas automáticas**.

---

## ✅ Cómo se alinea con la rúbrica

1. **Exactitud financiera (30%)**  
   Conversión de tasas (nominal/efectiva, anticipada/vencida, capitalización, base 360/365); la tabla cierra con saldo final ≈ 0 (ajuste ≤ 0.1% del principal). Se imprime **tasa por periodo objetivo** y **EA equivalente**.

2. **Funcionalidad: método y abonos (25%)**  
   Método francés estable; abonos `plazo` (acorta) y `cuota` (recalcula) consistentes y reproducibles.

3. **Entradas y uso (15%)**  
   CLI clara: **monto**, **tasa** (valor, tipo, capitalización, vencimiento, base), **plazo** (por `--n_periodos` o `--duracion + --duracion_unidad`), **frecuencia de pago**, **fecha inicio**. Validaciones de cortesía y exportes CSV/XLSX.

4. **Código en Python (15%)**  
   Diseño modular y legible: `amort/rates.py` (tasas), `amort/schedule.py` (francés, abonos, fechas), `amort/utils.py` (export e helpers), `cli.py` (interfaz), `app.py` (modo interactivo).

5. **Pruebas y README (15%)**  
   Suite `pytest` con **17 pruebas** (conversión EA→mensual, efectiva mensual, nominal cap. mensual, anticipada→vencida, base 360/365, fin de mes desde 31/ene, tasa 0%, abonos `plazo`/`cuota`, cierre de tabla). Este README documenta uso, fórmulas y supuestos.

---

## 🧱 Estructura del repositorio

```text
ProyectoTablaAmortizacion/
├── amort/
│   ├── __init__.py
│   ├── rates.py          # Conversión de tasas (RateSpec, _ppya, tasa_periodica_normalizada, ...)
│   ├── schedule.py       # Método francés, fechas (fin de mes), abonos
│   └── utils.py          # Export a CSV/Excel, helpers
├── cli.py                # Interfaz de línea de comandos (uso principal)
├── app.py                # Modo interactivo por consola
├── tests/                # Pruebas con pytest
│   ├── test_rates.py
│   ├── test_schedule.py
│   ├── test_cli_smoke.py
│   └── test_core.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> Requisito: **Python 3.9+**

---

## 🖥️ Uso

### 1) CLI (recomendado)

**Parámetros clave de la tasa (tasa de referencia que el usuario conoce):**
- `--tasa_valor` : porcentaje (ej. `24.33`)
- `--tasa_tipo`  : `nominal` | `efectiva`
- `--tasa_cap`   : capitalización de esa tasa (`diaria|semanal|quincenal|mensual|bimestral|trimestral|semestral|anual`)
- `--tasa_venc`  : `vencida` | `anticipada`
- `--base_dias`  : `360` | `365` *(solo afecta si `tasa_cap=diaria`)*

**Plazo:**
- O **número de cuotas**: `--n_periodos N`
- O **duración + unidad**: `--duracion X --duracion_unidad {dias,semanas,quincenas,meses,bimestres,trimestres,semestres,anios}`  
  *(se convierte a `N` coherente con la **frecuencia de pago**)*

**Frecuencia de pago (objetivo):**
- `--frecuencia {diaria,semanal,quincenal,mensual,bimestral,trimestral,semestral,anual}`

**Otros:**
- `--fecha_inicio DD/MM/YYYY` *(opcional; activa fechas y fin de mes si inicia el 31)*  
- `--abonos_json '[{"periodo":6,"monto":1000000,"tipo":"plazo"}]'` *(tipo ∈ {"plazo","cuota"})*  
- `--export_csv salida.csv` | `--export_xlsx salida.xlsx`  
- `--preview N` *(muestra N filas)*  
- `--miles` *(formato amigable en consola; no afecta cálculos ni exportes)*

### 2) Modo interactivo
```bash
python app.py
```

---

## 🔁 Ejemplos reproducibles

**1. EA 24.33% anual → pagos mensuales (N=24)**
```bash
python cli.py --monto 7000000 --tasa_valor 24.33 --tasa_tipo efectiva --tasa_cap anual   --tasa_venc vencida --frecuencia mensual --n_periodos 24   --fecha_inicio 01/01/2025 --miles
```

**2. Efectiva 1.74% mensual (duración 24 meses)**
```bash
python cli.py --monto 7000000 --tasa_valor 1.74 --tasa_tipo efectiva --tasa_cap mensual   --tasa_venc vencida --frecuencia mensual   --duracion 24 --duracion_unidad meses   --fecha_inicio 15/10/2025 --miles
```

**3. Nominal 24% cap. mensual (≈2%/mes), plazo 2 trimestres**
```bash
python cli.py --monto 7000000 --tasa_valor 24 --tasa_tipo nominal --tasa_cap mensual   --tasa_venc vencida --frecuencia mensual   --duracion 2 --duracion_unidad trimestres   --fecha_inicio 01/01/2025 --miles
```

**4. Efectiva 2% mensual ANTICIPADA (normalizada a vencida)**
```bash
python cli.py --monto 3000000 --tasa_valor 2 --tasa_tipo efectiva --tasa_cap mensual   --tasa_venc anticipada --frecuencia mensual --n_periodos 12   --fecha_inicio 01/02/2025 --miles
```

**5. Abono que reduce plazo (mantiene cuota)**
```bash
python cli.py --monto 5000000 --tasa_valor 24 --tasa_tipo nominal --tasa_cap mensual   --tasa_venc vencida --frecuencia mensual --n_periodos 24   --fecha_inicio 01/01/2025   --abonos_json '[{"periodo":6,"monto":1800000,"tipo":"plazo"}]'
```

**6. Abono que recalcula cuota (mantiene plazo)**
```bash
python cli.py --monto 7000000 --tasa_valor 24.33 --tasa_tipo efectiva --tasa_cap anual   --tasa_venc vencida --frecuencia mensual --n_periodos 24   --fecha_inicio 01/01/2025   --abonos_json '[{"periodo":6,"monto":1000000,"tipo":"cuota"}]'
```

**7. Fin de mes anclado (desde 31/01/2025)**
```bash
python cli.py --monto 1000000 --tasa_valor 18 --tasa_tipo efectiva --tasa_cap anual   --tasa_venc vencida --frecuencia mensual --n_periodos 6   --fecha_inicio 31/01/2025 --preview 6
```

**8. Diaria: base 360 vs 365 (EA=20%)**
```bash
# base 360
python cli.py --monto 1000000 --tasa_valor 20 --tasa_tipo efectiva --tasa_cap anual   --tasa_venc vencida --frecuencia diaria --n_periodos 30 --base_dias 360

# base 365
python cli.py --monto 1000000 --tasa_valor 20 --tasa_tipo efectiva --tasa_cap anual   --tasa_venc vencida --frecuencia diaria --n_periodos 30 --base_dias 365
```

**9. Tasa 0% (cuotas iguales, sin intereses)**
```bash
python cli.py --monto 900000 --tasa_valor 0 --tasa_tipo efectiva --tasa_cap anual   --tasa_venc vencida --frecuencia mensual --n_periodos 9   --fecha_inicio 01/10/2025 --miles
```

---

## 🧮 Fórmulas clave (resumen)

Sea `ppya(periodo)` el número de pagos por año:  
`diaria=base_dias`, `semanal=52`, `quincenal=24`, `mensual=12`, `bimestral=6`, `trimestral=4`, `semestral=2`, `anual=1`.

**1) Nominal anual j con capitalización p_ref → periódica ref (vencida)**  
`i_ref = (j/100) / p_ref`  
Si venía **anticipada**: `i_ref = i_ref / (1 - i_ref)`.

**2) Efectiva periódica ref (valor en %) → i_ref (vencida)**  
`i_ref = valor/100`  
Si **anticipada**: `i_ref = i_ref / (1 - i_ref)`.

**3) Periódica ref → Efectiva Anual (EA)**  
`i_EA = (1 + i_ref)^{p_ref} - 1`.

**4) EA → Periódica objetivo (frecuencia de pago p_obj, vencida)**  
`i_obj = (1 + i_EA)^{1/p_obj} - 1`.

**Método francés (cuota vencida)**  
`A = P · [ i (1+i)^n / ((1+i)^n − 1) ]`  *(si `i=0` entonces `A = P/n`)*  
`Interés_t = Saldo_{t-1} · i`  
`Amortización_t = A − Interés_t`  
*Ajuste final:* se corrige residuo de redondeo en la última fila.

**Abonos**  
- `plazo`: descuenta del saldo, **mantiene A**, **reduce N**.  
- `cuota`: descuenta del saldo, **recalcula A** para los periodos restantes (mismo `N` total).

---

## 📅 Fechas y fin de mes

- Si `--fecha_inicio` es **31**, los pagos mensuales se **anclan a fin de mes** (28/29/30/31 según corresponda).  
- Otras frecuencias suman su intervalo natural (7, 15 días, etc.).  
- Sin fecha, la columna `Fecha` puede ser `None`.

---

## 🔒 Validaciones y supuestos

- `monto > 0`, `tasa_valor ≥ 0`, `n_periodos ≥ 1`.  
- Abonos con `periodo ≥ 1`, `monto ≥ 0`, `tipo ∈ {"plazo","cuota"}`.  
- La **base 360/365** solo afecta **tasa diaria**.  
- Los exportes no alteran el cálculo (solo salida de datos).

---

## 🧪 Pruebas

```bash
pytest -q
```
Resultado esperado del repo: **17 passed**.  
Cobertura: conversiones (incluye anticipada→vencida), base 360/365, fin de mes, tasa 0%, abonos `plazo` y `cuota`, cierre a saldo ≈ 0.

---

## 📝 Licencia / uso

Uso académico para el **Trabajo Final de Ingeniería Financiera (UPB, 2025-2)**.
