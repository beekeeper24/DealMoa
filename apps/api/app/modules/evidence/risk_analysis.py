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
class VerifiedReviewRiskAnalysis:
    score: int
    level: ModerationRiskLevel
    reasons: list[str]


def analyze_verified_review_risk(
    *,
    body: str,
    title: str,
) -> VerifiedReviewRiskAnalysis:
    reasons: list[str] = []
    combined_text = f"{title}\n{body}"
    normalized = combined_text.lower()

    if EXTERNAL_CONTACT_PATTERN.search(combined_text):
        reasons.append("external_contact")
    if len(URL_PATTERN.findall(combined_text)) >= 2:
        reasons.append("repeated_url")
    if any(term in normalized for term in BLOCKED_COMMERCIAL_SPAM_TERMS):
        reasons.append("blocked_commercial_spam")

    if any(
        reason in reasons
        for reason in (
            "external_contact",
            "blocked_commercial_spam",
        )
    ):
        return VerifiedReviewRiskAnalysis(score=100, level="high", reasons=reasons)
    if reasons:
        return VerifiedReviewRiskAnalysis(score=50, level="medium", reasons=reasons)
    return VerifiedReviewRiskAnalysis(score=0, level="low", reasons=[])
