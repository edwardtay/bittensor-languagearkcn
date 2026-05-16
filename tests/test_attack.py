from languageark.attack import Network, _ground_truth_at_tempo, _vtrust, simulate


def test_ground_truth_weights_sum_positive():
    w = _ground_truth_at_tempo(0)
    assert sum(w.values()) > 0
    assert len(w) == 5


def test_ground_truth_changes_over_time():
    w0 = _ground_truth_at_tempo(0)
    w5 = _ground_truth_at_tempo(5)
    assert w0 != w5, "ranking should drift to model real subnet churn"


def test_vulnerable_network_freeloader_steals_100pct():
    n = Network(name="A", commit_reveal_period=0)
    simulate(n, n_tempos=10)
    vt = _vtrust(n)
    assert sum(vt) / len(vt) > 0.95, "freeloader must capture nearly all honest dividends"


def test_languageark_commit_reveal_defeats_freeloader():
    n = Network(name="B", commit_reveal_period=5)
    simulate(n, n_tempos=10)
    vt = _vtrust(n)
    mean = sum(vt) / len(vt)
    assert mean < 0.6, f"commit_reveal_period=5 should cut freeloader to <60% dividends, got {mean:.2f}"


def test_simulate_pure_no_external_state():
    n = Network(name="X", commit_reveal_period=5)
    simulate(n, n_tempos=4)
    assert len(n.honest_weights) == 4
    assert len(n.freeloader_weights) == 4
