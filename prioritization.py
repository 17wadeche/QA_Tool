SEVERE_SIGNAL_FLAGS = {
    "death_keyword_present",
    "serious_injury_keyword_present",
    "fire_keyword_present",
}
SEVERE_DECISION_FLAGS = {
    "coding_regulatory_decision_rule_flag",
    "coding_regulatory_decision_missing_flag",
    "investigation_required_mismatch",
}
def layer3_prioritization(layer1_result, layer2_result):
    score = layer1_result.get("layer1_score", 0)
    layer1_flags = set(layer1_result.get("layer1_flags", []))
    reasons = []
    if layer1_flags:
        reasons.append("Layer 1 flags present")
    inconsistency_fields = [
        "coding_event_description_inconsistency",
        "coding_regulatory_decision_inconsistency",
        "coding_investigation_decision_inconsistency",
    ]
    inconsistency_count = sum(
        str(layer2_result.get(field, "")).strip().lower() == "yes"
        for field in inconsistency_fields
    )
    if inconsistency_count:
        score += inconsistency_count * 2
        reasons.append(f"{inconsistency_count} Layer 2 inconsistency checks flagged")
    concern_level = str(layer2_result.get("concern_level", "")).strip().lower()
    concern_points = {"high": 4, "medium": 2, "low": 1}.get(concern_level, 0)
    score += concern_points
    if concern_points:
        reasons.append(f"Layer 2 concern level = {concern_level.title()}")
    severe_decision_conflict = bool(layer1_flags & SEVERE_SIGNAL_FLAGS) and bool(
        layer1_flags & SEVERE_DECISION_FLAGS
    )
    multiple_material_inconsistencies = inconsistency_count >= 2 and concern_level == "high"
    if severe_decision_conflict or multiple_material_inconsistencies:
        tier = 1
    elif inconsistency_count >= 1 or concern_level in {"medium", "high"} or score >= 5:
        tier = 2
    elif score >= 2:
        tier = 3
    else:
        tier = 4
    return {
        "priority_tier": tier,
        "priority_score": score,
        "priority_reasons": reasons,
    }