from typing import List, Dict
from antinode_norma.core.types import GateResult, Verdict


def aggregate_results(gate_results: List[GateResult], hard_gate_ids: Dict[str, bool] = None) -> Verdict:
    """Aggregate individual GateResult outcomes into a final Verdict instance."""
    if hard_gate_ids is None:
        hard_gate_ids = {"Q0": True, "Q1": True, "Q2": True, "Q3": True, "Q4": True, "Q5": True}

    gate_map: Dict[str, GateResult] = {g.gate_id: g for g in gate_results}

    hard_pass = True
    soft_scores: List[float] = []
    sem_scores: List[float] = []

    for res in gate_results:
        is_hard = hard_gate_ids.get(res.gate_id, False)
        if is_hard and not res.passed:
            hard_pass = False

        if not is_hard:
            if res.gate_id == "Q10":
                sem_scores.append(res.score)
            else:
                soft_scores.append(res.score)

    soft_score = (sum(soft_scores) / len(soft_scores)) if soft_scores else 1.0
    sem_score = (sum(sem_scores) / len(sem_scores)) if sem_scores else 1.0

    summary = "PASS" if (hard_pass and soft_score >= 0.85 and sem_score >= 0.85) else "FAIL"

    return Verdict(
        hard_pass=hard_pass,
        soft_score=soft_score,
        sem_score=sem_score,
        gate_results=gate_map,
        summary=summary,
    )
