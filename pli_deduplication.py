import re
import pandas as pd
def _identifier(value):
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).strip()
    first_value = re.split(r"[,;|\n]+", text)[0].strip()
    if re.fullmatch(r"\d+\.0", first_value):
        first_value = first_value[:-2]
    if re.fullmatch(r"\d+", first_value):
        return first_value.lstrip("0") or "0"
    return first_value
def _has_value(value):
    if value is None or pd.isna(value):
        return False
    return bool(str(value).strip()) and str(value).strip().lower() != "nan"
def deduplicate_pli_rows(df):
    if df.empty:
        return df.copy(), 0
    working = df.copy()
    working["_source_order"] = range(len(working))
    working["_pe_id"] = working["Product Event ID"].map(_identifier)
    pli_values = working.get("PE - PLI #", pd.Series(index=working.index, dtype=object))
    working["_pli_id"] = pli_values.map(_identifier)
    data_columns = [
        column for column in working.columns
        if column not in {"join_key", "_source_order", "_pe_id", "_pli_id"}
    ]
    working["_completeness"] = working[data_columns].apply(
        lambda row: sum(_has_value(value) for value in row), axis=1
    )
    identified = working[(working["_pe_id"] != "") & (working["_pli_id"] != "")].copy()
    unidentified = working.drop(index=identified.index).copy()
    identified = identified.sort_values(
        ["_completeness", "_source_order"], ascending=[False, True], kind="stable"
    ).drop_duplicates(subset=["_pe_id", "_pli_id"], keep="first")
    unidentified = unidentified.drop_duplicates(subset=data_columns, keep="first")
    deduplicated = pd.concat([identified, unidentified]).sort_values("_source_order", kind="stable")
    removed_count = len(working) - len(deduplicated)
    deduplicated = deduplicated.drop(
        columns=["_source_order", "_pe_id", "_pli_id", "_completeness"]
    ).reset_index(drop=True)
    return deduplicated, removed_count