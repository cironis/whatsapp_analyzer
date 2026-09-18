"""Medição de duração de áudios a partir dos bytes reais dentro do .zip.

Compartilhado entre `analyses/media_gallery.py` (figurinhas e áudios) e
`analyses/evolucao_periodica.py` (evolução mensal/semanal) — os dois
precisam da duração real de cada áudio, lida com `mutagen`.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

try:
    from mutagen import File as MutagenFile
except ImportError:  # pragma: no cover - mutagen está no requirements.txt
    MutagenFile = None


def duracao_audio(caminho: Path):
    if MutagenFile is None:
        return None

    try:
        audio = MutagenFile(str(caminho))
        if audio is None or not hasattr(audio, "info"):
            return None
        return float(getattr(audio.info, "length", None) or 0) or None
    except Exception:
        return None


def medir_duracoes_audio(df: pd.DataFrame, media_store) -> pd.DataFrame:
    """Devolve as linhas de áudio de `df` com `duracao_audio_segundos` preenchida.

    Lê cada arquivo de áudio uma única vez (por nome), independente de
    quantas linhas do DataFrame o referenciam.
    """

    audios = df.loc[df["arquivo_audio"]].copy()

    if audios.empty:
        return audios

    duracoes = {}
    with tempfile.TemporaryDirectory() as pasta:
        pasta = Path(pasta)
        for indice, nome_arquivo in enumerate(audios["nome_arquivo_anexo"].dropna().unique(), start=1):
            conteudo = media_store.read(nome_arquivo)
            if conteudo is None:
                continue
            extensao = Path(nome_arquivo).suffix or ".opus"
            caminho_temporario = pasta / f"audio_{indice:05d}{extensao}"
            caminho_temporario.write_bytes(conteudo)
            duracoes[nome_arquivo.casefold()] = duracao_audio(caminho_temporario)

    audios["duracao_audio_segundos"] = audios["nome_arquivo_anexo"].str.casefold().map(duracoes)

    return audios
