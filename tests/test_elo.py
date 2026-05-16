from languageark.elo import INITIAL_RATING, Match, Rating, update_rating


def test_new_rating_baseline():
    r = Rating()
    assert r.rating == INITIAL_RATING
    assert r.rd == 350.0


def test_winning_against_equal_increases_rating():
    r = Rating()
    matches = [Match(opponent_rating=1500.0, opponent_rd=200.0, outcome=1.0)]
    new = update_rating(r, matches)
    assert new.rating > r.rating
    assert new.rd < r.rd  # uncertainty decreases


def test_losing_against_equal_decreases_rating():
    r = Rating()
    matches = [Match(opponent_rating=1500.0, opponent_rd=200.0, outcome=0.0)]
    new = update_rating(r, matches)
    assert new.rating < r.rating


def test_inactivity_increases_uncertainty_but_not_rating():
    r = Rating(rating=1700.0, rd=100.0, volatility=0.06)
    new = update_rating(r, matches=[])
    assert new.rating == 1700.0
    assert new.rd > 100.0


def test_draw_against_higher_increases_rating():
    r = Rating()
    matches = [Match(opponent_rating=1800.0, opponent_rd=100.0, outcome=0.5)]
    new = update_rating(r, matches)
    assert new.rating > r.rating  # drawing a stronger opponent is a positive signal


def test_pure_function_does_not_mutate():
    r = Rating(rating=1600.0, rd=200.0)
    snapshot = (r.rating, r.rd, r.volatility)
    _ = update_rating(r, [Match(1500.0, 200.0, 1.0)])
    assert (r.rating, r.rd, r.volatility) == snapshot
