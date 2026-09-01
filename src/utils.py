"""Funções pequenas e reutilizadas em vários módulos."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd


def limpar_texto_invisivel(texto) -> str:
    """Remove caracteres invisíveis comuns nas exportações do WhatsApp."""

    return (
        str(texto)
        .replace("‎", "")
        .replace("‏", "")
        .replace("﻿", "")
        .strip()
    )


def normalizar_nome_arquivo(texto: str) -> str:
    """Transforma um texto livre em um nome de arquivo seguro e legível."""

    texto_sem_acento = (
        unicodedata.normalize("NFKD", str(texto))
        .encode("ascii", "ignore")
        .decode("ascii")
    )

    nome = re.sub(r"[^\w.-]+", "_", texto_sem_acento.strip()).strip("_.")

    return nome or "item"


def formatar_duracao(segundos) -> str:
    """Formata segundos como HH:MM:SS ou MM:SS."""

    if pd.isna(segundos):
        return "não disponível"

    total_segundos = max(0, int(round(float(segundos))))
    horas, resto = divmod(total_segundos, 3600)
    minutos, segundos_restantes = divmod(resto, 60)

    if horas:
        return f"{horas:02d}:{minutos:02d}:{segundos_restantes:02d}"

    return f"{minutos:02d}:{segundos_restantes:02d}"


def formatar_numero(numero) -> str:
    """Formata um número inteiro com separador de milhar (padrão BR)."""

    try:
        return f"{int(round(float(numero))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(numero)


def truncar(texto: str, largura: int = 28) -> str:
    """Encurta um texto longo preservando legibilidade em rótulos."""

    texto = str(texto)

    if len(texto) <= largura:
        return texto

    return texto[: largura - 1].rstrip() + "…"
