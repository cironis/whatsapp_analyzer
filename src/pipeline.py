"""Orquestra o fluxo completo: parsing → renomeação → análises → entregáveis.

É o único módulo que o `app.py` (Streamlit) precisa conhecer em detalhe.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable, Optional

import matplotlib.pyplot as plt
import pandas as pd

from . import enrich, parsing
from .analyses import ANALISES
from .analyses.timeline import QUANTIDADE_DIAS as DIAS_JANELA_RECENTE
from .colors import build_color_map
from .media_store import MediaStore
from .models import AnalysisContext
from .report.pdf_builder import construir_pdf
from .report.zip_builder import construir_zip_imagens
from .style import DPI, aplicar_estilo_global
from .utils import formatar_mes_ano


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


def limites_periodo_disponivel(dados: DadosCarregados) -> tuple[date, date]:
    """Primeiro e último dia com mensagem no arquivo — usado no seletor de período."""

    datas = dados.df_bruto["data"]
    return datas.min().date(), datas.max().date()


def listar_meses_disponiveis(dados: DadosCarregados) -> list[tuple[int, int]]:
    """Lista (ano, mês) com pelo menos uma mensagem, do mais antigo ao mais recente."""

    periodos = dados.df_bruto["data"].dt.to_period("M").unique()

    return sorted((periodo.year, periodo.month) for periodo in periodos)


def _filtrar_por_periodo(
    df: "pd.DataFrame", filtro_periodo: Optional[dict]
) -> tuple["pd.DataFrame", Optional[pd.Timestamp], Optional[pd.Timestamp], str, str]:
    """Aplica o filtro de período escolhido e calcula a janela do gráfico de
    evolução recente (últimos 30 dias, exceto no modo "mes_ano", que mostra o
    mês inteiro).

    Retorna (df_filtrado, janela_inicio, janela_fim, titulo_janela, recorte_periodo).
    """

    filtro_periodo = filtro_periodo or {"modo": "geral"}
    modo = filtro_periodo.get("modo", "geral")

    if modo == "mes_ano":
        ano, mes = filtro_periodo["ano"], filtro_periodo["mes"]
        mes_inicio = pd.Timestamp(year=ano, month=mes, day=1)
        mes_fim = mes_inicio + pd.offsets.MonthEnd(1)
        limite_fim = mes_fim + pd.Timedelta(hours=23, minutes=59, seconds=59)

        df_filtrado = df.loc[df["data"].between(mes_inicio, limite_fim)].reset_index(drop=True)
        titulo_mes = formatar_mes_ano(ano, mes)

        return df_filtrado, mes_inicio, mes_fim, titulo_mes, f"Mês selecionado: {titulo_mes}"

    if modo == "periodo":
        inicio = pd.Timestamp(filtro_periodo["inicio"])
        fim = pd.Timestamp(filtro_periodo["fim"]) + pd.Timedelta(hours=23, minutes=59, seconds=59)
        df_filtrado = df.loc[df["data"].between(inicio, fim)].reset_index(drop=True)
        recorte_periodo = "Período selecionado"
    else:
        df_filtrado = df
        recorte_periodo = "Histórico completo"

    if df_filtrado.empty:
        return df_filtrado, None, None, f"Últimos {DIAS_JANELA_RECENTE} dias", recorte_periodo

    data_final = df_filtrado["data"].max().normalize()
    data_inicial = max(
        data_final - pd.Timedelta(days=DIAS_JANELA_RECENTE - 1),
        df_filtrado["data"].min().normalize(),
    )
    dias_na_janela = (data_final - data_inicial).days + 1

    return df_filtrado, data_inicial, data_final, f"Últimos {dias_na_janela} dias", recorte_periodo


def executar_analise(
    dados: DadosCarregados,
    mapa_nomes: dict,
    rotulo_grupo: str = "Conversa do WhatsApp",
    filtro_periodo: Optional[dict] = None,
    progresso: Optional[Callable[[str], None]] = None,
) -> ResultadoPipeline:
    """Passo 2: aplica os nomes finais e o filtro de período, roda as
    análises e monta ZIP + PDF.

    `filtro_periodo` é um dict com uma das formas:
      - {"modo": "geral"} (ou None) — usa todo o histórico;
      - {"modo": "mes_ano", "ano": 2026, "mes": 1} — só aquele mês;
      - {"modo": "periodo", "inicio": date(...), "fim": date(...)} — intervalo livre.
    """

    aplicar_estilo_global()

    df = dados.df_bruto.copy()
    df["nome"] = df["nome"].replace(mapa_nomes or {})

    df, janela_inicio, janela_fim, titulo_janela, recorte_periodo = _filtrar_por_periodo(df, filtro_periodo)

    if df.empty:
        raise ValueError("Não há mensagens no período selecionado. Escolha outro mês ou intervalo de datas.")

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
        janela_recente_inicio=janela_inicio,
        janela_recente_fim=janela_fim,
        janela_recente_titulo=titulo_janela,
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

    meta = _montar_meta(df, pessoas, ctx.has_media, rotulo_grupo, recorte_periodo)

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


def _montar_meta(df, pessoas: list, tem_midia: bool, rotulo_grupo: str, recorte_periodo: str) -> dict:
    return {
        "rotulo_grupo": rotulo_grupo,
        "periodo_inicio": df["data"].min().strftime("%d/%m/%Y"),
        "periodo_fim": df["data"].max().strftime("%d/%m/%Y"),
        "recorte_periodo": recorte_periodo,
        "num_pessoas": len(pessoas),
        "total_mensagens": int(len(df)),
        "total_caracteres": int(df["quantidade_caracteres"].sum()),
        "dias_com_mensagem": int(df["data_calendario"].nunique()),
        "maior_sequencia": enrich.maior_sequencia_do_grupo(df),
        "tem_midia": tem_midia,
        "gerado_em": datetime.now().strftime("%d/%m/%Y às %H:%M"),
    }
