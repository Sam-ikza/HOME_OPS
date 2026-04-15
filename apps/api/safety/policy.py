from __future__ import annotations

import re
from datetime import date, datetime, timezone

from config import settings
from schemas.diagnosis import DiagnosisResponse

HIGH_RISK_TERMS = {
    "gas",
    "gas leak",
    "lpg",
    "cng",
    "refrigerant",
    "coolant leak",
    "freon",
    "r32",
    "r410a",
    "r22",
    "high voltage",
    "mains voltage",
    "live wire",
    "electric shock",
    "electrocution",
    "shock",
    "240v",
    "415v",
    "wiring",
    "internal wiring",
    "capacitor",
    "inverter board",
    "control board",
    "pcb",
    "compressor",
    "sealed system",
    "breaker panel",
    "mcb",
    "rcb",
    "rcbo",
    "earthing",
    "ground fault",
    "short circuit",
    "electrical arc",
    "arc flash",
    "spark",
    "sparks",
    "smoke",
    "fire",
    "flame",
    "burning smell",
    "burnt smell",
    "burning plastic",
    "water near wiring",
}

SOFTWARE_LOCK_TERMS = {
    "smart fridge",
    "firmware lock",
    "oem diagnostics",
    "pairing lock",
    "samsung family hub",
    "bosch 800-series",
    "lg smartwash",
    "apple",
    "nest",
    "john deere",
}


def _is_high_risk(issue_text: str) -> bool:
    lowered = issue_text.lower()
    return any(_contains_term(lowered, term) for term in HIGH_RISK_TERMS)


def _contains_term(text: str, term: str) -> bool:
    escaped = re.escape(term.lower())
    if " " in term or "-" in term:
        pattern = escaped.replace(r"\ ", r"(?:\s+|-)").replace(r"\-", r"(?:\s+|-)")
        return re.search(rf"(?<!\w){pattern}(?!\w)", text) is not None
    return re.search(rf"\b{escaped}\b", text) is not None


def _software_lock_warning(model_text: str, issue_text: str) -> str | None:
    merged = f"{model_text} {issue_text}".lower()
    dynamic_terms = {
        term.strip().lower()
        for term in settings.software_lock_hints.split(",")
        if term.strip()
    }
    if any(term in merged for term in SOFTWARE_LOCK_TERMS.union(dynamic_terms)):
        return "Model may require OEM software tools. Check software lock status before disassembly."
    return None


def compute_warranty_active(purchase_date: date | None) -> bool:
    if purchase_date is None:
        return False
    delta_days = (datetime.now(timezone.utc).date() - purchase_date).days
    return delta_days <= settings.warranty_days


def enforce_business_rules(
    response: DiagnosisResponse,
    issue_text: str,
    warranty_active: bool,
    model_text: str,
) -> DiagnosisResponse:
    high_risk = _is_high_risk(issue_text)
    software_lock = _software_lock_warning(model_text, issue_text)

    if high_risk:
        response.danger_level = "HIGH"
        response.call_pro = True
        response.diy_steps = []
        response.escalation_message = settings.danger_escalation_text

    if warranty_active:
        response.warranty_active = True
        response.warranty_block_reason = "Appliance appears to be under active warranty window."
        response.call_pro = True
        response.diy_steps = []
        if not response.manufacturer_support:
            response.manufacturer_support = "Contact manufacturer support with serial/model for authorized service."
        response.escalation_message = response.manufacturer_support

    if software_lock and not response.software_lock_warning:
        response.software_lock_warning = software_lock

    if response.danger_level == "HIGH":
        response.call_pro = True
        response.diy_steps = []

    if response.warranty_active:
        response.diy_steps = []
        response.call_pro = True

    if not response.fragility_warning:
        response.fragility_warning = "Handle plastic clips, glass, and sensor connectors gently to avoid breakage."

    return response
