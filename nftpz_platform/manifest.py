"""Serializable experiment and silo contracts.

The manifest is deliberately storage-provider agnostic. Azure is one backend;
local directories are used for reproducible tests and CI.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SiloSpec:
    silo_id: str
    dataset: str
    location: str
    schema: str
    labels: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class JobSpec:
    job_id: str
    task: str
    silos: tuple[SiloSpec, ...]
    output_prefix: str = "outputs"
    privacy: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_file(cls, path: str | Path) -> "JobSpec":
        payload = json.loads(Path(path).read_text())
        payload["silos"] = tuple(SiloSpec(**item) for item in payload["silos"])
        return cls(**payload)
