"""Servidor local do site, com o modo Simulador.

Uso::

    python -m sim.site_server [--port 8000]    # abrir http://127.0.0.1:8000

Escuta só em 127.0.0.1 e serve apenas a página e os dados gerados. A cada recarga os
dados são refeitos a partir dos CSVs. No Simulador o navegador envia os vencedores
escolhidos e recebe a chave calculada aqui, pela engine; nada é gravado em disco.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ingest.seeds import SEEDS_PATH, load_seeds
from ingest.vrs import PROJECT_ROOT

from .common import MANUAL_DIR
from .export_site import PROCESSED_DIR, STAGE2_CSV, build, write_site_data
from .format_config import DEFAULT_FORMAT
from .live import Pick, apply_picks, official_model, stage_view
from .official import OFFICIAL_DIR
from .results import build_state, read_results
from .stages import entrants_by_seed, stage2_names

APP_PAGE = PROJECT_ROOT / "app" / "index.html"
STAGE1_CSV = MANUAL_DIR / "stage1_results.csv"
MAX_BODY = 64 * 1024
MAX_PICKS = 66


def parse_request(body: dict) -> tuple[int, list[Pick], bool]:
    """Valida o pedido do Simulador: ``stage``, ``picks`` e ``do_zero``."""
    if not isinstance(body, dict):
        raise ValueError("pedido inválido")
    stage = body.get("stage")
    if stage not in (1, 2):
        raise ValueError("o Simulador cobre os Stages 1 e 2")
    raw = body.get("picks", [])
    if not isinstance(raw, list) or len(raw) > MAX_PICKS:
        raise ValueError("lista de escolhas inválida")
    picks = []
    for item in raw:
        try:
            pick = Pick(int(item["rodada"]), str(item["a"]), str(item["b"]),
                        str(item["vencedor"]))  # fmt: skip
        except (KeyError, TypeError, ValueError):
            raise ValueError("escolha incompleta ou inválida") from None
        picks.append(pick)
    return stage, picks, bool(body.get("do_zero", False))


def simulate(
    stage: int,
    picks: list[Pick],
    from_scratch: bool,
    stage1_path: Path = STAGE1_CSV,
    stage2_path: Path = STAGE2_CSV,
    seeds_path: Path = SEEDS_PATH,
    official_dir: Path = OFFICIAL_DIR,
) -> dict:
    """Chave de um stage com os resultados reais (ou do zero) mais as escolhas."""
    seeds = load_seeds(seeds_path)
    base = DEFAULT_FORMAT.stage_state(1, entrants_by_seed(seeds, 1))
    prob_fn = None
    if stage == 1:
        rows = read_results(stage1_path)
    else:
        stage1 = build_state(base, read_results(stage1_path))
        base = DEFAULT_FORMAT.stage_state(2, stage2_names(seeds, stage1))
        rows = read_results(stage2_path) if stage2_path.exists() else []
        prob_fn = official_model(seeds, official_dir).prob_fn
    if from_scratch:
        rows = []
    state, chosen, ignored = apply_picks(build_state(base, rows), picks)
    view = stage_view(state, rows, prob_fn, chosen)
    return view | {
        "ignoradas": [
            {"rodada": p.round, "a": p.team_a, "b": p.team_b, "vencedor": p.winner}
            for p in ignored
        ]
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "previsor"

    def _send(self, status: HTTPStatus, content: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def _error(self, status: HTTPStatus, message: str) -> None:
        payload = json.dumps({"erro": message}, ensure_ascii=False).encode()
        self._send(status, payload, "application/json")

    def _local_host(self) -> bool:
        """Recusa cabeçalho Host de outro nome (proteção contra DNS rebinding)."""
        port = self.server.server_address[1]
        return self.headers.get("Host") in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def do_GET(self) -> None:  # noqa: N802 (nome exigido pela biblioteca)
        if not self._local_host():
            return self._error(HTTPStatus.FORBIDDEN, "host não permitido")
        path = self.path.split("?", 1)[0]
        if path == "/":
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/app/index.html")
            self.end_headers()
        elif path == "/app/index.html":
            self._send(HTTPStatus.OK, APP_PAGE.read_bytes(), "text/html")
        elif path == "/data/processed/site_data.js":
            self._send_data()
        else:
            self._error(HTTPStatus.NOT_FOUND, "não encontrado")

    def _send_data(self) -> None:
        try:
            target = write_site_data(build(STAGE1_CSV), PROCESSED_DIR)
        except (FileNotFoundError, ValueError, subprocess.CalledProcessError) as exc:
            # Mostra o erro na página em vez de servir dados velhos sem avisar.
            message = json.dumps(str(exc), ensure_ascii=False)
            script = f"window.SITE_ERROR = {message};\n".encode()
            return self._send(HTTPStatus.OK, script, "text/javascript")
        self._send(HTTPStatus.OK, target.read_bytes(), "text/javascript")

    def do_POST(self) -> None:  # noqa: N802
        if not self._local_host():
            return self._error(HTTPStatus.FORBIDDEN, "host não permitido")
        if self.path != "/api/simulate":
            return self._error(HTTPStatus.NOT_FOUND, "não encontrado")
        # Exigir JSON impede envios de formulários de outras páginas sem preflight.
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            return self._error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "envie JSON")
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_BODY:
                raise ValueError("tamanho do pedido inválido")
            view = simulate(*parse_request(json.loads(self.rfile.read(length))))
        except (FileNotFoundError, ValueError) as exc:
            return self._error(HTTPStatus.BAD_REQUEST, str(exc))
        payload = json.dumps(view, ensure_ascii=False, allow_nan=False).encode()
        self._send(HTTPStatus.OK, payload, "application/json")


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="Servidor local do site")
    cli.add_argument("--port", type=int, default=8000)
    args = cli.parse_args(argv)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError as exc:
        print(f"ERRO: não foi possível abrir a porta {args.port}: {exc}")
        return 1
    print(f"Site em http://127.0.0.1:{args.port} (Ctrl+C para parar)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
