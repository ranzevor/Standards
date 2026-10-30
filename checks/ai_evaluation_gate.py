"""Synthetic evidence gate, not a model benchmark or project release approval."""
import sys
if sys.flags.optimize: raise RuntimeError("Validation requires assertions enabled; do not use -O or -OO")
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Evidence:
    planned: int
    success: int
    failed: int = 0
    unresolved: int = 0
    not_run: int = 0
    critical_violations: int = 0
    judge_valid: bool = False
    required_layers_complete: bool = False


def decide(evidence):
    """Conservative all-success demonstration; project quality thresholds differ."""
    if not isinstance(evidence, Evidence):
        raise ValueError('expected Evidence')
    counts = (evidence.planned, evidence.success, evidence.failed,
              evidence.unresolved, evidence.not_run, evidence.critical_violations)
    if any(type(x) is not int or x < 0 for x in counts):
        raise ValueError('counts must be nonnegative integers, not bools')
    if evidence.planned <= 0:
        raise ValueError('empty evidence cannot establish success')
    if sum(counts[1:5]) != evidence.planned:
        raise ValueError('all planned trials must be accounted for')
    if evidence.critical_violations > evidence.planned - evidence.not_run:
        raise ValueError('violations cannot exceed executed trials')
    if type(evidence.judge_valid) is not bool or type(evidence.required_layers_complete) is not bool:
        raise ValueError('evidence flags must be bools')
    if evidence.critical_violations or evidence.failed:
        return 'FAIL'
    if evidence.unresolved or evidence.not_run or not evidence.judge_valid or not evidence.required_layers_complete:
        return 'INSUFFICIENT'
    return 'PASS'


def raw_success_fraction(evidence):
    """Unverified input success labels / planned trials; NOT validated task success.

    Critical-violation overlap may make these labels inconsistent. Use decide
    for this synthetic gate; real task success requires per-case reconciliation."""
    decide(evidence)
    return evidence.success / evidence.planned


def zero_failure_upper(n, alpha=0.05):
    """One-sided exact upper bound ONLY for n independent Bernoulli trials.

    Caller must establish assumptions; repeats/variants need not be independent.
    This mathematical helper cannot validate the experimental sampling design.
    """
    if type(n) is not int or n <= 0:
        raise ValueError('positive integer independent sample count required')
    if type(alpha) not in (int, float) or not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError('alpha must be finite and strictly between zero and one')
    return -math.expm1(math.log(alpha) / n)
