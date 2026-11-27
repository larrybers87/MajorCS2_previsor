"""Diagnóstico de calibração por faixas (dados sintéticos)."""

import numpy as np
from test_b1 import synthetic

from backtest.b0_calibration import rated_matches
from backtest.calibration_diagnostic import MAIN, band_table, predictions, render


def test_bands_use_the_favourite_and_count_every_match_once():
    p = np.array([0.55, 0.45, 0.65, 0.2, 0.81, 0.99])
    won = np.array([True, False, False, False, True, False])
    rows = band_table(p, won, np.arange(6), np.random.default_rng(0))
    assert [r["faixa"] for r in rows] == ["50-60%", "60-70%", "70-80%", "80%+"]
    assert [r["n"] for r in rows] == [2, 1, 0, 3]
    assert rows[0]["observado"] == 1.0  # nos dois casos o favorito venceu
    assert rows[3]["observado"] == 2 / 3  # 0,2 -> favorito é o outro lado, que venceu
    assert rows[3]["previsto"] == np.mean([0.8, 0.81, 0.99])
    assert rows[3]["diferenca"] < 0 and "wilson" not in rows[2]


def test_main_model_is_the_mean_and_report_renders():
    data = rated_matches(synthetic())
    models, test, _ = predictions(data)
    np.testing.assert_allclose(models[MAIN][test], (models["w=0"] + models["w=1"])[test] / 2)
    assert not np.isnan(models[MAIN][test]).any()
    report = render(data)
    assert "Só diagnóstico" in report and report.count("| 80%+ |") == 3
