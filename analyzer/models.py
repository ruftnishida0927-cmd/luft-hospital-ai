from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class Page:
    url: str
    final_url: str
    domain: str
    category: str
    title: str = ""
    text: str = ""
    html: str = ""
    content_type: str = ""
    status_code: int = 0
    fetched_at: str = ""
    depth: int = 0
    source_type: str = "official"  # official / public / recruit / group / unknown
    anchors: List[str] = field(default_factory=list)


@dataclass
class Evidence:
    field_name: str
    value: str
    source_url: str
    source_label: str
    category: str
    source_type: str
    confidence: float
    extracted_by: str
    comment: str = ""


@dataclass
class ResolvedField:
    field_name: str
    final_value: str
    evidences: List[Evidence] = field(default_factory=list)
    consistency: str = "不明"
    comment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "final_value": self.final_value,
            "consistency": self.consistency,
            "comment": self.comment,
            "evidences": [asdict(e) for e in self.evidences],
        }


@dataclass
class AnalysisResult:
    hospital_name: str
    canonical_url: str
    pages: List[Page] = field(default_factory=list)
    resolved: Dict[str, ResolvedField] = field(default_factory=dict)
    facility_basic_fee: List[ResolvedField] = field(default_factory=list)
    facility_addons: List[ResolvedField] = field(default_factory=list)
    recruit_fields: Dict[str, ResolvedField] = field(default_factory=dict)
    group_entities: List[ResolvedField] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hospital_name": self.hospital_name,
            "canonical_url": self.canonical_url,
            "pages": [asdict(p) for p in self.pages],
            "resolved": {k: v.to_dict() for k, v in self.resolved.items()},
            "facility_basic_fee": [x.to_dict() for x in self.facility_basic_fee],
            "facility_addons": [x.to_dict() for x in self.facility_addons],
            "recruit_fields": {k: v.to_dict() for k, v in self.recruit_fields.items()},
            "group_entities": [x.to_dict() for x in self.group_entities],
            "notes": self.notes,
        }
