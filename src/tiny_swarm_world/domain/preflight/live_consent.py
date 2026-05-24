from __future__ import annotations

from dataclasses import dataclass


LIVE_CONSENT_ENVIRONMENT_VARIABLE = "TSW_LIVE_INFRASTRUCTURE_CONSENT"
LIVE_CONSENT_ENVIRONMENT_VALUE = "I_UNDERSTAND_THIS_CHANGES_LOCAL_INFRASTRUCTURE"
LIVE_CONSENT_PHRASE = "RUN TINY SWARM WORLD LIVE INSTALLATION"
LIVE_CONSENT_PROMPT = "Live setup can change local infrastructure. Continue? [y/N]:"
LIVE_CONSENT_YES_VALUES = frozenset({"y", "yes", "j", "ja"})


@dataclass(frozen=True)
class LiveConsent:
    live_flag: bool
    confirmed: bool = False
    environment_value: str | None = None
    typed_phrase: str | None = None

    @property
    def accepted(self) -> bool:
        return self.live_flag and (self.confirmed or self._legacy_consent_accepted)

    @property
    def missing_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.live_flag:
            reasons.append("missing --live")
        elif not self.confirmed and not self._legacy_consent_accepted:
            reasons.append("missing live confirmation")
        return tuple(reasons)

    @property
    def _legacy_consent_accepted(self) -> bool:
        return (
            self.environment_value == LIVE_CONSENT_ENVIRONMENT_VALUE
            and self.typed_phrase == LIVE_CONSENT_PHRASE
        )
