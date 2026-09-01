"""Ícones simples desenhados com matplotlib (sem depender de assets externos).

Cada função `_icone_*` desenha em um eixo 0–10 x 0–10. `render_icone` rasteriza
para PNG com fundo transparente e `obter_icone` cacheia o resultado em bytes.
"""

from __future__ import annotations

import io
from functools import lru_cache

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle
from matplotlib.path import Path as MplPath

from .colors import BRAND


def _sem_eixo(ax):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")


def _icone_chat(ax, cor):
    corpo = FancyBboxPatch(
        (0.8, 3.6), 8.4, 5.4,
        boxstyle="round,pad=0,rounding_size=1.4",
        linewidth=0, facecolor=cor,
    )
    rabicho = Polygon([[2.3, 3.9], [2.3, 1.3], [4.6, 3.9]], closed=True, facecolor=cor, linewidth=0)
    ax.add_patch(corpo)
    ax.add_patch(rabicho)
    for x in (2.6, 4.4, 6.2):
        ax.add_patch(Circle((x, 6.3), 0.55, facecolor="white", linewidth=0))


def _icone_texto(ax, cor):
    folha = FancyBboxPatch(
        (1.6, 0.8), 6.8, 8.4,
        boxstyle="round,pad=0,rounding_size=0.5",
        linewidth=0, facecolor=cor,
    )
    ax.add_patch(folha)
    for y in (6.6, 5.4, 4.2, 3.0):
        largura = 4.6 if y != 3.0 else 2.6
        ax.add_patch(Rectangle((2.7, y), largura, 0.55, facecolor="white", linewidth=0))


def _icone_calendario(ax, cor):
    corpo = FancyBboxPatch(
        (0.8, 0.8), 8.4, 7.4,
        boxstyle="round,pad=0,rounding_size=0.6",
        linewidth=0, facecolor=cor,
    )
    topo = Rectangle((0.8, 6.6), 8.4, 1.6, facecolor=BRAND["dark"], linewidth=0)
    ax.add_patch(corpo)
    ax.add_patch(topo)
    for x in (2.6, 7.4):
        ax.add_patch(Rectangle((x - 0.35, 7.6), 0.7, 1.6, facecolor=BRAND["ink"], linewidth=0))
    for linha in range(3):
        for coluna in range(3):
            ax.add_patch(
                Rectangle(
                    (2.0 + coluna * 2.1, 1.6 + linha * 1.7), 1.4, 1.1,
                    facecolor="white", linewidth=0, alpha=0.9,
                )
            )


def _icone_trofeu(ax, cor):
    taca = Polygon(
        [[3.0, 5.2], [2.0, 8.6], [8.0, 8.6], [7.0, 5.2]],
        closed=True, facecolor=cor, linewidth=0,
    )
    alca_esq = Circle((2.0, 7.6), 1.05, facecolor="none", edgecolor=cor, linewidth=1.6)
    alca_dir = Circle((8.0, 7.6), 1.05, facecolor="none", edgecolor=cor, linewidth=1.6)
    pe = Rectangle((4.5, 3.0), 1.0, 2.3, facecolor=cor, linewidth=0)
    base = FancyBboxPatch((3.0, 1.6), 4.0, 1.3, boxstyle="round,pad=0,rounding_size=0.3", facecolor=cor, linewidth=0)
    ax.add_patch(taca)
    ax.add_patch(alca_esq)
    ax.add_patch(alca_dir)
    ax.add_patch(pe)
    ax.add_patch(base)
    ax.add_patch(Circle((5.0, 6.4), 0.55, facecolor="white", linewidth=0, alpha=0.85))


def _icone_microfone(ax, cor):
    ax.add_patch(FancyBboxPatch((3.6, 4.2), 2.8, 5.0, boxstyle="round,pad=0,rounding_size=1.4", facecolor=cor, linewidth=0))
    arco = MplPath.arc(200, 340)
    verts = arco.vertices * 2.6 + [5.0, 4.6]
    ax.add_patch(plt.Polygon(verts, closed=False, fill=False, edgecolor=cor, linewidth=1.7))
    ax.plot([5.0, 5.0], [2.0, 3.4], color=cor, linewidth=1.7, solid_capstyle="round")
    ax.plot([3.6, 6.4], [2.0, 2.0], color=cor, linewidth=1.7, solid_capstyle="round")


def _icone_imagem(ax, cor):
    moldura = FancyBboxPatch((0.8, 1.2), 8.4, 7.0, boxstyle="round,pad=0,rounding_size=0.6", facecolor="white", edgecolor=cor, linewidth=1.8)
    ax.add_patch(moldura)
    ax.add_patch(Circle((3.1, 5.7), 0.85, facecolor=cor, linewidth=0))
    montanha = Polygon([[1.4, 2.0], [4.1, 5.0], [5.7, 3.4], [8.6, 2.0]], closed=False, fill=False, edgecolor=cor, linewidth=1.8, joinstyle="round")
    ax.add_patch(montanha)
    ax.add_patch(Rectangle((1.4, 1.3), 7.2, 0.15, facecolor=cor, linewidth=0, alpha=0))


def _icone_figurinha(ax, cor):
    corpo = Polygon(
        [[1.2, 8.6], [7.0, 8.6], [8.6, 7.0], [8.6, 1.2], [1.2, 1.2]],
        closed=True, facecolor=cor, linewidth=0,
    )
    dobra = Polygon([[7.0, 8.6], [7.0, 7.0], [8.6, 7.0]], closed=True, facecolor=BRAND["dark"], linewidth=0)
    ax.add_patch(corpo)
    ax.add_patch(dobra)
    estrela_x = [5.0, 5.6, 6.7, 5.8, 6.1, 5.0, 3.9, 4.2, 3.3, 4.4]
    estrela_y = [6.3, 5.1, 4.9, 4.1, 2.9, 3.6, 2.9, 4.1, 4.9, 5.1]
    ax.add_patch(Polygon(list(zip(estrela_x, estrela_y)), closed=True, facecolor="white", linewidth=0))


def _icone_grade(ax, cor):
    import numpy as np

    rng = [0.35, 0.65, 1.0, 0.5, 0.8]
    for linha in range(4):
        for coluna in range(7):
            intensidade = rng[(linha * 7 + coluna) % len(rng)]
            ax.add_patch(
                Rectangle(
                    (0.4 + coluna * 1.3, 0.6 + linha * 2.2), 1.05, 1.75,
                    facecolor=cor, alpha=0.35 + 0.65 * intensidade, linewidth=0,
                )
            )


def _icone_pessoas(ax, cor):
    ax.add_patch(Circle((3.6, 6.6), 1.55, facecolor=cor, linewidth=0))
    ax.add_patch(FancyBboxPatch((1.3, 0.8), 4.6, 3.6, boxstyle="round,pad=0,rounding_size=1.6", facecolor=cor, linewidth=0))
    ax.add_patch(Circle((7.2, 6.9), 1.15, facecolor=cor, alpha=0.55, linewidth=0))
    ax.add_patch(FancyBboxPatch((5.4, 1.6), 3.6, 2.8, boxstyle="round,pad=0,rounding_size=1.3", facecolor=cor, alpha=0.55, linewidth=0))


def _icone_relogio(ax, cor):
    ax.add_patch(Circle((5, 5), 4.0, facecolor="none", edgecolor=cor, linewidth=1.8))
    ax.plot([5, 5], [5, 7.3], color=cor, linewidth=1.8, solid_capstyle="round")
    ax.plot([5, 6.9], [5, 5], color=cor, linewidth=1.8, solid_capstyle="round")
    ax.add_patch(Circle((5, 5), 0.35, facecolor=cor, linewidth=0))


def _icone_clipe(ax, cor):
    # Duas argolas entrelaçadas, como um clipe de anexo.
    ax.add_patch(
        FancyBboxPatch(
            (1.5, 5.1), 4.4, 2.9, boxstyle="round,pad=0,rounding_size=1.4",
            linewidth=2.8, edgecolor=cor, facecolor="none",
        )
    )
    ax.add_patch(
        FancyBboxPatch(
            (4.4, 2.0), 4.4, 2.9, boxstyle="round,pad=0,rounding_size=1.4",
            linewidth=2.8, edgecolor=cor, facecolor="none",
        )
    )


def _icone_faisca(ax, cor):
    chama = Polygon(
        [[5.0, 9.0], [3.4, 6.3], [4.2, 6.3], [3.6, 4.0], [6.6, 6.6], [5.6, 6.6], [7.0, 8.6],
         [5.9, 8.0], [6.2, 9.4]],
        closed=True, facecolor=cor, linewidth=0,
    )
    ax.add_patch(chama)
    ax.add_patch(Circle((5.0, 2.4), 1.7, facecolor=cor, alpha=0.9, linewidth=0))


_DESENHOS = {
    "chat": _icone_chat,
    "texto": _icone_texto,
    "calendario": _icone_calendario,
    "trofeu": _icone_trofeu,
    "microfone": _icone_microfone,
    "imagem": _icone_imagem,
    "figurinha": _icone_figurinha,
    "grade": _icone_grade,
    "pessoas": _icone_pessoas,
    "relogio": _icone_relogio,
    "clipe": _icone_clipe,
    "faisca": _icone_faisca,
}


@lru_cache(maxsize=None)
def obter_icone_png(nome: str, cor: str = BRAND["primary"], tamanho_px: int = 240) -> bytes:
    """Renderiza um ícone para PNG (fundo transparente) e cacheia o resultado."""

    desenhar = _DESENHOS.get(nome, _icone_chat)

    fig, ax = plt.subplots(figsize=(tamanho_px / 100, tamanho_px / 100), dpi=100)
    _sem_eixo(ax)
    desenhar(ax, cor)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", transparent=True)
    plt.close(fig)

    buffer.seek(0)
    return buffer.read()


NOMES_DISPONIVEIS = tuple(_DESENHOS)
