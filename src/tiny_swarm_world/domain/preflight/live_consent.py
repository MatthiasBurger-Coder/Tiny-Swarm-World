from __future__ import annotations

from dataclasses import dataclass


LIVE_CONSENT_ENVIRONMENT_VARIABLE = "TSW_LIVE_INFRASTRUCTURE_CONSENT"
LIVE_CONSENT_ENVIRONMENT_VALUE = "I_UNDERSTAND_THIS_CHANGES_LOCAL_INFRASTRUCTURE"
LIVE_CONSENT_PHRASE = "RUN TINY SWARM WORLD LIVE INSTALLATION"


@dataclass(frozen=True)
class LiveConsent:
    live_flag: bool
    environment_value: str | None
    typed_phrase: str | None

    @property
    def accepted(self) -> bool:
        return (
            self.live_flag
            and self.environment_value == LIVE_CONSENT_ENVIRONMENT_VALUE
            and self.typed_phrase == LIVE_CONSENT_PHRASE
        )

    @property
    def missing_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.live_flag:
            reasons.append("missing --live")
        if self.environment_value != LIVE_CONSENT_ENVIRONMENT_VALUE:
            reasons.append(f"missing {LIVE_CONSENT_ENVIRONMENT_VARIABLE}")
        if self.typed_phrase != LIVE_CONSENT_PHRASE:
            reasons.append("missing typed live confirmation phrase")
        return tuple(reasons)
