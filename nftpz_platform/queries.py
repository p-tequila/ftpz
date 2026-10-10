"""Allowlisted predicates evaluated at the owner gateway; never arbitrary SQL/code."""
from dataclasses import asdict, dataclass
import math


@dataclass(frozen=True)
class Query:
    field: str
    comparison: str
    value: float

    def validate(self, fields):
        if self.field not in fields or self.comparison not in {"ge", "le", "eq"}:
            raise ValueError("query outside approved schema/operator allowlist")
        if not isinstance(self.value, (int, float)) or not math.isfinite(self.value):
            raise ValueError("finite numeric predicate required")

    def to_dict(self):
        return asdict(self)


def owner_count(table, indices, query):
    query.validate(table.features)
    values = table.X[indices, table.features.index(query.field)]
    if query.comparison == "ge":
        matches = values >= query.value
    elif query.comparison == "le":
        matches = values <= query.value
    else:
        matches = values == query.value
    return int(matches.sum())
