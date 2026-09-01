"""Lógica compartilhada entre o ranking de dias e os grids estilo GitHub.

Não é uma análise registrada — é o cálculo comum usado por `daily_ranking`
e `github_grid`: "quem venceu cada dia" em cada métrica.
"""

from __future__ import annotations

import pandas as pd

METRICAS = [
    {"chave": "mensagens", "plural": "mensagens", "rotulo": "mensagens enviadas", "requer_midia": False, "icone": "chat"},
    {"chave": "caracteres", "plural": "caracteres", "rotulo": "caracteres enviados", "requer_midia": False, "icone": "texto"},
    {"chave": "audio", "plural": "áudios", "rotulo": "áudios enviados", "requer_midia": True, "icone": "microfone"},
    {"chave": "figurinha", "plural": "figurinhas", "rotulo": "figurinhas enviadas", "requer_midia": True, "icone": "figurinha"},
]


def serie_diaria(df: pd.DataFrame, chave: str) -> pd.Series:
    if chave == "mensagens":
        return df.groupby(["data_calendario", "nome"], observed=True).size()
    if chave == "caracteres":
        return df.groupby(["data_calendario", "nome"], observed=True)["quantidade_caracteres"].sum()
    if chave == "audio":
        return df.groupby(["data_calendario", "nome"], observed=True)["arquivo_audio"].sum()
    if chave == "figurinha":
        return df.groupby(["data_calendario", "nome"], observed=True)["figurinha"].sum()
    raise ValueError(f"Métrica desconhecida: {chave}")


def vencedores_por_dia(df: pd.DataFrame, chave: str) -> pd.Series:
    """Para cada dia com atividade, quem "venceu" a métrica naquele dia.

    Em caso de empate, fica com quem aparece primeiro em ordem alfabética
    (critério determinístico e estável entre execuções).
    """

    serie = serie_diaria(df, chave)
    tabela = serie.reset_index()
    tabela.columns = ["data_calendario", "nome", "valor"]
    tabela = tabela.loc[tabela["valor"] > 0].sort_values(["data_calendario", "nome"])

    if tabela.empty:
        return pd.Series(dtype=object, name="vencedor")

    vencedores = tabela.groupby("data_calendario").apply(
        lambda grupo: grupo.loc[grupo["valor"].idxmax(), "nome"]
    )
    vencedores.name = "vencedor"

    return vencedores


def ranking_dias_vencidos(vencedores: pd.Series, people: list) -> pd.DataFrame:
    contagem = vencedores.value_counts().reindex(people, fill_value=0)
    tabela = contagem.reset_index()
    tabela.columns = ["nome", "dias_vencidos"]

    return tabela.sort_values("dias_vencidos", ascending=False).reset_index(drop=True)
