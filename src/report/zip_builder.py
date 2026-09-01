"""Monta o .zip com todas as imagens dos gráficos gerados."""

from __future__ import annotations

import io
import zipfile


def construir_zip_imagens(resultados: list) -> bytes:
    """Empacota o PNG já renderizado de cada gráfico em um .zip em memória."""

    buffer_zip = io.BytesIO()

    with zipfile.ZipFile(buffer_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as arquivo_zip:
        for resultado in resultados:
            for grafico in resultado.charts:
                if grafico.png:
                    arquivo_zip.writestr(grafico.filename(), grafico.png)

    buffer_zip.seek(0)
    return buffer_zip.getvalue()
