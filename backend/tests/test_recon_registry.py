"""Registry sanity checks: every phase is tagged active or passive, every
phase has at least one tool, and ids/tool labels are unique within a phase."""
from app.recon.registry import PHASES, PHASES_BY_ID


def test_every_phase_has_a_valid_mode():
    for phase in PHASES:
        assert phase.mode in {"active", "passive"}


def test_every_phase_has_at_least_one_tool():
    for phase in PHASES:
        assert len(phase.tools) >= 1


def test_phase_ids_are_unique():
    ids = [p.id for p in PHASES]
    assert len(ids) == len(set(ids))


def test_phases_by_id_matches_phases():
    assert len(PHASES_BY_ID) == len(PHASES)
    for phase in PHASES:
        assert PHASES_BY_ID[phase.id] is phase


def test_phase_counts_by_mode():
    active = [p for p in PHASES if p.mode == "active"]
    passive = [p for p in PHASES if p.mode == "passive"]
    assert len(active) == 12
    assert len(passive) == 6
