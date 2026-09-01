"""Acesso à mídia dentro do ZIP exportado pelo WhatsApp.

Uma exportação "sem mídia" traz só o .txt, com `<Media omitted>` genérico
no lugar de cada anexo — nesse caso não há como saber se era um áudio, uma
figurinha ou uma foto. Uma exportação "com mídia" traz os arquivos de
verdade e o .txt referencia cada um pelo nome real (ex.: `STK-...webp
(file attached)`), o que permite classificar o tipo exato do anexo.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Optional

# Prefixos usados pelo próprio WhatsApp ao nomear os anexos. São o sinal
# mais confiável de tipo — mais confiável até que a extensão sozinha,
# já que uma figurinha e uma foto podem ambas usar extensões de imagem.
PREFIXOS_TIPO = {
    "IMG": "imagem",
    "STK": "figurinha",
    "PTT": "audio",
    "AUD": "audio",
    "VID": "video",
    "DOC": "documento",
    "VCARD": "contato",
}

EXTENSOES_TIPO = {
    ".webp": "figurinha",
    ".jpg": "imagem",
    ".jpeg": "imagem",
    ".png": "imagem",
    ".gif": "imagem",
    ".aac": "audio",
    ".flac": "audio",
    ".m4a": "audio",
    ".mp3": "audio",
    ".oga": "audio",
    ".ogg": "audio",
    ".opus": "audio",
    ".wav": "audio",
    ".mp4": "video",
    ".mov": "video",
    ".avi": "video",
    ".mkv": "video",
    ".3gp": "video",
    ".pdf": "documento",
    ".doc": "documento",
    ".docx": "documento",
    ".xls": "documento",
    ".xlsx": "documento",
    ".ppt": "documento",
    ".pptx": "documento",
    ".zip": "documento",
    ".rar": "documento",
    ".vcf": "contato",
}

EXTENSOES_AUDIO = {
    ext for ext, tipo in EXTENSOES_TIPO.items() if tipo == "audio"
}

EXTENSOES_MIDIA = set(EXTENSOES_TIPO)


def classificar_por_nome_arquivo(nome_arquivo: Optional[str]) -> Optional[str]:
    """Classifica um anexo pelo prefixo/extensão do nome do arquivo.

    Retorna um dos tipos ("imagem", "figurinha", "audio", "video",
    "documento", "contato") ou None se o nome não permitir identificar.
    """

    if not nome_arquivo:
        return None

    nome = Path(str(nome_arquivo)).name
    prefixo = nome.split("-", 1)[0].upper()

    if prefixo in PREFIXOS_TIPO:
        return PREFIXOS_TIPO[prefixo]

    extensao = Path(nome).suffix.lower()

    return EXTENSOES_TIPO.get(extensao)


class MediaStore:
    """Acesso somente-leitura à mídia de um ZIP exportado do WhatsApp."""

    def __init__(self, zip_bytes: Optional[bytes]):
        self._zip_bytes = zip_bytes
        self._pacote: Optional[zipfile.ZipFile] = None
        self._indice: dict[str, zipfile.ZipInfo] = {}

        if zip_bytes is not None:
            import io

            self._pacote = zipfile.ZipFile(io.BytesIO(zip_bytes))

            for info in self._pacote.infolist():
                if info.is_dir():
                    continue

                nome = Path(info.filename).name.casefold()
                self._indice[nome] = info

    @property
    def has_media(self) -> bool:
        """Verdadeiro se o ZIP contiver algum arquivo de mídia de verdade."""

        if not self._indice:
            return False

        return any(
            Path(nome).suffix.lower() in EXTENSOES_MIDIA
            for nome in self._indice
        )

    def read(self, nome_arquivo: str) -> Optional[bytes]:
        """Lê os bytes de um anexo pelo nome (case-insensitive)."""

        if self._pacote is None or not nome_arquivo:
            return None

        info = self._indice.get(Path(nome_arquivo).name.casefold())

        if info is None:
            return None

        try:
            return self._pacote.read(info)
        except Exception:
            return None

    def contains(self, nome_arquivo: str) -> bool:
        if not nome_arquivo:
            return False

        return Path(nome_arquivo).name.casefold() in self._indice
