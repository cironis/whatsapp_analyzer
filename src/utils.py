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


def formatar_duracao_extensa(segundos) -> str:
    """Formata uma duração longa (ex.: uma conversa) por extenso, em português,
    como "2 dias, 3h e 20min" — diferente de `formatar_duracao`, pensada para
    a duração (curta) de um único áudio.
    """

    if pd.isna(segundos):
        return "não disponível"

    total_segundos = max(0, int(round(float(segundos))))
    dias, resto = divmod(total_segundos, 86400)
    horas, resto = divmod(resto, 3600)
    minutos, _ = divmod(resto, 60)

    partes = []
    if dias:
        partes.append(f"{dias} dia" + ("s" if dias != 1 else ""))
    if horas:
        partes.append(f"{horas}h")
    if minutos or not partes:
        partes.append(f"{minutos}min")

    if len(partes) == 1:
        return partes[0]

    return ", ".join(partes[:-1]) + " e " + partes[-1]


MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


def formatar_mes_ano(ano: int, mes: int) -> str:
    """Formata ano/mês como "Janeiro de 2026", sem depender de locale do sistema."""

    return f"{MESES_PT[mes]} de {ano}"


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
