"""Enriquecimento do DataFrame bruto: colunas derivadas usadas pelas análises.

Este módulo roda uma única vez no pipeline, depois da troca de nomes.
Qualquer análise nova deveria conseguir se apoiar nas colunas daqui em vez
de recalcular a mesma coisa — é o "contrato" entre o parsing e as análises.
"""

from __future__ import annotations

import pandas as pd

from .media_store import classificar_por_nome_arquivo
from .utils import limpar_texto_invisivel

LIMITE_CONVERSA_HORAS = 1

ORDEM_DIAS_SEMANA = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo",
]

MAPA_DIAS_SEMANA = dict(enumerate(ORDEM_DIAS_SEMANA))

# Placeholders que já indicam o tipo exato do anexo, usados por algumas
# versões/idiomas do WhatsApp mesmo em exportações sem mídia.
MARCADORES_MIDIA_TIPO = {
    "audio omitted": "audio",
    "áudio omitido": "audio",
    "áudio ocultado": "audio",
    "sticker omitted": "figurinha",
    "figurinha omitida": "figurinha",
    "figurinha ocultada": "figurinha",
    "image omitted": "imagem",
    "imagem omitida": "imagem",
    "imagem ocultada": "imagem",
    "gif omitted": "imagem",
    "video omitted": "video",
    "vídeo omitido": "video",
    "vídeo ocultado": "video",
    "document omitted": "documento",
    "documento omitido": "documento",
    "documento ocultado": "documento",
    "contact card omitted": "contato",
    "cartão do contato omitido": "contato",
}

# Placeholder genérico: sabemos que é mídia, mas não qual tipo (o caso
# mais comum em exportações "sem mídia" feitas por versões recentes).
MARCADORES_MIDIA_GENERICOS = {
    "<media omitted>",
    "media omitted",
    "<mídia oculta>",
    "mídia oculta",
    "mídia ocultada",
}


def _classificar_conteudo(mensagem, nome_arquivo_anexo):
    """Classifica uma mensagem como texto ou mídia (e o tipo, se possível)."""

    if pd.notna(nome_arquivo_anexo) and nome_arquivo_anexo:
        return "midia", classificar_por_nome_arquivo(nome_arquivo_anexo)

    texto = limpar_texto_invisivel(mensagem).lower() if not pd.isna(mensagem) else ""

    if texto in MARCADORES_MIDIA_TIPO:
        return "midia", MARCADORES_MIDIA_TIPO[texto]

    if texto in MARCADORES_MIDIA_GENERICOS:
        return "midia", None

    return "texto", None


def maior_sequencia_consecutiva(datas) -> tuple:
    """Maior sequência de dias consecutivos com pelo menos uma mensagem.

    Devolve (tamanho, inicio, fim) da sequência mais longa. Em caso de
    empate, fica com a primeira ocorrência (mais antiga). Pública porque
    também é usada por `analyses/evolucao_periodica.py` (sequência dentro
    de cada mês/semana).
    """

    datas_unicas = sorted(pd.Series(datas).dropna().unique())

    if not datas_unicas:
        return 0, None, None

    maior, atual = 1, 1
    inicio_atual = datas_unicas[0]
    inicio_maior, fim_maior = datas_unicas[0], datas_unicas[0]

    for indice in range(1, len(datas_unicas)):
        diferenca = (
            pd.Timestamp(datas_unicas[indice]) - pd.Timestamp(datas_unicas[indice - 1])
        ).days

        if diferenca == 1:
            atual += 1
        else:
            atual = 1
            inicio_atual = datas_unicas[indice]

        if atual > maior:
            maior = atual
            inicio_maior, fim_maior = inicio_atual, datas_unicas[indice]

    return maior, pd.Timestamp(inicio_maior), pd.Timestamp(fim_maior)


def enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    """Recebe o DataFrame já com os nomes finais e adiciona colunas derivadas."""

    df = df.sort_values("data", kind="stable").reset_index(drop=True).copy()

    classificacao = df.apply(
        lambda linha: _classificar_conteudo(linha["mensagem"], linha["nome_arquivo_anexo"]),
        axis=1,
        result_type="expand",
    )
    df["tipo_conteudo"] = classificacao[0]
    df["tipo_midia"] = classificacao[1]

    df["arquivo_midia"] = df["tipo_conteudo"] == "midia"
    df["arquivo_audio"] = df["tipo_midia"] == "audio"
    df["figurinha"] = df["tipo_midia"] == "figurinha"

    df["quantidade_caracteres"] = 0
    df.loc[~df["arquivo_midia"], "quantidade_caracteres"] = (
        df.loc[~df["arquivo_midia"], "mensagem"].fillna("").astype(str).str.len()
    )

    df["dia_semana"] = pd.Categorical(
        df["data"].dt.dayofweek.map(MAPA_DIAS_SEMANA),
        categories=ORDEM_DIAS_SEMANA,
        ordered=True,
    )
    df["hora_dia"] = df["data"].dt.hour
    df["data_calendario"] = df["data"].dt.normalize()

    # Segmentação em "conversas": uma nova conversa começa quando o
    # intervalo desde a mensagem anterior passa de LIMITE_CONVERSA_HORAS.
    diferenca_anterior_horas = df["data"].diff().dt.total_seconds() / 3600
    diferenca_proxima_horas = (
        df["data"].shift(-1) - df["data"]
    ).dt.total_seconds() / 3600

    df["primeira_mensagem_conversa"] = (
        diferenca_anterior_horas.isna() | (diferenca_anterior_horas > LIMITE_CONVERSA_HORAS)
    )
    df["ultima_mensagem_conversa"] = (
        diferenca_proxima_horas.isna() | (diferenca_proxima_horas > LIMITE_CONVERSA_HORAS)
    )
    df["numero_conversa"] = df["primeira_mensagem_conversa"].cumsum()

    # Preenchido depois, sob demanda, pela análise de mídia (precisa
    # abrir cada áudio para medir a duração real).
    df["duracao_audio_segundos"] = float("nan")

    return df


def maior_sequencia_do_grupo(df: pd.DataFrame) -> int:
    tamanho, _inicio, _fim = maior_sequencia_consecutiva(df["data_calendario"])
    return tamanho


def maior_sequencia_do_grupo_com_periodo(df: pd.DataFrame) -> tuple:
    """Tamanho e período (início, fim) da maior sequência de dias consecutivos do grupo."""

    return maior_sequencia_consecutiva(df["data_calendario"])


def maior_sequencia_por_pessoa(df: pd.DataFrame) -> pd.DataFrame:
    """Maior sequência de dias consecutivos, por pessoa, com o período (início/fim) em que ela ocorreu."""

    resultado = df.groupby("nome", observed=True)["data_calendario"].apply(maior_sequencia_consecutiva)

    tabela = pd.DataFrame(
        resultado.tolist(),
        columns=["maximo_dias_consecutivos", "sequencia_inicio", "sequencia_fim"],
        index=resultado.index,
    ).reset_index()

    return tabela.sort_values("maximo_dias_consecutivos", ascending=False).reset_index(drop=True)


def sequencia_atual_por_pessoa(df: pd.DataFrame) -> pd.DataFrame:
    """Sequência de dias consecutivos "em andamento" por pessoa: quantos dias
    seguidos, terminando no último dia do período analisado, a pessoa mandou
    mensagem. Se o último dia dela não coincidir com o último dia do
    período, a sequência já foi quebrada (conta 0).
    """

    ultimo_dia_periodo = df["data_calendario"].max()

    registros = []
    for pessoa, grupo in df.groupby("nome", observed=True):
        dias = sorted(grupo["data_calendario"].dropna().unique())

        if not dias or pd.Timestamp(dias[-1]) != ultimo_dia_periodo:
            registros.append({"nome": pessoa, "sequencia_atual": 0})
            continue

        atual = 1
        for indice in range(len(dias) - 1, 0, -1):
            diferenca = (pd.Timestamp(dias[indice]) - pd.Timestamp(dias[indice - 1])).days
            if diferenca == 1:
                atual += 1
            else:
                break

        registros.append({"nome": pessoa, "sequencia_atual": atual})

    return pd.DataFrame(registros, columns=["nome", "sequencia_atual"])


def resumo_por_conversa(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por conversa (ver `numero_conversa`): início, fim, duração e
    volume de mensagens/figurinhas. Base para médias por conversa e para os
    recordes de conversa mais longa (duração e quantidade de mensagens).
    """

    resumo = (
        df.groupby("numero_conversa", observed=True)
        .agg(
            inicio=("data", "min"),
            fim=("data", "max"),
            quantidade_mensagens=("data", "size"),
            quantidade_figurinhas=("figurinha", "sum"),
        )
        .reset_index()
    )
    resumo["duracao_segundos"] = (resumo["fim"] - resumo["inicio"]).dt.total_seconds()

    return resumo
