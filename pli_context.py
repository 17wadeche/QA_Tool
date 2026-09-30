import re
def _text(value):
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text
def is_no_allegation_code(value):
    normalized = re.sub(r"[^a-z0-9]+", " ", _text(value).lower()).strip()
    return bool(re.search(r"\bno(?:\s+[a-z0-9]+){0,3}\s+allegation\b", normalized))
def _has_substantive_code(pli):
    rfr_code = _text(pli.get("RFR Code"))
    if rfr_code:
        return not is_no_allegation_code(rfr_code)
    fdp_code = _text(pli.get("FDP Code"))
    return bool(fdp_code) and not is_no_allegation_code(fdp_code)
def reconcile_layer2_with_pli_context(layer2_result, row_dict, related_plis=None):
    reconciled = dict(layer2_result)
    event_flag = _text(
        reconciled.get("coding_event_description_inconsistency")
    ).lower() == "yes"
    current_codes = [row_dict.get("RFR Code"), row_dict.get("FDP Code")]
    current_has_no_allegation = any(is_no_allegation_code(code) for code in current_codes)
    sibling_has_allegation_coding = any(
        not pli.get("isCurrentPli") and _has_substantive_code(pli)
        for pli in (related_plis or [])
    )
    if not (event_flag and current_has_no_allegation and sibling_has_allegation_coding):
        return reconciled
    reconciled["coding_event_description_inconsistency"] = "No"
    reconciled["coding_event_description_reason"] = (
        "The event description concerns an allegation coded on a related PLI; "
        "the current PLI's no-allegation coding is not contradictory."
    )
    other_flags = [
        reconciled.get("coding_regulatory_decision_inconsistency"),
        reconciled.get("coding_investigation_decision_inconsistency"),
    ]
    if not any(_text(value).lower() == "yes" for value in other_flags):
        reconciled["layer2_flag"] = "No"
        reconciled["concern_level"] = "Low"
        reconciled["layer2_reason"] = (
            "No inconsistency remains after applying the related-PLI context."
        )
    return reconciled