"""Identificação da previsão oficial do Stage 2 (D28). Ver docs/previsao_oficial_stage2.md.

A pasta é congelada: nada aqui a altera. Atualizações ao vivo vão para
``predictions/stage2/round<N>/``.
"""

from __future__ import annotations

from ingest.vrs import PROJECT_ROOT

OFFICIAL_TAG = "stage2-oficial"
OFFICIAL_COMMIT = "7f8835fd9ae3f99fe68717916329b6525ebb25e1"
OFFICIAL_PUSH_UTC = "2026-11-27T16:13:36Z"  # API de atividade do GitHub
DEADLINE_UTC = "2026-11-28T04:00:00Z"  # primeiro jogo do Stage 2 (D17)
OFFICIAL_FOLDER_NAME = "20261127T161221Z"
OFFICIAL_RELATIVE = f"predictions/stage2/{OFFICIAL_FOLDER_NAME}"
OFFICIAL_DIR = PROJECT_ROOT / OFFICIAL_RELATIVE
