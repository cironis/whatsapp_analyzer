"""Tipos compartilhados entre os módulos de análise e o gerador de relatório.

Qualquer nova análise futura deve devolver um `AnalysisResult` e produzir
`ChartArtifact`s a partir de figuras matplotlib — é esse contrato que o
pipeline, o ZIP de imagens e o PDF sabem consumir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

import pandas as pd

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from .media_store import MediaStore


@dataclass
class ChartArtifact:
    """Um gráfico já renderizado, pronto para ir ao ZIP e ao PDF."""

    slug: str
    title: str
    figure: "Figure"
    caption: str = ""
    png: Optional[bytes] = None

    def filename(self) -> str:
        return f"{self.slug}.png"


@dataclass
class AnalysisContext:
    """Tudo que uma análise pode precisar para rodar."""

    df: pd.DataFrame
    color_map: dict
    people: list
    has_media: bool
    media_store: Optional["MediaStore"]
    group_label: str = "a conversa"


@dataclass
class AnalysisResult:
    """Saída padronizada de uma análise: tabelas, gráficos e insights."""

    key: str
    title: str
    icon: str
    tables: dict = field(default_factory=dict)
    charts: list = field(default_factory=list)
    insights: list = field(default_factory=list)
    intro: str = ""
