"""Guarda de requisições do spike, testada sem rede."""

import pytest

from ingest.hltv_spike import BASE_URL, RequestGuard, SpikeStop, validate_path


class FakeResponse:
    def __init__(self, status=200, body=b"<html>ok</html>", headers=None):
        self.status_code = status
        self.content = body
        self.headers = headers or {}


class FakeTime:
    def __init__(self):
        self.now = 1000.0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def make_guard(tmp_path, responses, fake=None):
    fake = fake or FakeTime()
    calls = []

    def real_get(url, **kwargs):
        calls.append((url, kwargs, fake.now))
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        fake.now += 0.5  # duração da resposta
        return item

    guard = RequestGuard(real_get, tmp_path, min_interval=2.0, clock=fake.clock, sleep=fake.sleep)
    return guard, calls, fake


def test_budget_is_three_requests_across_instances(tmp_path):
    guard, calls, fake = make_guard(tmp_path, [FakeResponse() for _ in range(3)])
    for i in range(3):
        guard(f"{BASE_URL}/matches/{i}/x")
    with pytest.raises(SpikeStop, match="orçamento"):
        guard(f"{BASE_URL}/results")
    # Nova execução lê o mesmo livro-caixa e também recusa.
    again, new_calls, _ = make_guard(tmp_path, [FakeResponse()], fake)
    with pytest.raises(SpikeStop, match="orçamento"):
        again(f"{BASE_URL}/results")
    assert len(calls) == 3
    assert new_calls == []


def test_interval_counts_from_end_of_previous_response(tmp_path):
    guard, calls, _ = make_guard(tmp_path, [FakeResponse(), FakeResponse()])
    guard(f"{BASE_URL}/results")
    guard(f"{BASE_URL}/results?offset=100")
    first_end = calls[0][2] + 0.5
    assert calls[1][2] - first_end >= 2.0


def test_redirects_disabled_and_raw_body_saved(tmp_path):
    guard, calls, _ = make_guard(tmp_path, [FakeResponse(body=b"a\r\nb")])
    guard(f"{BASE_URL}/results", allow_redirects=True)
    assert calls[0][1]["allow_redirects"] is False
    assert (tmp_path / "response_1.html").read_bytes() == b"a\r\nb"


@pytest.mark.parametrize(
    "response",
    [
        FakeResponse(status=403),
        FakeResponse(status=302),
        FakeResponse(body=b"<title>Just a moment...</title>"),
        FakeResponse(headers={"CF-Mitigated": "challenge"}),
        ConnectionError("sem rede"),
    ],
)
def test_any_anomaly_stops_and_blocks_further_requests(tmp_path, response):
    guard, calls, _ = make_guard(tmp_path, [response, FakeResponse()])
    with pytest.raises(SpikeStop):
        guard(f"{BASE_URL}/results")
    with pytest.raises(SpikeStop, match="anterior falhou"):
        guard(f"{BASE_URL}/results")
    assert len(calls) == 1


def test_stop_is_not_caught_by_except_exception():
    assert not issubclass(SpikeStop, Exception)


@pytest.mark.parametrize(
    "path",
    ["/ranking/teams", "/matches/..\\x", "/matches/1/../../x", "@evil.example/matches/1/",
     "/matches/1/a b"],
)  # fmt: skip
def test_unsafe_paths_are_rejected(path):
    with pytest.raises(SpikeStop):
        validate_path(path)


def test_other_hosts_are_rejected(tmp_path):
    guard, calls, _ = make_guard(tmp_path, [FakeResponse()])
    with pytest.raises(SpikeStop, match="host"):
        guard("https://www.hltv.org.evil.example/results")
    assert calls == []
