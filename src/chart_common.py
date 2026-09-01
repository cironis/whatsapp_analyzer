"""Gráficos genéricos reaproveitados por várias análises.

Manter esses padrões centralizados é o que faz uma análise nova (ex.: uma
métrica ainda não pensada) já sair com a mesma cara das demais.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .colors import BRAND
from .style import DPI, FIGSIZE_LARGO, FIGSIZE_PADRAO, estilizar_eixo, rodape_assinatura, rotular_barras
from .utils import truncar


def grafico_barras_por_pessoa(
    tabela: pd.DataFrame,
    coluna_valor: str,
    titulo: str,
    rotulo_y: str,
    color_map: dict,
    formato_valor: str = "{:.0f}",
    subtitulo: str = "",
    linha_media: float | None = None,
    rotulo_media: str = "Média do grupo",
):
    """Uma barra por pessoa, cor consistente, valor anotado no topo.

    Quando `linha_media` é informado, desenha uma linha tracejada horizontal
    com a média do grupo, para comparar cada pessoa contra o coletivo.
    """

    tabela = tabela.sort_values(coluna_valor, ascending=False).reset_index(drop=True)
    largura = max(FIGSIZE_PADRAO[0], 1.1 * len(tabela) + 3)

    fig, ax = plt.subplots(figsize=(largura, FIGSIZE_PADRAO[1]))
    cores = [color_map.get(nome, BRAND["primary"]) for nome in tabela["nome"]]

    ax.bar(
        [truncar(n, 16) for n in tabela["nome"]],
        tabela[coluna_valor],
        color=cores,
        width=0.62,
        zorder=3,
    )

    topo = tabela[coluna_valor].max() if len(tabela) else 0

    if linha_media is not None:
        topo = max(topo, linha_media)
        ax.axhline(linha_media, color=BRAND["muted"], linestyle="--", linewidth=1.4, zorder=4)
        ax.text(
            len(tabela) - 0.42, linha_media, f" {rotulo_media}: {formato_valor.format(linha_media)}",
            va="bottom", ha="right", fontsize=9.5, color=BRAND["ink"], fontweight="bold", zorder=5,
        )

    ax.set_title(titulo)
    if subtitulo:
        ax.text(0.0, 1.06, subtitulo, transform=ax.transAxes, fontsize=10.5, color=BRAND["muted"])
    ax.set_ylabel(rotulo_y)
    ax.set_ylim(0, max(topo * 1.18, 1))
    estilizar_eixo(ax)
    rotular_barras(ax, formato_valor)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")

    fig.tight_layout()
    rodape_assinatura(fig)

    return fig


def grafico_heatmap_dia_hora(tabela: pd.DataFrame, titulo: str):
    """Heatmap dia da semana × hora do dia (estilo simples e legível)."""

    fig, ax = plt.subplots(figsize=FIGSIZE_LARGO)

    mapa_cores = _colormap_marca()
    imagem = ax.imshow(tabela.values, aspect="auto", cmap=mapa_cores)

    ax.set_xticks(range(24))
    ax.set_xticklabels([str(h) for h in range(24)], fontsize=9)
    ax.set_yticks(range(len(tabela.index)))
    ax.set_yticklabels(tabela.index)
    ax.set_xlabel("Hora do dia")
    ax.set_title(titulo)
    ax.grid(False)

    for lado in ax.spines.values():
        lado.set_visible(False)

    valor_maximo = tabela.values.max() if tabela.values.size else 0
    for i in range(tabela.shape[0]):
        for j in range(tabela.shape[1]):
            valor = tabela.values[i, j]
            if valor <= 0:
                continue
            cor_texto = "white" if valor > valor_maximo * 0.6 else BRAND["ink"]
            ax.text(j, i, int(valor), ha="center", va="center", fontsize=7.5, color=cor_texto)

    barra_cor = fig.colorbar(imagem, ax=ax, fraction=0.025, pad=0.02)
    barra_cor.outline.set_visible(False)
    barra_cor.set_label("Mensagens")

    fig.tight_layout()
    rodape_assinatura(fig)

    return fig


def grafico_barras_simples(tabela, coluna_x, coluna_y, titulo, rotulo_x, rotulo_y, cor=None):
    """Um único gráfico de barras (sem quebra por pessoa), cor de marca."""

    fig, ax = plt.subplots(figsize=FIGSIZE_LARGO)

    ax.bar(tabela[coluna_x].astype(str), tabela[coluna_y], color=cor or BRAND["primary"], width=0.65, zorder=3)

    ax.set_title(titulo)
    ax.set_xlabel(rotulo_x)
    ax.set_ylabel(rotulo_y)
    ax.set_ylim(0, max(tabela[coluna_y].max() * 1.18, 1))
    estilizar_eixo(ax)
    rotular_barras(ax, "{:.0f}")
    plt.setp(ax.get_xticklabels(), rotation=0 if len(tabela) <= 10 else 45, ha="center" if len(tabela) <= 10 else "right")

    fig.tight_layout()
    rodape_assinatura(fig)

    return fig


def grafico_linhas_por_categoria(
    tabela_longa: pd.DataFrame,
    coluna_x: str,
    coluna_y: str,
    coluna_cor: str,
    titulo: str,
    rotulo_x: str,
    rotulo_y: str,
    color_map: dict,
    ordem_x: list,
):
    """Uma linha por pessoa sobre um eixo categórico (dia da semana, hora do dia...).

    Diferente de `grafico_linha_temporal`, o eixo x aqui não é uma data —
    é uma categoria com ordem fixa (`ordem_x`), então cada linha é
    reindexada nessa ordem antes de desenhar.
    """

    fig, ax = plt.subplots(figsize=FIGSIZE_LARGO)

    for nome, grupo in tabela_longa.groupby(coluna_cor, observed=True):
        grupo = grupo.set_index(coluna_x).reindex(ordem_x).reset_index()
        ax.plot(
            [str(v) for v in grupo[coluna_x]], grupo[coluna_y],
            label=nome, color=color_map.get(nome, BRAND["primary"]),
            linewidth=2.2, marker="o", markersize=4.5,
        )

    ax.set_title(titulo)
    ax.set_xlabel(rotulo_x)
    ax.set_ylabel(rotulo_y)
    estilizar_eixo(ax)

    muitas_categorias = len(ordem_x) > 10
    plt.setp(
        ax.get_xticklabels(),
        rotation=0 if muitas_categorias else 20,
        ha="center" if muitas_categorias else "right",
        fontsize=9 if muitas_categorias else 10.5,
    )
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0)

    fig.tight_layout()
    rodape_assinatura(fig)

    return fig


def grafico_linha_temporal(tabela_longa, coluna_x, coluna_y, coluna_cor, titulo, rotulo_y, color_map):
    """Série temporal com uma linha por pessoa."""

    fig, ax = plt.subplots(figsize=(12, 5.8))

    for nome, grupo in tabela_longa.groupby(coluna_cor, observed=True):
        grupo = grupo.sort_values(coluna_x)
        ax.plot(
            grupo[coluna_x], grupo[coluna_y],
            label=nome, color=color_map.get(nome, BRAND["primary"]),
            linewidth=2.4, marker="o", markersize=4.5,
        )

    ax.set_title(titulo)
    ax.set_ylabel(rotulo_y)
    estilizar_eixo(ax)
    fig.autofmt_xdate(rotation=35)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0)

    fig.tight_layout()
    rodape_assinatura(fig)

    return fig


def _colormap_marca():
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list(
        "marca", ["#F2FBF9", BRAND["accent"], BRAND["dark"]]
    )
