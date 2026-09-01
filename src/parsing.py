"""Leitura de exportações do WhatsApp (.zip com ou sem mídia, ou .txt)."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Optional

import pandas as pd

from .media_store import MediaStore
from .utils import limpar_texto_invisivel

# Exemplos de primeira linha de uma mensagem:
#   6/10/26, 09:36 - Luiza: mensagem
#   10/06/2026, 9:36 AM - Luiza: mensagem
#   10/06/2026, 09:36 - Luiza: STK-20260612-WA0014.webp (file attached)
PADRAO_MENSAGEM = re.compile(
    r"^(?P<data>\d{1,2}/\d{1,2}/\d{2,4}),?\s+"
    r"(?P<hora>\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap][Mm])?)\s*"
    r"[-–]\s*"
    r"(?P<nome>.*?):\s(?P<mensagem>.*)$"
)

# Reconhece qualquer linha que comece com data e hora, incluindo
# notificações do sistema (sem remetente, ex.: "fulano entrou no grupo").
PADRAO_INICIO = re.compile(
    r"^\d{1,2}/\d{1,2}/\d{2,4},?\s+"
    r"\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap][Mm])?\s*[-–]\s*"
)

PADRAO_DATA_COMPONENTES = re.compile(r"^(\d{1,2})/(\d{1,2})/\d{2,4}$")

PADRAO_ARQUIVO_ANEXADO = re.compile(
    r"^(?P<arquivo>[^/\\\r\n]+?)\s*\((?:file attached|arquivo anexado)\)\s*$",
    flags=re.IGNORECASE,
)


class ArquivoInvalidoError(ValueError):
    """Erro amigável quando o arquivo enviado não é uma exportação válida."""


def _detectar_dayfirst(datas: pd.Series) -> bool:
    """Detecta se o formato é DD/MM ou MM/DD olhando os componentes.

    Todo o histórico usa a mesma ordem, então basta achar uma linha em
    que um dos componentes seja maior que 12 para decidir com certeza.
    Sem nenhum indício, assume DD/MM (padrão mais comum no Brasil).
    """

    primeiro_maior_que_12 = False
    segundo_maior_que_12 = False

    for valor in datas.dropna().unique():
        correspondencia = PADRAO_DATA_COMPONENTES.match(str(valor))

        if not correspondencia:
            continue

        primeiro, segundo = int(correspondencia.group(1)), int(correspondencia.group(2))

        if primeiro > 12:
            primeiro_maior_que_12 = True
        if segundo > 12:
            segundo_maior_que_12 = True

    if primeiro_maior_que_12:
        return True

    if segundo_maior_que_12:
        return False

    return True


def _extrair_arquivo_anexado(mensagem) -> Optional[str]:
    """Extrai o nome do arquivo quando a mensagem é um anexo real."""

    if pd.isna(mensagem):
        return None

    texto = limpar_texto_invisivel(mensagem).splitlines()[0] if mensagem else ""
    correspondencia = PADRAO_ARQUIVO_ANEXADO.match(texto)

    return correspondencia.group("arquivo").strip() if correspondencia else None


def _ler_linhas_txt(texto_completo: str) -> pd.DataFrame:
    registros = []
    registro_atual = None

    for linha in texto_completo.splitlines():
        linha = limpar_texto_invisivel(linha)

        correspondencia = PADRAO_MENSAGEM.match(linha)

        if correspondencia:
            if registro_atual is not None:
                registros.append(registro_atual)

            registro_atual = correspondencia.groupdict()

        elif PADRAO_INICIO.match(linha):
            # Notificação do sistema, sem remetente — encerra a mensagem atual.
            if registro_atual is not None:
                registros.append(registro_atual)
                registro_atual = None

        elif registro_atual is not None:
            # Continuação de uma mensagem com várias linhas.
            registro_atual["mensagem"] += "\n" + linha

    if registro_atual is not None:
        registros.append(registro_atual)

    df = pd.DataFrame(registros)

    if df.empty:
        raise ArquivoInvalidoError(
            "Nenhuma mensagem foi encontrada no arquivo. Verifique se é "
            "mesmo uma exportação de conversa do WhatsApp (.txt ou .zip)."
        )

    dayfirst = _detectar_dayfirst(df["data"])

    df["data"] = pd.to_datetime(
        df["data"] + " " + df["hora"],
        format="mixed",
        dayfirst=dayfirst,
        errors="coerce",
    )

    df = df.dropna(subset=["data"]).copy()

    if df.empty:
        raise ArquivoInvalidoError(
            "Não foi possível interpretar as datas das mensagens."
        )

    df["nome"] = df["nome"].astype(str).str.strip()
    df["nome_arquivo_anexo"] = df["mensagem"].apply(_extrair_arquivo_anexado)

    df = df.sort_values("data", kind="stable").reset_index(drop=True)

    return df[["data", "nome", "mensagem", "nome_arquivo_anexo"]]


def _escolher_txt_principal(pacote: zipfile.ZipFile) -> zipfile.ZipInfo:
    candidatos = [
        info
        for info in pacote.infolist()
        if not info.is_dir() and Path(info.filename).suffix.lower() == ".txt"
    ]

    if not candidatos:
        raise ArquivoInvalidoError(
            "O ZIP enviado não contém um arquivo .txt de conversa. "
            "Envie o .zip exportado pelo WhatsApp (Mais opções → "
            "Exportar conversa)."
        )

    # Numa exportação normal há um único TXT; se houver mais, o maior
    # tende a ser o histórico principal da conversa.
    return max(candidatos, key=lambda info: info.file_size)


def carregar_exportacao(conteudo: bytes, nome_arquivo: str) -> tuple[pd.DataFrame, MediaStore]:
    """Lê um .zip (com ou sem mídia) ou .txt exportado do WhatsApp.

    Retorna o DataFrame bruto (uma linha por mensagem) e um `MediaStore`
    para acessar eventuais anexos.
    """

    extensao = Path(nome_arquivo).suffix.lower()

    if extensao == ".zip":
        try:
            pacote = zipfile.ZipFile(io.BytesIO(conteudo))
        except zipfile.BadZipFile as erro:
            raise ArquivoInvalidoError(
                "O arquivo enviado não é um .zip válido."
            ) from erro

        txt_info = _escolher_txt_principal(pacote)

        with pacote.open(txt_info, "r") as origem:
            texto_completo = origem.read().decode("utf-8-sig", errors="replace")

        df = _ler_linhas_txt(texto_completo)
        media_store = MediaStore(conteudo)

        return df, media_store

    if extensao == ".txt":
        texto_completo = conteudo.decode("utf-8-sig", errors="replace")
        df = _ler_linhas_txt(texto_completo)

        return df, MediaStore(None)

    raise ArquivoInvalidoError(
        "Formato não suportado. Envie o .zip exportado pelo WhatsApp "
        "(com ou sem mídia)."
    )


def listar_nomes(df: pd.DataFrame) -> list:
    """Lista os nomes originais encontrados, em ordem alfabética."""

    return sorted(df["nome"].dropna().unique().tolist())
