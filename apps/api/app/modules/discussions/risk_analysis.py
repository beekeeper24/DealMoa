import re
from dataclasses import dataclass
from typing import Literal

ModerationRiskLevel = Literal["low", "medium", "high"]

EXTERNAL_CONTACT_PATTERN = re.compile(
    r"(카톡|카카오톡|오픈채팅|텔레그램|telegram|010[- ]?\d{4}[- ]?\d{4})",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)
BLOCKED_COMMERCIAL_SPAM_TERMS = ("무료바카라", "사설토토", "비밀링크")


@dataclass(frozen=True)
class DiscussionRiskAnalysis:
    score: int
    level: ModerationRiskLevel
    reasons: list[str]


def analyze_discussion_risk(body: str) -> DiscussionRiskAnalysis:
    reasons: list[str] = []
    normalized = body.lower()

    if EXTERNAL_CONTACT_PATTERN.search(body):
        reasons.append("external_contact")
    if len(URL_PATTERN.findall(body)) >= 2:
        reasons.append("repeated_url")
    if any(term in normalized for term in BLOCKED_COMMERCIAL_SPAM_TERMS):
        reasons.append("blocked_commercial_spam")

    if "blocked_commercial_spam" in reasons or "external_contact" in reasons:
        return DiscussionRiskAnalysis(score=100, level="high", reasons=reasons)
    if reasons:
        return DiscussionRiskAnalysis(score=50, level="medium", reasons=reasons)
    return DiscussionRiskAnalysis(score=0, level="low", reasons=[])
