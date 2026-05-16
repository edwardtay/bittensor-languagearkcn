import pytest

from languageark.speaker_dao import SpeakerDAO


def test_register_speaker_needs_min_stake(tmp_path):
    dao = SpeakerDAO(tmp_path / "dao.json")
    with pytest.raises(ValueError, match="Min stake"):
        dao.register_speaker("sp1", "nan", stake_tao=10.0, attesters=["a1", "a2"])


def test_register_speaker_needs_two_attesters(tmp_path):
    dao = SpeakerDAO(tmp_path / "dao.json")
    with pytest.raises(ValueError, match="at least 2"):
        dao.register_speaker("sp1", "nan", stake_tao=100.0, attesters=["a1"])
    with pytest.raises(ValueError, match="at least 2"):
        # duplicates collapse — still <2 distinct
        dao.register_speaker("sp1", "nan", stake_tao=100.0, attesters=["a1", "a1"])


def test_register_and_check(tmp_path):
    dao = SpeakerDAO(tmp_path / "dao.json")
    dao.register_speaker("sp1", "nan", stake_tao=100.0, attesters=["a1", "a2"])
    assert dao.is_registered("sp1", "nan")
    assert not dao.is_registered("sp1", "yue")
    assert not dao.is_registered("sp2", "nan")


def test_unregistered_speaker_cannot_vote(tmp_path):
    dao = SpeakerDAO(tmp_path / "dao.json")
    with pytest.raises(PermissionError):
        dao.record_vote("ghost", miner_a_uid=0, miner_b_uid=1, winner_uid=0, lang="nan")


def test_vote_updates_ratings(tmp_path):
    dao = SpeakerDAO(tmp_path / "dao.json")
    dao.register_speaker("sp1", "nan", stake_tao=100.0, attesters=["a1", "a2"])
    base_elo = dao.elo(0, "nan")
    dao.record_vote("sp1", miner_a_uid=0, miner_b_uid=1, winner_uid=0, lang="nan")
    assert dao.elo(0, "nan") > base_elo
    assert dao.elo(1, "nan") < base_elo


def test_save_and_reload(tmp_path):
    path = tmp_path / "dao.json"
    dao = SpeakerDAO(path)
    dao.register_speaker("sp1", "nan", stake_tao=100.0, attesters=["a1", "a2"])
    dao.record_vote("sp1", 0, 1, winner_uid=0, lang="nan")
    elo0 = dao.elo(0, "nan")
    dao.save()

    reloaded = SpeakerDAO(path)
    assert reloaded.is_registered("sp1", "nan")
    assert reloaded.elo(0, "nan") == elo0
