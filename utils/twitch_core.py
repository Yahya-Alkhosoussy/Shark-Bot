from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class TwitchUser:
    display: str
    login: str
    id: str

@dataclass
class TwitchBan:
    user: TwitchUser
    reason: str
    mod_responsible: TwitchUser
    time_banned: datetime
    duration: float | timedelta | None = None

    def __post_init__(self):
        if isinstance(self.duration, timedelta):
            self.duration = self.duration.total_seconds() if self.duration else None

@dataclass
class TwitchWarning:
    "Rules cited is different to the raw rules"
    user: TwitchUser
    mod: TwitchUser
    reason: str | None
    rules: list[str] | None
    time_of_warning: datetime

    def __post_init__(self):
        if self.rules is None:
            self.rules_cited = "No Rules Cited"

        if isinstance(self.rules, list):
            for rule in self.rules:
                self.rules_cited += rule + "\n"
