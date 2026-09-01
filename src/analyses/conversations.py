"""Quem puxa e quem encerra as conversas, e a maior sequência de dias ativos."""

from __future__ import annotations

from ..chart_common import grafico_barras_por_pessoa
from ..enrich import maior_sequencia_do_grupo, maior_sequencia_por_pessoa
from ..models import AnalysisResult, ChartArtifact
from ..utils import formatar_numero

KEY = "conversas"
TITLE = "Conversas e sequências"
ICON = "faisca"
REQUIRES_MEDIA = False


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
    ]

    quem_inicia = iniciadas.iloc[0]
    quem_finaliza = finalizadas.iloc[0]
    quem_mais_sequencia = sequencias.iloc[0]

    insights = [
        f"{quem_inicia['nome']} é quem mais costuma puxar uma nova conversa "
        f"({formatar_numero(quem_inicia['conversas_iniciadas'])} vezes).",
        f"{quem_finaliza['nome']} costuma ser quem fala por último "
        f"({formatar_numero(quem_finaliza['conversas_finalizadas'])} vezes).",
        f"O grupo já ficou {formatar_numero(sequencia_grupo)} dias seguidos "
        f"com pelo menos uma mensagem — recorde individual de "
        f"{quem_mais_sequencia['nome']}: {formatar_numero(quem_mais_sequencia['maximo_dias_consecutivos'])} dias.",
    ]

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        tables={
            "conversas_iniciadas": iniciadas,
            "conversas_finalizadas": finalizadas,
            "sequencia_por_pessoa": sequencias,
        },
        charts=charts,
        insights=insights,
        intro="Uma conversa nova começa quando passam mais de 2h de silêncio. "
        "Aqui vemos quem inicia, quem encerra e quem mantém a chama acesa por mais dias seguidos.",
    )
