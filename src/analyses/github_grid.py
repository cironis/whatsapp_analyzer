"""Grids estilo "contribuições do GitHub", um por métrica, coloridos por
quem venceu cada dia (mensagens, caracteres, áudios, figurinhas)."""

from __future__ import annotations

import datetime as dt

import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

from ..colors import BRAND, NEUTRAL_GRID
from ..models import AnalysisResult, ChartArtifact
from ..style import rodape_assinatura
from ._daywinner import METRICAS, vencedores_por_dia

KEY = "grids_github"
TITLE = "Grid de atividade (estilo GitHub)"
ICON = "grade"
REQUIRES_MEDIA = False

_MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
_DIAS_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
_NUMERACAO_SLUG = {"mensagens": "22", "caracteres": "23", "audio": "24", "figurinha": "25"}


def _desenhar_ano(ax, ano: int, vencedores: dict, color_map: dict):
    inicio_ano = dt.date(ano, 1, 1)
    fim_ano = dt.date(ano, 12, 31)

    inicio_grade = inicio_ano - dt.timedelta(days=inicio_ano.weekday())
    fim_grade = fim_ano + dt.timedelta(days=6 - fim_ano.weekday())

    dia = inicio_grade
    mes_anterior = None

    while dia <= fim_grade:
        semana = (dia - inicio_grade).days // 7
        linha = 6 - dia.weekday()

        if inicio_ano <= dia <= fim_ano:
            vencedor = vencedores.get(dia)
            cor = color_map.get(vencedor, NEUTRAL_GRID) if vencedor else NEUTRAL_GRID
            alpha = 1.0

            if dia.weekday() == 0 and dia.day <= 7 and dia.month != mes_anterior:
                ax.text(semana, 7.3, _MESES_PT[dia.month - 1], fontsize=9, color=BRAND["muted"], ha="left", va="bottom")
                mes_anterior = dia.month

            ax.add_patch(
                Rectangle((semana - 0.4, linha - 0.4), 0.8, 0.8, facecolor=cor, alpha=alpha, linewidth=0)
            )

        dia += dt.timedelta(days=1)

    total_semanas = (fim_grade - inicio_grade).days // 7 + 1
    ax.set_xlim(-0.6, total_semanas - 0.4)
    ax.set_ylim(-0.8, 8.2)
    ax.set_yticks(range(6, -1, -1))
    ax.set_yticklabels(_DIAS_PT, fontsize=8.5)
    ax.set_xticks([])
    rotulo_ano = ax.set_ylabel(str(ano), fontsize=12.5, fontweight="bold", color=BRAND["ink"], rotation=0, labelpad=28)
    rotulo_ano.set_verticalalignment("center")

    for lado in ax.spines.values():
        lado.set_visible(False)
    ax.tick_params(length=0)
    ax.set_aspect("equal")


def _grafico_grid(vencedores, color_map: dict, pessoas_presentes: list, titulo: str):
    dias_com_dado = list(vencedores.index)

    if not dias_com_dado:
        fig, ax = plt.subplots(figsize=(9, 2.4))
        ax.axis("off")
        ax.text(0.5, 0.5, "Sem dados suficientes para montar o grid.", ha="center", va="center")
        return fig

    vencedores_dict = {pd_ts.date(): nome for pd_ts, nome in vencedores.items()}
    anos = sorted({data.year for data in vencedores_dict})

    fig, eixos = plt.subplots(nrows=len(anos), ncols=1, figsize=(14, 2.5 * len(anos) + 0.6), squeeze=False)
    fig.suptitle(titulo, fontsize=17, fontweight="bold", y=0.995 if len(anos) > 1 else 0.99)

    for eixo, ano in zip(eixos[:, 0], anos):
        _desenhar_ano(eixo, ano, vencedores_dict, color_map)

    legenda = [Patch(facecolor=color_map[nome], label=nome) for nome in pessoas_presentes]
    legenda.append(Patch(facecolor=NEUTRAL_GRID, label="Sem atividade"))

    fig.legend(
        handles=legenda, loc="lower center", ncol=min(len(legenda), 5),
        bbox_to_anchor=(0.5, -0.02), frameon=False, fontsize=10,
    )

    fig.tight_layout(rect=(0.03, 0.05, 1, 0.96))
    rodape_assinatura(fig)

    return fig


def run(ctx) -> AnalysisResult:
    charts = []
    tabelas = {}
    insights = []

    for metrica in METRICAS:
        if metrica["requer_midia"] and not ctx.has_media:
            continue

        vencedores = vencedores_por_dia(ctx.df, metrica["chave"])

        if vencedores.empty:
            continue

        slug = _NUMERACAO_SLUG[metrica["chave"]]
        charts.append(
            ChartArtifact(
                slug=f"{slug}_grid_{metrica['chave']}",
                title=f"Grid de {metrica['rotulo'].lower()}",
                figure=_grafico_grid(
                    vencedores, ctx.color_map, ctx.people,
                    f"Quem venceu cada dia — {metrica['rotulo'].lower()}",
                ),
                caption="Cada célula é um dia; a cor é de quem mais teve essa métrica naquele dia.",
            )
        )
        tabelas[f"vencedores_por_dia_{metrica['chave']}"] = vencedores.rename("vencedor").reset_index().rename(
            columns={"index": "data_calendario"}
        )
        insights.append(
            f"O grid de {metrica['rotulo'].lower()} mostra, dia a dia, quem liderou essa métrica."
        )

    return AnalysisResult(
        key=KEY,
        title=TITLE,
        icon=ICON,
        tables=tabelas,
        charts=charts,
        insights=insights,
        intro="Inspirado no gráfico de contribuições do GitHub: cada quadradinho é um dia, "
        "colorido com a cor de quem venceu aquele dia na métrica.",
    )
