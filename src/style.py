"""Estilo visual compartilhado por todos os gráficos matplotlib do app."""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt

from .colors import BRAND

matplotlib.use("Agg")

DPI = 200
FIGSIZE_PADRAO = (9, 5.2)
FIGSIZE_LARGO = (11.5, 5.5)
FIGSIZE_QUADRADO = (8, 8)


def aplicar_estilo_global() -> None:
    """Configura os rcParams uma única vez para todos os gráficos do app."""

    plt.rcParams.update(
        {
            "figure.max_open_warning": 0,
            "figure.dpi": DPI,
            "savefig.dpi": DPI,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Segoe UI",
                "DejaVu Sans",
                "Arial",
                "Helvetica",
            ],
            "font.size": 12,
            "axes.titlesize": 15,
            "axes.titleweight": "bold",
            "axes.titlepad": 14,
            "axes.labelsize": 11.5,
            "axes.labelcolor": BRAND["muted"],
            "axes.edgecolor": BRAND["line"],
            "axes.linewidth": 1.0,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": BRAND["line"],
            "grid.linewidth": 0.9,
            "xtick.color": BRAND["ink"],
            "ytick.color": BRAND["ink"],
            "xtick.labelsize": 10.5,
            "ytick.labelsize": 10.5,
            "text.color": BRAND["ink"],
            "legend.frameon": False,
            "legend.fontsize": 10.5,
            "figure.titlesize": 18,
            "figure.titleweight": "bold",
        }
    )


def estilizar_eixo(eixo, grade_y=True, grade_x=False) -> None:
    """Aplica o acabamento padrão (sem bordas supérfluas) a um eixo."""

    for lado in ("top", "right"):
        eixo.spines[lado].set_visible(False)

    eixo.spines["left"].set_color(BRAND["line"])
    eixo.spines["bottom"].set_color(BRAND["line"])

    if grade_y:
        eixo.grid(True, axis="y", color=BRAND["line"], linewidth=0.9)
    if grade_x:
        eixo.grid(True, axis="x", color=BRAND["line"], linewidth=0.9)
    eixo.set_axisbelow(True)


def rotular_barras(eixo, formato="{:.0f}", cor=None, tamanho=10.5) -> None:
    """Escreve o valor no topo de cada barra de um gráfico de barras."""

    for barra in eixo.patches:
        altura = barra.get_height()

        if altura is None:
            continue

        eixo.annotate(
            formato.format(altura),
            xy=(barra.get_x() + barra.get_width() / 2, altura),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=tamanho,
            fontweight="bold",
            color=cor or BRAND["ink"],
        )


def rodape_assinatura(figura, texto="Gerado por WhatsApp Analyzer") -> None:
    """Escreve uma assinatura discreta no rodapé da figura."""

    figura.text(
        0.995,
        0.008,
        texto,
        ha="right",
        va="bottom",
        fontsize=8,
        color=BRAND["muted"],
        alpha=0.8,
    )
