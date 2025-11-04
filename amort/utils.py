from __future__ import annotations
import pandas as pd

def export_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False, encoding="utf-8-sig")

def export_excel(df: pd.DataFrame, path: str, sheet_name: str = "Tabla") -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as wr:
        df.to_excel(wr, index=False, sheet_name=sheet_name)