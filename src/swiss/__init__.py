"""Engine da fase suíça (regras do rulebook, ver ``docs/regras_suica.md``)."""

from .engine import (
    NoValidPairingError,
    Pairing,
    PairingMismatch,
    advancing_teams,
    announce_pairings,
    apply_results,
    buchholz,
    check_pairings,
    current_round,
    pair_round,
    records,
    standings,
)
from .probability import ProbFn, seed_strength_prob_fn, series_probability
from .rules import best_of, is_decider_match
from .simulate import SimulationResult, simulate_stage
from .state import Match, StageState, Team

__all__ = [
    "Match",
    "NoValidPairingError",
    "Pairing",
    "PairingMismatch",
    "ProbFn",
    "SimulationResult",
    "StageState",
    "Team",
    "advancing_teams",
    "announce_pairings",
    "apply_results",
    "best_of",
    "buchholz",
    "check_pairings",
    "current_round",
    "is_decider_match",
    "pair_round",
    "records",
    "seed_strength_prob_fn",
    "series_probability",
    "simulate_stage",
    "standings",
]
