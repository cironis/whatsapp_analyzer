"""Orquestra o fluxo completo: parsing → renomeação → análises → entregáveis.

É o único módulo que o `app.py` (Streamlit) precisa conhecer em detalhe.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

import matplotlib.pyplot as plt

from . import enrich, parsing
from .analyses import ANALISES
from .colors import build_color_map
from .media_store import MediaStore
from .models import AnalysisContext
from .report.pdf_builder import construir_pdf
from .report.zip_builder import construir_zip_imagens
from .style import DPI, aplicar_estilo_global


@dataclass
class DadosCarregados:
    """Resultado do passo 1 (parsing rápido) — o suficiente para a tela de renomeação."""

    df_bruto: object
    media_store: MediaStore
    nomes_originais: list


@dataclass
class ResultadoPipeline:
    """Resultado final: pronto para os botões de download no Streamlit."""

    resultados: list
    zip_bytes: bytes
    pdf_bytes: bytes
    pessoas: list
    meta: dict


def carregar_para_renomear(conteudo: bytes, nome_arquivo: str) -> DadosCarregados:
    """Passo 1: lê o arquivo e lista os nomes originais para a tela de renomeação."""

    df_bruto, media_store = parsing.carregar_exportacao(conteudo, nome_arquivo)
    nomes_originais = parsing.listar_nomes(df_bruto)

    return DadosCarregados(df_bruto=df_bruto, media_store=media_store, nomes_originais=nomes_originais)


def executar_analise(
    dados: DadosCarregados,
    mapa_nomes: dict,
    rotulo_grupo: str = "Conversa do WhatsApp",
    progresso: Optional[Callable[[str], None]] = None,
) -> ResultadoPipeline:
    """Passo 2: aplica os nomes finais, roda as análises e monta ZIP + PDF."""

    aplicar_estilo_global()

    df = dados.df_bruto.copy()
    df["nome"] = df["nome"].replace(mapa_nomes or {})
    df = enrich.enriquecer(df)

    pessoas = sorted(df["nome"].dropna().unique().tolist())
    mapa_cores = build_color_map(pessoas)

    ctx = AnalysisContext(
        df=df,
        color_map=mapa_cores,
        people=pessoas,
        has_media=dados.media_store.has_media,
        media_store=dados.media_store,
        group_label=rotulo_grupo,
    )

    resultados = []
    for modulo in ANALISES:
        if getattr(modulo, "REQUIRES_MEDIA", False) and not ctx.has_media:
            continue

        if progresso:
            progresso(modulo.TITLE)

        resultado = modulo.run(ctx)

        if resultado.charts:
            resultados.append(resultado)

    _renderizar_pngs(resultados)

    meta = _montar_meta(df, pessoas, ctx.has_media, rotulo_grupo)

    zip_bytes = construir_zip_imagens(resultados)
    pdf_bytes = construir_pdf(resultados, meta)

    return ResultadoPipeline(
        resultados=resultados, zip_bytes=zip_bytes, pdf_bytes=pdf_bytes, pessoas=pessoas, meta=meta,
    )


def _renderizar_pngs(resultados: list) -> None:
    """Salva cada figura matplotlib como PNG uma única vez (ZIP e PDF reaproveitam)."""

    for resultado in resultados:
        for grafico in resultado.charts:
            buffer = io.BytesIO()
            grafico.figure.savefig(buffer, format="png", dpi=DPI, bbox_inches="tight", facecolor="white")
            grafico.png = buffer.getvalue()
            plt.close(grafico.figure)


def _montar_meta(df, pessoas: list, tem_midia: bool, rotulo_grupo: str) -> dict:
    return {
        "rotulo_grupo": rotulo_grupo,
        "periodo_inicio": df["data"].min().strftime("%d/%m/%Y"),
        "periodo_fim": df["data"].max().strftime("%d/%m/%Y"),
        "num_pessoas": len(pessoas),
        "total_mensagens": int(len(df)),
        "total_caracteres": int(df["quantidade_caracteres"].sum()),
        "dias_com_mensagem": int(df["data_calendario"].nunique()),
        "maior_sequencia": enrich.maior_sequencia_do_grupo(df),
        "tem_midia": tem_midia,
        "gerado_em": datetime.now().strftime("%d/%m/%Y às %H:%M"),
    }
