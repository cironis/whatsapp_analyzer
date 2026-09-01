"""Quem puxa e quem encerra as conversas, a maior sequência de dias ativos,
médias por conversa (mensagens e figurinhas) e os recordes de conversa mais
longa — por duração e por quantidade de mensagens.
"""

from __future__ import annotations

import pandas as pd

from ..chart_common import grafico_barras_por_pessoa
from ..enrich import (
    MAPA_DIAS_SEMANA,
    maior_sequencia_do_grupo,
    maior_sequencia_por_pessoa,
    resumo_por_conversa,
)
from ..models import AnalysisResult, ChartArtifact
from ..utils import formatar_duracao_extensa, formatar_numero

KEY = "conversas"
TITLE = "Conversas e sequências"
ICON = "faisca"
REQUIRES_MEDIA = False


def _pessoas_da_conversa(df: pd.DataFrame, numero_conversa: int, people: list) -> pd.DataFrame:
    """Quantas mensagens cada pessoa mandou em uma conversa específica."""

    conversa = df.loc[df["numero_conversa"] == numero_conversa]

    return (
        conversa.groupby("nome", observed=True)
        .size()
        .reindex(people, fill_value=0)
        .reset_index(name="quantidade_mensagens")
        .sort_values("quantidade_mensagens", ascending=False)
        .reset_index(drop=True)
    )


def _formatar_intervalo(inicio: pd.Timestamp, fim: pd.Timestamp) -> str:
    """Dia(s) da semana e horário de uma conversa, por extenso."""

    if inicio.normalize() == fim.normalize():
        dia_semana = MAPA_DIAS_SEMANA[inicio.dayofweek]
        return (
            f"{dia_semana}, {inicio.strftime('%d/%m/%Y')}, "
            f"das {inicio.strftime('%H:%M')} às {fim.strftime('%H:%M')}"
        )

    return (
        f"de {MAPA_DIAS_SEMANA[inicio.dayofweek]}, {inicio.strftime('%d/%m/%Y %H:%M')} "
        f"até {MAPA_DIAS_SEMANA[fim.dayofweek]}, {fim.strftime('%d/%m/%Y %H:%M')}"
    )


def run(ctx) -> AnalysisResult:
    df = ctx.df

    iniciadas = (
        df.loc[df["primeira_mensagem_conversa"]]
        .groupby("nome", observed=True)
        .size()
        .reset_index(name="conversas_iniciadas")
        .sort_values("conversas_iniciadas", ascending=False)
        .reset_index(drop=True)
    )

    finalizadas = (
        df.loc[df["ultima_mensagem_conversa"]]
        .groupby("nome", observed=True)
        .size()
        .reset_index(name="conversas_finalizadas")
        .sort_values("conversas_finalizadas", ascending=False)
        .reset_index(drop=True)
    )

    sequencias = maior_sequencia_por_pessoa(df)
    sequencia_grupo = maior_sequencia_do_grupo(df)

    resumo = resumo_por_conversa(df)

    media_mensagens_grupo = float(resumo["quantidade_mensagens"].mean())
    media_figurinhas_grupo = float(resumo["quantidade_figurinhas"].mean())

    conversas_por_pessoa = df.groupby("nome", observed=True)["numero_conversa"].nunique()
    mensagens_por_pessoa = df.groupby("nome", observed=True).size()
    figurinhas_por_pessoa = df.groupby("nome", observed=True)["figurinha"].sum()

    media_mensagens_pessoa = (
        (mensagens_por_pessoa / conversas_por_pessoa)
        .reindex(ctx.people)
        .rename("media_mensagens_por_conversa")
        .reset_index()
    )
    media_figurinhas_pessoa = (
        (figurinhas_por_pessoa / conversas_por_pessoa)
        .reindex(ctx.people)
        .rename("media_figurinhas_por_conversa")
        .reset_index()
    )

    linha_duracao = resumo.loc[resumo["duracao_segundos"].idxmax()]
    linha_contagem = resumo.loc[resumo["quantidade_mensagens"].idxmax()]
    mesma_conversa = linha_duracao["numero_conversa"] == linha_contagem["numero_conversa"]

    tabela_pessoas_duracao = _pessoas_da_conversa(df, linha_duracao["numero_conversa"], ctx.people)

    charts = [
        ChartArtifact(
            slug="07_conversas_iniciadas",
            title="Conversas iniciadas por pessoa",
            figure=grafico_barras_por_pessoa(
                iniciadas, "conversas_iniciadas", "Quem mais puxa assunto",
                "Conversas iniciadas", ctx.color_map,
            ),
        ),
        ChartArtifact(
            slug="08_conversas_finalizadas",
            title="Conversas finalizadas por pessoa",
            figure=grafico_barras_por_pessoa(
                finalizadas, "conversas_finalizadas", "Quem costuma falar por último",
                "Conversas finalizadas", ctx.color_map,
            ),
        ),
        ChartArtifact(
            slug="09_sequencia_dias_consecutivos",
            title="Maior sequência de dias consecutivos",
            figure=grafico_barras_por_pessoa(
                sequencias, "maximo_dias_consecutivos", "Maior sequência de dias seguidos mandando mensagem",
                "Dias consecutivos", ctx.color_map,
            ),
        ),
        ChartArtifact(
            slug="09b_media_mensagens_por_conversa",
            title="Média de mensagens por conversa, por pessoa",
            figure=grafico_barras_por_pessoa(
                media_mensagens_pessoa, "media_mensagens_por_conversa",
                "Quantas mensagens cada um manda, em média, por conversa",
                "Mensagens por conversa", ctx.color_map,
                formato_valor="{:.1f}", linha_media=media_mensagens_grupo,
            ),
        ),
        ChartArtifact(
            slug="09d_conversa_mais_longa_duracao",
            title="Conversa mais longa em duração — por pessoa",
            figure=grafico_barras_por_pessoa(
                tabela_pessoas_duracao, "quantidade_mensagens",
                "Quem mais falou na conversa mais longa (em duração)",
                "Mensagens nessa conversa", ctx.color_map,
            ),
        ),
    ]

    tabelas = {
        "conversas_iniciadas": iniciadas,
        "conversas_finalizadas": finalizadas,
        "sequencia_por_pessoa": sequencias,
        "media_mensagens_por_conversa": media_mensagens_pessoa,
        "conversa_mais_longa_duracao_pessoas": tabela_pessoas_duracao,
    }

    if ctx.has_media:
        charts.append(
            ChartArtifact(
                slug="09c_media_figurinhas_por_conversa",
                title="Média de figurinhas por conversa, por pessoa",
                figure=grafico_barras_por_pessoa(
                    media_figurinhas_pessoa, "media_figurinhas_por_conversa",
                    "Quantas figurinhas cada um manda, em média, por conversa",
                    "Figurinhas por conversa", ctx.color_map,
                    formato_valor="{:.2f}", linha_media=media_figurinhas_grupo,
                ),
            )
        )
        tabelas["media_figurinhas_por_conversa"] = media_figurinhas_pessoa

    quem_inicia = iniciadas.iloc[0]
    quem_finaliza = finalizadas.iloc[0]
    quem_mais_sequencia = sequencias.iloc[0]
    lider_media_mensagens = media_mensagens_pessoa.sort_values(
        "media_mensagens_por_conversa", ascending=False
    ).iloc[0]

    insights = [
        f"{quem_inicia['nome']} iniciou mais conversas: {formatar_numero(quem_inicia['conversas_iniciadas'])} vezes.",
        f"{quem_finaliza['nome']} falou por último mais vezes: {formatar_numero(quem_finaliza['conversas_finalizadas'])}.",
        f"Sequência mais longa do grupo: {formatar_numero(sequencia_grupo)} dias seguidos com mensagem. "
        f"Recorde individual: {quem_mais_sequencia['nome']}, com {formatar_numero(quem_mais_sequencia['maximo_dias_consecutivos'])} dias.",
        f"Média do grupo: {media_mensagens_grupo:.1f} mensagens por conversa"
        + (f" e {media_figurinhas_grupo:.2f} figurinhas por conversa." if ctx.has_media else "."),
        f"{lider_media_mensagens['nome']} é quem mais mensagens manda por conversa, em média: "
        f"{lider_media_mensagens['media_mensagens_por_conversa']:.1f}.",
    ]

    if ctx.has_media:
        lider_media_figurinhas = media_figurinhas_pessoa.sort_values(
            "media_figurinhas_por_conversa", ascending=False
        ).iloc[0]
        insights.append(
            f"{lider_media_figurinhas['nome']} é quem mais figurinhas manda por conversa, em média: "
            f"{lider_media_figurinhas['media_figurinhas_por_conversa']:.2f}."
        )

    top_duracao = tabela_pessoas_duracao.iloc[0]
    participantes_duracao = int((tabela_pessoas_duracao["quantidade_mensagens"] > 0).sum())

    insights.append(
        f"Conversa mais longa em duração: {formatar_duracao_extensa(linha_duracao['duracao_segundos'])} seguidas, "
        f"{_formatar_intervalo(linha_duracao['inicio'], linha_duracao['fim'])} "
        f"({formatar_numero(linha_duracao['quantidade_mensagens'])} mensagens, {participantes_duracao} pessoas). "
        f"{top_duracao['nome']} foi quem mais mandou mensagem nela: {formatar_numero(top_duracao['quantidade_mensagens'])}."
    )

    if mesma_conversa:
        insights.append("Essa mesma conversa também foi a que teve mais mensagens no total.")
    else:
        tabela_pessoas_contagem = _pessoas_da_conversa(df, linha_contagem["numero_conversa"], ctx.people)
        top_contagem = tabela_pessoas_contagem.iloc[0]
        participantes_contagem = int((tabela_pessoas_contagem["quantidade_mensagens"] > 0).sum())

        charts.append(
            ChartArtifact(
                slug="09e_conversa_mais_longa_mensagens",
                title="Conversa com mais mensagens — por pessoa",
                figure=grafico_barras_por_pessoa(
                    tabela_pessoas_contagem, "quantidade_mensagens",
                    "Quem mais falou na conversa com mais mensagens",
                    "Mensagens nessa conversa", ctx.color_map,
                ),
            )
        )
        tabelas["conversa_mais_longa_mensagens_pessoas"] = tabela_pessoas_contagem

        insights.append(
            f"Conversa com mais mensagens: {formatar_numero(linha_contagem['quantidade_mensagens'])} mensagens em "
            f"{formatar_duracao_extensa(linha_contagem['duracao_segundos'])}, "
            f"{_formatar_intervalo(linha_contagem['inicio'], linha_contagem['fim'])} ({participantes_contagem} pessoas). "
            f"{top_contagem['nome']} foi quem mais mandou mensagem nela: {formatar_numero(top_contagem['quantidade_mensagens'])}."
        )

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        tables=tabelas,
        charts=charts,
        insights=insights,
        intro="Uma conversa nova começa após 2h de silêncio. Quem inicia, quem encerra, "
        "as médias de mensagens e figurinhas por conversa e os recordes de conversa mais "
        "longa — por duração e por quantidade de mensagens.",
    )
