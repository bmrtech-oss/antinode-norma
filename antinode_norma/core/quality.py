from typing import List, Union
from .schemas import UserStory, QualityReport

VAGUE_WORDS = {"etc", "various", "handle", "properly", "many", "some", "multiple"}
IMPL_WORDS = {"sql", "database", "rest", "api", "class", "method"}
SYSTEM_WORDS = {"call", "update", "insert", "delete", "compute"}
TEST_VERBS = {"should", "must", "returns", "displays", "sends"}


def is_independent(story: UserStory) -> bool:
    deps = story.dependencies or []
    return len(deps) <= 2


def is_negotiable(story: UserStory) -> Union[bool, str]:
    for crit in story.acceptance_criteria:
        if any(word in crit.lower() for word in IMPL_WORDS):
            return "needs_review"
    return True


def is_valuable(story: UserStory) -> bool:
    return not any(word in story.benefit.lower() for word in SYSTEM_WORDS)


def is_estimable(story: UserStory) -> bool:
    for crit in story.acceptance_criteria:
        if any(word in crit.lower() for word in VAGUE_WORDS):
            return False
    return True


def is_small(story: UserStory) -> bool:
    if story.estimated_points is not None:
        return story.estimated_points <= 8
    return len(story.acceptance_criteria) <= 5


def is_testable(story: UserStory) -> bool:
    for crit in story.acceptance_criteria:
        if not any(verb in crit.lower() for verb in TEST_VERBS):
            return False
    return True


def _suggestion_for(criterion: str) -> str:
    suggestions = {
        "independent": "Remove or document dependencies. Split story.",
        "negotiable": "Replace implementation details with user‑visible outcomes.",
        "valuable": "Rewrite benefit to focus on user value.",
        "estimable": "Remove vague words like 'various', 'handle'.",
        "small": "Split into smaller parts or reduce acceptance criteria to ≤5.",
        "testable": "Make each criterion a clear assertion (e.g., 'system returns X').",
    }
    return suggestions.get(criterion, "Review this aspect.")


def compute_quality(story: UserStory) -> QualityReport:
    invest = {
        "independent": is_independent(story),
        "negotiable": is_negotiable(story),
        "valuable": is_valuable(story),
        "estimable": is_estimable(story),
        "small": is_small(story),
        "testable": is_testable(story),
    }
    passes = all(v is True for v in invest.values() if isinstance(v, bool))
    issues = []
    suggestions = []
    for k, v in invest.items():
        if v is False:
            issues.append(f"Fails '{k}': {_suggestion_for(k)}")
            suggestions.append(_suggestion_for(k))
        elif v == "needs_review":
            issues.append(f"'{k}' needs review – implementation details present")
            suggestions.append(_suggestion_for(k))

    numeric = [1 if x is True else 0 if x is False else 0.5 for x in invest.values()]
    score = sum(numeric) / len(numeric)

    return QualityReport(
        passes_invest=passes,
        invest_details=invest,
        issues=issues,
        suggestions=suggestions,
        quality_score=score,
        improved_story=None,
    )
