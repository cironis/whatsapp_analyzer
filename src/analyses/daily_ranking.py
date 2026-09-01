"""Ranking de "quem venceu o dia" em cada métrica: mensagens, caracteres,
áudios e figurinhas enviadas.
"""

from __future__ import annotations

from ..chart_common import grafico_barras_por_pessoa
from ..models import AnalysisResult, ChartArtifact
from ..utils import formatar_numero
from ._daywinner import METRICAS, ranking_dias_vencidos, vencedores_por_dia

KEY = "ranking_dias"
TITLE = "Ranking de dias vencidos"
ICON = "trofeu"
REQUIRES_MEDIA = False

_NUMERACAO_SLUG = {"mensagens": "18", "caracteres": "19", "audio": "20", "figurinha": "21"}


def run(ctx) -> AnalysisResult:
    tabelas = {}
    charts = []
    insights = []

    for metrica in METRICAS:
        if metrica["requer_midia"] and not ctx.has_media:
            continue

        vencedores = vencedores_por_dia(ctx.df, metrica["chave"])
        ranking = ranking_dias_vencidos(vencedores, ctx.people)

        if ranking["dias_vencidos"].sum() == 0:
            continue

        tabelas[f"ranking_dias_{metrica['chave']}"] = ranking

        slug = _NUMERACAO_SLUG[metrica["chave"]]
        charts.append(
            ChartArtifact(
                slug=f"{slug}_ranking_dias_{metrica['chave']}",
                title=f"Dias em que mais {metrica['rotulo'].lower()}",
                figure=grafico_barras_por_pessoa(
                    ranking, "dias_vencidos",
                    f"Ranking de dias — quem mais {metrica['rotulo'].lower()}",
                    "Dias em 1º lugar", ctx.color_map,
                    subtitulo="Conta 1 dia sempre que a pessoa foi quem mais teve essa métrica naquele dia.",
                ),
            )
        )

        lider = ranking.iloc[0]
        insights.append(
            f"{lider['nome']} venceu mais dias em \"{metrica['rotulo'].lower()}\": "
            f"{formatar_numero(lider['dias_vencidos'])} dias."
        )

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        tables=tabelas,
        charts=charts,
        insights=insights,
        intro="Para cada dia do histórico, vemos quem 'ganhou' aquele dia em cada métrica — "
        "e contamos quantos dias cada pessoa já venceu.",
    )
