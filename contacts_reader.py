"""Módulo para leitura de contatos de arquivos CSV e Excel."""

import csv
from pathlib import Path

import pandas as pd


def read_contacts(filepath):
    """Lê contatos de um arquivo CSV ou Excel.

    O arquivo deve conter ao menos uma coluna 'email'.
    Todas as outras colunas serão usadas como variáveis de personalização.

    Args:
        filepath: Caminho para o arquivo CSV (.csv) ou Excel (.xlsx/.xls).

    Returns:
        list[dict]: Lista de dicionários com os dados de cada contato.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se a coluna 'email' não for encontrada.
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    ext = path.suffix.lower()

    if ext == ".csv":
        df = _read_csv(path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(path, engine="openpyxl")
    else:
        raise ValueError(f"Formato não suportado: {ext}. Use .csv, .xlsx ou .xls")

    df.columns = [col.strip().lower() for col in df.columns]

    if "email" not in df.columns:
        raise ValueError(
            f"Coluna 'email' não encontrada. Colunas disponíveis: {list(df.columns)}"
        )

    df = df.dropna(subset=["email"])
    df["email"] = df["email"].str.strip()
    df = df[df["email"].str.contains("@", na=False)]

    contacts = df.fillna("").to_dict("records")

    print(f"[OK] {len(contacts)} contatos válidos carregados de {path.name}")
    return contacts


def _read_csv(path):
    """Detecta o delimitador e lê o CSV."""
    with open(path, "r", encoding="utf-8-sig") as f:
        sample = f.read(4096)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        sep = dialect.delimiter
    except csv.Error:
        sep = ","
    return pd.read_csv(path, sep=sep, encoding="utf-8-sig")
