"""Gera o relatório em PDF: capa com KPIs, e uma seção por análise."""

from __future__ import annotations

import io

from PIL import Image as PILImage
from reportlab.lib import colors as rl_colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from ..colors import BRAND
from ..icons import obter_icone_png
from ..utils import formatar_numero

LARGURA_PAGINA, ALTURA_PAGINA = A4
MARGEM = 1.8 * cm
MARGEM_TOPO = 1.9 * cm
MARGEM_BASE = 1.7 * cm
LARGURA_CONTEUDO = LARGURA_PAGINA - 2 * MARGEM
ALTURA_MAX_IMAGEM = 21 * cm


def _cor(hexadecimal: str):
    return rl_colors.HexColor(hexadecimal)


def _estilos() -> dict:
    return {
        "capa_titulo": ParagraphStyle(
            "capa_titulo", fontName="Helvetica-Bold", fontSize=26, leading=31,
            textColor=_cor(BRAND["dark"]), alignment=TA_CENTER, spaceAfter=6,
        ),
        "capa_subtitulo": ParagraphStyle(
            "capa_subtitulo", fontName="Helvetica", fontSize=12.5, leading=17,
            textColor=_cor(BRAND["muted"]), alignment=TA_CENTER,
        ),
        "kpi_numero": ParagraphStyle(
            "kpi_numero", fontName="Helvetica-Bold", fontSize=18, leading=21,
            textColor=_cor(BRAND["dark"]), alignment=TA_CENTER,
        ),
        "kpi_rotulo": ParagraphStyle(
            "kpi_rotulo", fontName="Helvetica", fontSize=8.7, leading=11,
            textColor=_cor(BRAND["muted"]), alignment=TA_CENTER,
        ),
        "secao_titulo": ParagraphStyle(
            "secao_titulo", fontName="Helvetica-Bold", fontSize=17, leading=20,
            textColor=_cor(BRAND["dark"]),
        ),
        "intro": ParagraphStyle(
            "intro", fontName="Helvetica-Oblique", fontSize=10, leading=14,
            textColor=_cor(BRAND["muted"]), spaceAfter=8,
        ),
        "insight": ParagraphStyle(
            "insight", fontName="Helvetica", fontSize=10.3, leading=14.5,
            textColor=_cor(BRAND["ink"]), leftIndent=10, spaceAfter=4,
        ),
        "legenda": ParagraphStyle(
            "legenda", fontName="Helvetica-Oblique", fontSize=8.3, leading=11,
            textColor=_cor(BRAND["muted"]), alignment=TA_CENTER, spaceBefore=3, spaceAfter=14,
        ),
        "rodape_capa": ParagraphStyle(
            "rodape_capa", fontName="Helvetica", fontSize=8.5, leading=12,
            textColor=_cor(BRAND["muted"]), alignment=TA_CENTER,
        ),
    }


class _RelatorioDocTemplate(BaseDocTemplate):
    """DocTemplate que gera marcadores (bookmarks) a partir dos títulos de seção."""

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "secao_titulo":
            texto = flowable.getPlainText()
            chave = f"secao-{texto}"
            self.canv.bookmarkPage(chave)
            self.canv.addOutlineEntry(texto, chave, level=0)


def _rodape(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(_cor(BRAND["line"]))
    canvas.setLineWidth(0.7)
    canvas.line(MARGEM, 1.25 * cm, LARGURA_PAGINA - MARGEM, 1.25 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(_cor(BRAND["muted"]))
    canvas.drawString(MARGEM, 0.9 * cm, "Gerado por WhatsApp Analyzer")
    canvas.drawRightString(LARGURA_PAGINA - MARGEM, 0.9 * cm, f"Página {doc.page}")
    canvas.restoreState()


def _imagem_ajustada(png_bytes: bytes, largura_max=LARGURA_CONTEUDO, altura_max=ALTURA_MAX_IMAGEM):
    imagem_pil = PILImage.open(io.BytesIO(png_bytes))
    largura_px, altura_px = imagem_pil.size
    razao = largura_px / altura_px if altura_px else 1

    largura, altura = largura_max, largura_max / razao
    if altura > altura_max:
        altura = altura_max
        largura = altura * razao

    imagem = Image(io.BytesIO(png_bytes), width=largura, height=altura)
    imagem.hAlign = "CENTER"
    return imagem


def _cartao_kpi(icone_bytes: bytes, numero_texto: str, rotulo_texto: str, estilos: dict):
    icone_img = Image(io.BytesIO(icone_bytes), width=0.85 * cm, height=0.85 * cm)
    icone_img.hAlign = "CENTER"

    tabela = Table(
        [[icone_img], [Paragraph(numero_texto, estilos["kpi_numero"])], [Paragraph(rotulo_texto, estilos["kpi_rotulo"])]],
        colWidths=[LARGURA_CONTEUDO / 3 - 0.6 * cm],
    )
    tabela.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), _cor(BRAND["bg"])),
                ("BOX", (0, 0), (-1, -1), 0.7, _cor(BRAND["line"])),
                ("TOPPADDING", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
                ("TOPPADDING", (0, 1), (-1, 2), 2),
            ]
        )
    )
    return tabela


def _grade_kpis(cartoes: list, colunas: int = 3):
    linhas = [cartoes[i : i + colunas] for i in range(0, len(cartoes), colunas)]
    if linhas and len(linhas[-1]) < colunas:
        linhas[-1] += [""] * (colunas - len(linhas[-1]))

    tabela = Table(linhas, colWidths=[LARGURA_CONTEUDO / colunas] * colunas)
    tabela.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return tabela


def _construir_capa(meta: dict, estilos: dict) -> list:
    icone_capa = Image(io.BytesIO(obter_icone_png("chat", BRAND["primary"], 320)), width=2.5 * cm, height=2.5 * cm)
    icone_capa.hAlign = "CENTER"

    elementos = [
        Spacer(1, 1.4 * cm),
        icone_capa,
        Spacer(1, 0.5 * cm),
        Paragraph("Análise da Conversa do WhatsApp", estilos["capa_titulo"]),
        Paragraph(meta["rotulo_grupo"], estilos["capa_subtitulo"]),
        Paragraph(
            f"{meta['periodo_inicio']} — {meta['periodo_fim']} · {meta['recorte_periodo']}",
            estilos["capa_subtitulo"],
        ),
        Spacer(1, 0.7 * cm),
        HRFlowable(width="35%", thickness=1.6, color=_cor(BRAND["accent"]), spaceAfter=16, hAlign="CENTER"),
        _grade_kpis(
            [
                _cartao_kpi(obter_icone_png("pessoas", BRAND["primary"]), str(meta["num_pessoas"]), "Participantes", estilos),
                _cartao_kpi(obter_icone_png("chat", BRAND["primary"]), formatar_numero(meta["total_mensagens"]), "Mensagens", estilos),
                _cartao_kpi(obter_icone_png("texto", BRAND["primary"]), formatar_numero(meta["total_caracteres"]), "Caracteres", estilos),
                _cartao_kpi(obter_icone_png("calendario", BRAND["primary"]), str(meta["dias_com_mensagem"]), "Dias com conversa", estilos),
                _cartao_kpi(obter_icone_png("faisca", BRAND["primary"]), str(meta["maior_sequencia"]), "Sequência recorde (dias)", estilos),
                _cartao_kpi(obter_icone_png("clipe", BRAND["primary"]), "Incluída" if meta["tem_midia"] else "Não incluída", "Mídia no arquivo", estilos),
            ]
        ),
        Spacer(1, 1.3 * cm),
        Paragraph(f"Relatório gerado em {meta['gerado_em']}.", estilos["rodape_capa"]),
        Paragraph("Os nomes exibidos foram configurados por quem gerou este relatório.", estilos["rodape_capa"]),
        PageBreak(),
    ]

    return elementos


def _cabecalho_secao(resultado, estilos: dict):
    icone_img = Image(io.BytesIO(obter_icone_png(resultado.icon, BRAND["primary"], 200)), width=0.8 * cm, height=0.8 * cm)

    tabela = Table(
        [[icone_img, Paragraph(resultado.title, estilos["secao_titulo"])]],
        colWidths=[1.05 * cm, LARGURA_CONTEUDO - 1.05 * cm],
    )
    tabela.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return tabela


def _construir_bloco_secao(resultado, estilos: dict) -> list:
    cabecalho = [_cabecalho_secao(resultado, estilos), HRFlowable(width="100%", thickness=0.8, color=_cor(BRAND["line"]), spaceAfter=10)]

    if resultado.intro:
        cabecalho.append(Paragraph(resultado.intro, estilos["intro"]))

    for texto in resultado.insights:
        cabecalho.append(Paragraph(f"● {texto}", estilos["insight"]))

    if resultado.insights:
        cabecalho.append(Spacer(1, 0.35 * cm))

    return cabecalho


def construir_pdf(resultados: list, meta: dict) -> bytes:
    """Monta o PDF completo e retorna os bytes prontos para download."""

    estilos = _estilos()
    buffer = io.BytesIO()

    doc = _RelatorioDocTemplate(
        buffer, pagesize=A4, leftMargin=MARGEM, rightMargin=MARGEM,
        topMargin=MARGEM_TOPO, bottomMargin=MARGEM_BASE,
        title="Análise da Conversa do WhatsApp",
    )
    quadro = Frame(
        MARGEM, MARGEM_BASE, LARGURA_CONTEUDO, ALTURA_PAGINA - MARGEM_TOPO - MARGEM_BASE, id="conteudo",
    )
    doc.addPageTemplates([PageTemplate(id="pagina", frames=[quadro], onPage=_rodape)])

    historia = list(_construir_capa(meta, estilos))

    for resultado in resultados:
        if not resultado.charts:
            continue

        historia.append(KeepTogether(_construir_bloco_secao(resultado, estilos)))

        for grafico in resultado.charts:
            if not grafico.png:
                continue

            historia.append(_imagem_ajustada(grafico.png))

            if grafico.caption:
                historia.append(Paragraph(grafico.caption, estilos["legenda"]))
            else:
                historia.append(Spacer(1, 0.5 * cm))

        historia.append(PageBreak())

    while historia and isinstance(historia[-1], PageBreak):
        historia.pop()

    doc.build(historia)

    buffer.seek(0)
    return buffer.getvalue()
