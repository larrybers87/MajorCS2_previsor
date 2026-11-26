"""Spike do scraper: busca UMA página do HLTV por execução, com orçamento rígido.

Usa o cliente HTTP do pacote ``hltv-crawler`` 0.1.0 (código auditado, carregado de
uma pasta externa, sem instalar) envolvido por uma guarda que:

- limita a ``MAX_REQUESTS`` requisições no total, somando todas as execuções
  (livro-caixa em disco, gravado ANTES de cada chamada);
- espera >= ``MIN_INTERVAL`` segundos desde o fim da requisição anterior;
- não segue redirecionamentos e não faz retry;
- salva corpo bruto, status e cabeçalhos;
- para em qualquer anomalia e, depois disso, recusa novas requisições.

Não serve para coleta em massa. Uso (no ambiente isolado)::

    python -I src/ingest/hltv_spike.py --package-dir <pasta do sdist extraído> \\
        --out data/raw/spike /results
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path

BASE_URL = "https://www.hltv.org"
ALLOWED_PREFIXES = ("/results", "/matches/", "/stats/matches/")
MAX_REQUESTS = 3
MIN_INTERVAL = 3.0  # o mínimo exigido é 2 s; folga deliberada
CHALLENGE_MARKERS = (
    b"<title>Just a moment",
    b"Attention Required! | Cloudflare",
    b"cf-chl-",
    b"challenge-error-text",
)


class SpikeStop(BaseException):
    """Interrompe o spike. Herda de ``BaseException`` para atravessar o
    ``except Exception`` do cliente do pacote, que faria retry."""


def validate_path(path: str) -> str:
    if (
        not path.startswith(ALLOWED_PREFIXES)
        or ".." in path
        or "\\" in path
        or "@" in path
        or any(c.isspace() for c in path)
    ):
        raise SpikeStop(f"caminho recusado: {path!r}")
    return path


def is_challenge(body: bytes, headers: dict[str, str]) -> bool:
    lowered = {k.lower(): v for k, v in headers.items()}
    return "cf-mitigated" in lowered or any(marker in body for marker in CHALLENGE_MARKERS)


class RequestGuard:
    """Substitui ``session.get`` impondo orçamento, intervalo e registro."""

    def __init__(
        self,
        real_get: Callable,
        out_dir: Path,
        max_requests: int = MAX_REQUESTS,
        min_interval: float = MIN_INTERVAL,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._real_get = real_get
        self._out = out_dir
        self._max = max_requests
        self._interval = min_interval
        self._clock = clock
        self._sleep = sleep
        self._ledger_path = out_dir / "ledger.json"

    def ledger(self) -> list[dict]:
        if not self._ledger_path.exists():
            return []
        return json.loads(self._ledger_path.read_text(encoding="utf-8"))

    def _write(self, entries: list[dict]) -> None:
        self._out.mkdir(parents=True, exist_ok=True)
        self._ledger_path.write_text(
            json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def __call__(self, url: str, **kwargs):
        if not url.startswith(BASE_URL + "/"):
            raise SpikeStop(f"host não permitido: {url!r}")
        validate_path(url[len(BASE_URL) :])
        entries = self.ledger()
        if any(not e.get("ok") for e in entries):
            raise SpikeStop("uma requisição anterior falhou; spike encerrado")
        if len(entries) >= self._max:
            raise SpikeStop(f"orçamento de {self._max} requisições esgotado")
        if entries:
            wait = entries[-1]["finished"] + self._interval - self._clock()
            if wait > 0:
                self._sleep(wait)

        number = len(entries) + 1
        entry = {"n": number, "url": url, "started": self._clock(), "ok": False}
        entry["finished"] = entry["started"]
        entries.append(entry)
        self._write(entries)

        kwargs["allow_redirects"] = False
        try:
            response = self._real_get(url, **kwargs)
        except Exception as exc:
            entry.update(finished=self._clock(), error=f"{type(exc).__name__}: {exc}")
            self._write(entries)
            raise SpikeStop(entry["error"]) from exc

        body = response.content
        headers = dict(response.headers)
        (self._out / f"response_{number}.html").write_bytes(body)
        (self._out / f"response_{number}.headers.json").write_text(
            json.dumps(headers, indent=2), encoding="utf-8"
        )
        challenge = is_challenge(body, headers)
        entry.update(
            finished=self._clock(),
            status=response.status_code,
            bytes=len(body),
            challenge=challenge,
            ok=response.status_code == 200 and not challenge,
        )
        self._write(entries)
        if not entry["ok"]:
            raise SpikeStop(
                f"resposta anômala: status={response.status_code}, desafio={challenge}"
            )
        return response


def _load_package(package_dir: Path):
    """Importa o código auditado sem instalar. Acrescentado ao FIM do ``sys.path``."""
    sys.path.append(str(package_dir))
    import parser as hltv_parser  # noqa: PLC0415 (pacote de topo do hltv-crawler)

    import scraper.http_client as http_client  # noqa: PLC0415

    for module in (hltv_parser, http_client):
        if not Path(module.__file__).resolve().is_relative_to(package_dir.resolve()):
            raise SpikeStop(f"módulo carregado de local inesperado: {module.__file__}")
    return http_client, hltv_parser


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    cli.add_argument("path", help="caminho no HLTV, ex.: /results")
    cli.add_argument("--package-dir", type=Path, required=True)
    cli.add_argument("--out", type=Path, default=Path("data/raw/spike"))
    args = cli.parse_args(argv)
    # O Git Bash converte argumentos iniciados por "/"; aceita-se o caminho sem a barra.
    path = args.path if args.path.startswith("/") else "/" + args.path

    out = args.out.resolve()
    try:
        validate_path(path)
        http_client, hltv_parser = _load_package(args.package_dir)
        # Os nomes são copiados no import: é preciso alterar o módulo http_client.
        http_client.CACHE_DIR = out / "cache"
        http_client.MAX_RETRIES = 1
        client = http_client.HltvHttpClient()
        guard = RequestGuard(client._session.get, out)
        client._session.get = guard
        html = client.get(path)
    except (SpikeStop, RuntimeError) as exc:
        print(f"PAROU: {exc}")
        return 1

    if path.startswith("/results"):
        parsed = hltv_parser.parse_results_page(html)
    elif path.startswith("/matches/"):
        parsed = hltv_parser.parse_match_detail(html)
    else:
        parsed = None  # o pacote não tem parser para /stats/
    used = len(guard.ledger())
    print(f"OK: {len(html)} caracteres; requisições usadas: {used}/{MAX_REQUESTS}")
    if parsed is not None:
        name = f"parsed_{used}.json"
        (out / name).write_text(
            json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"campos extraídos salvos em {out / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
