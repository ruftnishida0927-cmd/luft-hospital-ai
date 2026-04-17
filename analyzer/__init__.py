from .crawl import crawl_site
from .extract import extract_evidences
from .models import AnalysisResult
from .report import build_summary
from .resolve import resolve_facility_lists, resolve_fields, resolve_group, resolve_recruit
from .sources import detect_missing_source_layers, summarize_sources


def analyze_hospital(start_url: str, hospital_name: str = "") -> AnalysisResult:
    pages = crawl_site(start_url)
    evidences = extract_evidences(pages)
    resolved = resolve_fields(evidences)
    facility_basic, facility_addons = resolve_facility_lists(evidences)
    recruit_fields = resolve_recruit(evidences)
    group_entities = resolve_group(evidences)

    if not hospital_name:
        hospital_name = _infer_hospital_name(pages) or "不明"

    result = AnalysisResult(
        hospital_name=hospital_name,
        canonical_url=start_url,
        pages=pages,
        resolved=resolved,
        facility_basic_fee=facility_basic,
        facility_addons=facility_addons,
        recruit_fields=recruit_fields,
        group_entities=group_entities,
        notes=detect_missing_source_layers(pages),
    )
    return result


def _infer_hospital_name(pages):
    for p in pages:
        for token in ["病院", "クリニック", "医院", "メディカルセンター", "センター"]:
            if token in p.title:
                return p.title.split("|")[0].split("｜")[0].strip()
    return ""
