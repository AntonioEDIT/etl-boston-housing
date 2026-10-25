"""
ETL Boston Housing: CSV -> Pandas -> MySQL
Autor: Juan Antonio Delgado Hinojosa

Extract:   lee el CSV original
Transform: renombra columnas, revisa nulos y duplicados, valida tipos
           y crea una columna de categoría de precio
Load:      carga el resultado en MySQL (base etl_demo, tabla boston_housing_limpio)
"""

import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ---------- Configuración ----------
load_dotenv()  # lee el archivo .env (ahí va la contraseña, NO en el código)

DB_USER = os.getenv("DB_USER", "etl_user")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "etl_demo")

RUTA_CSV = "data/Boston-house-price-data.csv"
TABLA_DESTINO = "boston_housing_limpio"


# ---------- 1. EXTRACT ----------
def extraer(ruta):
    df = pd.read_csv(ruta)
    print(f"[Extract] {len(df)} filas y {len(df.columns)} columnas leídas")
    return df


# ---------- 2. TRANSFORM ----------
def transformar(df):
    # 2.1 Nombres de columnas claros en español
    nombres = {
        "CRIM": "tasa_criminalidad",
        "ZN": "pct_terreno_residencial",
        "INDUS": "pct_zona_industrial",
        "CHAS": "junto_al_rio",
        "NOX": "contaminacion_nox",
        "RM": "promedio_habitaciones",
        "AGE": "pct_casas_antiguas",
        "DIS": "distancia_empleo",
        "RAD": "acceso_autopistas",
        "TAX": "impuesto_predial",
        "PTRATIO": "alumnos_por_maestro",
        "B": "indice_b",
        "LSTAT": "pct_poblacion_bajos_ingresos",
        "MEDV": "precio_medio_miles",
    }
    df.columns = df.columns.str.strip().str.upper()
    df = df.rename(columns=nombres)

    # 2.2 Calidad de datos: nulos y duplicados
    nulos = int(df.isnull().sum().sum())
    duplicados = int(df.duplicated().sum())
    print(f"[Transform] Nulos encontrados: {nulos} | Duplicados encontrados: {duplicados}")
    df = df.drop_duplicates()
    df = df.dropna()

    # 2.3 Tipos de datos
    df["junto_al_rio"] = df["junto_al_rio"].astype(int)
    df["acceso_autopistas"] = df["acceso_autopistas"].astype(int)

    # 2.4 Columnas nuevas
    df["categoria_precio"] = pd.cut(
        df["precio_medio_miles"],
        bins=[0, 17, 25, float("inf")],
        labels=["Bajo", "Medio", "Alto"],
    ).astype(str)
    df["promedio_habitaciones"] = df["promedio_habitaciones"].round(1)

    print(f"[Transform] {len(df)} filas listas para cargar")
    return df


# ---------- 3. LOAD ----------
def cargar(df):
    url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(url)
    df.to_sql(TABLA_DESTINO, engine, if_exists="replace", index=False)

    # Validación: contar filas en MySQL
    with engine.connect() as conn:
        total = conn.execute(text(f"SELECT COUNT(*) FROM {TABLA_DESTINO}")).scalar()
    print(f"[Load] {total} filas cargadas en {DB_NAME}.{TABLA_DESTINO}")


if __name__ == "__main__":
    datos = extraer(RUTA_CSV)
    datos = transformar(datos)
    cargar(datos)
    print("ETL terminado correctamente")
