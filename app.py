import io
import hashlib
import json
import math
import os
import re
import zipfile
from datetime import date, datetime
from xml.etree import ElementTree as ET
import time
import pandas as pd
import requests
import streamlit as st
import subprocess 
from pathlib import Path 
from zoneinfo import ZoneInfo
def format_month_day_year(dt):
    return dt.strftime("%B ") + str(dt.day) + dt.strftime(", %Y")
def get_last_updated_from_github():
    repo_slug = os.getenv("GITHUB_REPOSITORY", "").strip()
    owner = ""
    repo = ""
    if repo_slug and "/" in repo_slug:
        owner, repo = repo_slug.split("/", 1)
    else:
        owner = os.getenv("GITHUB_OWNER", "").strip()
        repo = os.getenv("GITHUB_REPO", "").strip()
    branch = os.getenv("GITHUB_BRANCH", "main").strip()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not owner or not repo:
        return "Unknown"
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        date_str = data["commit"]["committer"]["date"]
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return format_month_day_year(dt)
    except Exception:
        return "Unknown"
st.set_page_config(
    page_title="QA Monitoring Tool",
    layout="wide",
    initial_sidebar_state="expanded",
)
last_updated = get_last_updated_from_github()
def get_last_updated():
     try:
         script_path = Path(__file__).resolve()
         commit_time = subprocess.check_output(
             [
                 "git",
                 "log",
                 "-1",
                 "--format=%cI",
                 "--",
                 script_path.name,
             ],
             cwd=script_path.parent,
             text=True,
             stderr=subprocess.DEVNULL,
         ).strip()
         updated = datetime.fromisoformat(commit_time)
         updated = updated.astimezone(ZoneInfo("America/Chicago"))
         return updated.strftime("%B %d, %Y at %I:%M %p %Z")
     except Exception:
         updated = datetime.fromtimestamp(
             Path(__file__).stat().st_mtime,
             tz=ZoneInfo("America/Chicago"),
         )
         return updated.strftime("%B %d, %Y at %I:%M %p %Z")
def get_app_version():
    version_path = Path(__file__).resolve().with_name("VERSION")
    try:
        return version_path.read_text(encoding="utf-8").strip().removeprefix("v")
    except OSError:
        return "Unknown"
st.title("QA Monitoring Tool")
st.caption(f"Raw complaint review prioritization for QA monitoring")
st.caption(f"V{get_app_version()} - Last updated: {get_last_updated()}")
st.markdown("""
<style>
:root {
    --mdt-navy: #123b5d;
    --mdt-blue: #1f5f8b;
    --mdt-blue-2: #2a6fa3;
    --mdt-light-blue: #dcecf8;
    --mdt-very-light: #f4f9fd;
    --mdt-border: #c8dced;
    --mdt-text: #17324d;
    --mdt-muted: #5f7891;
    --mdt-white: #ffffff;
    --tier1-bg: #dceeff;
    --tier1-text: #0d3f66;
    --tier2-bg: #e7f4ff;
    --tier2-text: #1c5b89;
    --tier3-bg: #eef7fb;
    --tier3-text: #3d6d8d;
    --tier4-bg: #f3f8fc;
    --tier4-text: #5d7387;
    --good-bg: #e5f5ea;
    --good-text: #1f6b42;
    --bad-bg: #fde8e8;
    --bad-text: #9b1c1c;
    --idk-bad-bg: #fff4db;
    --idk-bad-text: #8a5a00;
    --idk-good-bg: #edf6ff;
    --idk-good-text: #245d8a;
}
.stApp {
    background: linear-gradient(180deg, #f7fbff 0%, #eef5fb 100%);
    color: var(--mdt-text);
}
.block-container {
    padding-top: 3rem;
    padding-bottom: 2rem;
    max-width: 1450px;
}
h1, h2, h3, h4 {
    color: var(--mdt-navy);
    letter-spacing: -0.01em;
}
h1 {
    font-weight: 700;
    margin-bottom: 0.2rem;
}
p, li, label, div {
    color: var(--mdt-text);
}
.small-note {
    color: var(--mdt-muted);
    font-size: 0.9rem;
}
.pretty-section {
    padding: 0.4rem 0 0.2rem 0;
    margin-top: 0.5rem;
}
section[data-testid="stSidebar"] {
    background: #edf4fa;
    border-right: 1px solid var(--mdt-border);
}
div[data-testid="stMetric"] {
    background: var(--mdt-white);
    border: 1px solid var(--mdt-border);
    border-left: 5px solid var(--mdt-blue);
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 2px 8px rgba(18, 59, 93, 0.06);
}
div[data-testid="stMetricLabel"] {
    color: var(--mdt-muted);
    font-weight: 600;
}
div[data-testid="stMetricValue"] {
    color: var(--mdt-navy);
    font-weight: 700;
}
div[data-testid="stDataFrame"] {
    background: var(--mdt-white);
    border: 1px solid var(--mdt-border);
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(18, 59, 93, 0.04);
    overflow: hidden;
}
div[data-testid="stExpander"] {
    background: var(--mdt-white);
    border: 1px solid var(--mdt-border);
    border-radius: 12px;
}
.stButton > button,
.stDownloadButton > button {
    background: linear-gradient(180deg, #2c6f9e 0%, #1f5f8b 100%);
    color: white;
    border: 1px solid #1b5379;
    border-radius: 10px;
    font-weight: 600;
    padding: 0.45rem 1rem;
    box-shadow: 0 2px 6px rgba(18, 59, 93, 0.15);
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    background: linear-gradient(180deg, #255f87 0%, #174867 100%);
    border: 1px solid #143f5b;
    color: white;
}
.stTextInput > div > div,
.stNumberInput > div > div,
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background-color: var(--mdt-white);
    border-radius: 10px;
}
div[data-baseweb="select"] > div {
    border-color: var(--mdt-border);
}
input, textarea {
    color: var(--mdt-text);
}
div[data-testid="stTabs"] button {
    color: var(--mdt-navy);
    font-weight: 600;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--mdt-blue);
}
hr {
    border: none;
    border-top: 1px solid var(--mdt-border);
}
[data-testid="stCaptionContainer"] {
    color: var(--mdt-muted);
}
.review-table-wrapper {
    background: white;
    border: 1px solid var(--mdt-border);
    border-radius: 12px;
    padding: 10px;
    overflow-x: auto;
    box-shadow: 0 2px 8px rgba(18, 59, 93, 0.04);
}
.review-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
}
.review-table th {
    background: #e9f2fa;
    color: var(--mdt-navy);
    text-align: left;
    padding: 10px 12px;
    border-bottom: 1px solid var(--mdt-border);
    position: sticky;
    top: 0;
}
.review-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #edf2f7;
    vertical-align: top;
}
.review-table tr:hover {
    background: #f8fbff;
}
.badge {
    display: inline-block;
    padding: 0.22rem 0.6rem;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 700;
    white-space: nowrap;
}
.tier1 { background: var(--tier1-bg); color: var(--tier1-text); }
.tier2 { background: var(--tier2-bg); color: var(--tier2-text); }
.tier3 { background: var(--tier3-bg); color: var(--tier3-text); }
.tier4 { background: var(--tier4-bg); color: var(--tier4-text); }
.good { background: var(--good-bg); color: var(--good-text); }
.bad { background: var(--bad-bg); color: var(--bad-text); }
.idk-bad { background: var(--idk-bad-bg); color: var(--idk-bad-text); }
.idk-good { background: var(--idk-good-bg); color: var(--idk-good-text); }
</style>
""", unsafe_allow_html=True)
DEFAULT_BASE_MODELS_URL = "https://api.gpt.medtronic.com/providers/medtronicgpt/models"
DEFAULT_MODEL_ID = "gpt-41"
SYSTEM_PROMPT = """You are assisting with QA post-process monitoring of raw complaint/product event handling. Review each record only for inconsistencies between coded fields and related record content. Do not make assumptions beyond the information provided. Do not make final regulatory, compliance, or clinical decisions.

Each record may include multiple product line items (PLIs) for the same Product Event ID. Evaluate the current PLI in the context of all related PLIs, not as an isolated record. The event description can describe a problem with only one of several PLIs. Do not flag the other PLIs merely because their individual coding does not describe that problem. Flag coding only when the collective PLI context shows that the coding for the applicable PLI(s) is missing, contradictory, or otherwise inconsistent.

Focus only on these three checks:

Inconsistency between coding and the Event Description
Inconsistency between coding and regulatory decisions
Inconsistency between coding and investigation decisions

Use the raw fields in the record, especially:
- RFR Code
- FDP Code
- Reportable
- Investigation Required
- Brazil FER
- China FER
- Japan FER
- Korea FER
- Event Description - PE
- Summary of Investigation Results
- PLI Tasks
- Rationale for no return - PE PLI

Return only the structured result. Do not repeat the prompt or restate the full complaint record."""
USER_PROMPT_TEMPLATE = """Review the raw complaint/product event record below for QA post-process monitoring.

Evaluate only these three areas:

Coding vs. Event Description
Determine whether coded fields such as RFR Code and FDP Code are consistent with Event Description - PE and other narrative text. Cross-reference every related PLI for the Product Event ID before deciding. A problem that applies to one PLI does not require every sibling PLI to carry matching complaint coding.

Coding vs. Regulatory Decisions
Determine whether coded fields and event severity are consistent with Reportable and country FER fields.

Coding vs. Investigation Decisions
Determine whether coded fields and event narrative are consistent with Investigation Required, Summary of Investigation Results, PLI Tasks, and Rationale for no return - PE PLI.

For each area, state:

Yes or No for whether an inconsistency is present
a short reason

Then provide:

layer2_flag: Yes or No
concern_level: Low, Medium, or High
layer2_reason: short summary based only on the inconsistency checks above

Use this decision logic:

If no inconsistencies are found, set layer2_flag to No
If one inconsistency is found, set layer2_flag to Yes and assign Low or Medium concern based on significance
If two or more inconsistencies are found, set layer2_flag to Yes
If any inconsistency could materially affect quality, compliance, or documentation interpretation, set concern_level to High

Return the result in exactly this format:

coding_event_description_inconsistency: Yes/No
coding_event_description_reason:

coding_regulatory_decision_inconsistency: Yes/No
coding_regulatory_decision_reason:

coding_investigation_decision_inconsistency: Yes/No
coding_investigation_decision_reason:

layer2_flag: Yes/No
concern_level: Low/Medium/High
layer2_reason:

Complaint Record: {initial_json}"""
TIER_LABELS = {
    1: "Tier 1 - Critical QA Review",
    2: "Tier 2 - Targeted QA Review",
    3: "Tier 3 - Follow-Up Signal",
    4: "Tier 4 - No Review Signal",
}
PORTFOLIO_OU_MAP = {
    "Cardiovascular Portfolio": [
        "Cardiac Ablation Solutions",
        "Cardiac Rhythm Management",
        "Cardiac Surgery",
        "Coronary and Renal Denervation",
        "Mechanical Circulatory Support",
        "Structural Heart and Aortic",
        "Peripheral Vascular Health",
    ],
    "Neuroscience Portfolio": [
        "Cranial and Spinal Technologies",
        "Ear, Nose, and Throat",
        "Neuromodulation",
        "Neurovascular",
        "Pelvic Health",
    ],
    "Medical Surgical Portfolio": [
        "Acute Care & Monitoring",
        "Endoscopy",
        "Renal Care Solutions",
        "Surgical",
        "Ventilation Service Solutions",
    ],
}
DEATH_KEYWORDS = [
    "death",
    "died",
    "deceased",
    "fatal",
    "fatality",
]
SERIOUS_INJURY_KEYWORDS = [
    "serious injury",
    "seriously injured",
    "life threatening",
    "life-threatening",
    "hospitalization",
    "permanent impairment",
    "permanent damage",
]
FIRE_KEYWORDS = [
    "fire",
    "smoke",
    "burn",
    "burning",
    "sparking",
    "spark",
    "flame",
    "overheat",
    "overheating",
]
RAW_REQUIRED_FIELDS = [
    "Product Event ID",
    "Complaint? - PE",
    "Country – PE",
    "RFR Code",
    "FDP Code",
    "Reportable?",
    "Investigation Required?",
    "Event Description - PE",
]
base_models_url = st.text_input(
    "MDTGPT Models Base URL",
    value=os.getenv("MDTGPT_MODELS_BASE_URL", DEFAULT_BASE_MODELS_URL),
)
model_id = st.text_input(
    "Model ID",
    value=os.getenv("MDTGPT_MODEL_ID", DEFAULT_MODEL_ID),
    help="Defaults to gpt-41. If your GET /models response shows a different GPT 4.1 ID, use that value here.",
)
bearer_token = st.text_input(
    "Bearer Token",
    value=os.getenv("MDTGPT_API_TOKEN", ""),
    type="password",
)
timeout_seconds = st.number_input(
    "Request timeout (seconds)",
    min_value=5,
    max_value=300,
    value=int(os.getenv("MDTGPT_TIMEOUT_SECONDS", "60")),
)
with st.expander("Model request settings", expanded=False):
    temperature = st.number_input("temperature", min_value=0.0, max_value=2.0, value=0.0, step=0.1)
    top_p = st.number_input("top_p", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
    max_completion_tokens = st.number_input(
        "max_completion_tokens",
        min_value=1,
        max_value=32768,
        value=32768,
        step=100,
    )
    stream = st.checkbox("stream", value=False)
st.caption("Upload a raw workbook to start, or reupload an exported results workbook to resume")
uploaded_files = st.file_uploader(
    "Upload Excel workbooks",
    type=["xlsx"],
    accept_multiple_files=True,
    help=(
        "Upload a raw complaint workbook to start. To resume, upload just a results "
        "workbook exported by this tool; it already contains the input rows. You can "
        "also include additional results workbooks to combine their completed rows."
    ),
)
st.markdown(
    '<div class="small-note">Upload the raw complaint workbook to run layered screening, MDTGPT consistency review, and tiered prioritization.</div>',
    unsafe_allow_html=True
)
st.subheader("Portfolio Selection")
selected_portfolio = st.selectbox(
    "Select Portfolio",
    options=["Select Portfolio"] + list(PORTFOLIO_OU_MAP.keys()),
    index=0,
)
selected_ou_options = ["Select OU"]
if selected_portfolio in PORTFOLIO_OU_MAP:
    selected_ou_options += PORTFOLIO_OU_MAP[selected_portfolio]
selected_ou = st.selectbox(
    "Select Operating Unit (OU)",
    options=selected_ou_options,
    index=0,
)
if "processed_results" not in st.session_state:
    st.session_state.processed_results = None
if "processed_preview_df" not in st.session_state:
    st.session_state.processed_preview_df = None
if "processed_workbook_info" not in st.session_state:
    st.session_state.processed_workbook_info = None
if "processed_tier_summary_df" not in st.session_state:
    st.session_state.processed_tier_summary_df = None
if "processed_organized_results_df" not in st.session_state:
    st.session_state.processed_organized_results_df = None
if "processed_clean_display_df" not in st.session_state:
    st.session_state.processed_clean_display_df = None
if "processed_pretty_review_df" not in st.session_state:
    st.session_state.processed_pretty_review_df = None
if "processed_html_review_df" not in st.session_state:
    st.session_state.processed_html_review_df = None
if "processed_results_xlsx" not in st.session_state:
    st.session_state.processed_results_xlsx = None
if "last_uploaded_filename" not in st.session_state:
    st.session_state.last_uploaded_filename = None
if "last_uploaded_fingerprint" not in st.session_state:
    st.session_state.last_uploaded_fingerprint = None
if "loaded_partial_fingerprints" not in st.session_state:
    st.session_state.loaded_partial_fingerprints = set()
DASH_TRANSLATION = str.maketrans({
    "\u2010": "-",
    "\u2011": "-",
    "\u2012": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u2212": "-", 
})
def normalize_text(value):
    if value is None or (
        isinstance(value, float) and math.isnan(value)
    ):
        return ""
    text = str(value).translate(DASH_TRANSLATION)
    text = text.strip().lower().replace("_", " ")
    return re.sub(r"\s+", " ", text)
def normalize_column_label(value):
    label = "" if value is None else str(value)
    label = label.translate(DASH_TRANSLATION)
    label = re.sub(r"\s+", " ", label).strip()
    label = label.replace(" :", ":")
    return label
def dedupe_columns(columns):
    seen = {}
    output = []
    for index, column in enumerate(columns, start=1):
        base = normalize_column_label(column) or f"Column_{index}"
        if base not in seen:
            seen[base] = 0
            output.append(base)
        else:
            seen[base] += 1
            output.append(f"{base}_{seen[base]}")
    return output
def clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, float) and math.isnan(value):
        return None
    return value
def clean_row(row_dict):
    return {normalize_column_label(k): clean_value(v) for k, v in row_dict.items()}
def lower_str(value):
    if value is None:
        return ""
    return str(value).strip().lower()
def safe_text(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text
def get_value(row_dict, *keys):
    for key in keys:
        if key in row_dict and row_dict[key] not in (None, "", "nan"):
            return row_dict[key]
    return None
def get_country_value(row_dict):
    return safe_text(get_value(
        row_dict,
        "Country - PE",
        "Country – PE",
        "Country — PE",
        "Country-PE",
        "Country PE",
        "Country",
    ))
def value_to_id_text(value):
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()
def normalize_identifier(value):
    text = value_to_id_text(value)
    text = text.strip()
    if not text:
        return ""
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    if re.fullmatch(r"\d+", text):
        return text.lstrip("0") or "0"
    return text
def extract_ids(value):
    text = value_to_id_text(value)
    if not text:
        return []
    parts = re.split(r"[,;|\n]+", text)
    ids = []
    for part in parts:
        normalized = normalize_identifier(part)
        if normalized:
            ids.append(normalized)
    return ids
def yes_like(value):
    normalized = lower_str(value)
    return normalized in {
        "yes", "y", "true", "1", "required", "reportable"
    }
def no_like(value):
    normalized = lower_str(value)
    return normalized in {
        "no", "n", "false", "0", "not required", "not reportable", "non-reportable"
    }
def ensure_key_columns(df):
    df = df.copy()
    df.columns = dedupe_columns(df.columns)
    if "Product Event ID" not in df.columns and "ProductEventID" in df.columns:
        df["Product Event ID"] = df["ProductEventID"]
    return df
def infer_sheet_role(sheet_name, df):
    sheet_name_norm = normalize_text(sheet_name)
    cols_norm = {normalize_text(c) for c in df.columns}
    if "instruction" in sheet_name_norm:
        return "ignore"
    if "product event id" in cols_norm and "event description - pe" in cols_norm:
        return "main"
    if "raw" in sheet_name_norm and "product event id" in cols_norm:
        return "main"
    if "data" in sheet_name_norm and "product event id" in cols_norm:
        return "main"
    return "ignore"
def find_header_row(raw_df):
    if raw_df.empty:
        return 0
    max_rows = min(len(raw_df), 30)
    for i in range(max_rows):
        row_values = [normalize_text(v) for v in raw_df.iloc[i].tolist()]
        row_set = set(row_values)
        if "product event id" in row_set and "event description - pe" in row_set:
            return i
    return 0
def prepare_sheet_dataframe(raw_df):
    if raw_df.empty:
        return pd.DataFrame()
    raw_df = raw_df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    if raw_df.empty:
        return pd.DataFrame()
    header_idx = find_header_row(raw_df)
    headers = dedupe_columns(raw_df.iloc[header_idx].tolist())
    df = raw_df.iloc[header_idx + 1:].copy()
    df.columns = headers
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    unnamed_like_cols = [c for c in df.columns if normalize_text(c) in {"", "nan", "none"}]
    if unnamed_like_cols:
        df = df.drop(columns=unnamed_like_cols, errors="ignore")
    return ensure_key_columns(df)
def strict_xlsx_to_dataframes(file_bytes):
    MAIN_NS = "http://purl.oclc.org/ooxml/spreadsheetml/main"
    REL_NS = "http://purl.oclc.org/ooxml/officeDocument/relationships"
    PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
    def tag(ns, name):
        return f"{{{ns}}}{name}"
    def col_to_index(cell_ref):
        match = re.match(r"([A-Z]+)(\d+)", cell_ref or "")
        if not match:
            return None, None
        col_letters, row_num = match.groups()
        col_num = 0
        for ch in col_letters:
            col_num = col_num * 26 + (ord(ch) - 64)
        return int(row_num), col_num
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
        names = set(zf.namelist())
        shared_strings = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall(tag(MAIN_NS, "si")):
                text_parts = [t.text or "" for t in si.iter(tag(MAIN_NS, "t"))]
                shared_strings.append("".join(text_parts))
        rel_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rels = {
            rel.attrib["Id"]: rel.attrib["Target"].lstrip("/")
            for rel in rel_root.findall(tag(PKG_REL_NS, "Relationship"))
        }
        wb_root = ET.fromstring(zf.read("xl/workbook.xml"))
        sheets_node = wb_root.find(tag(MAIN_NS, "sheets"))
        if sheets_node is None:
            raise ValueError("Could not find workbook sheets in uploaded xlsx.")
        workbook = {}
        for sheet in sheets_node.findall(tag(MAIN_NS, "sheet")):
            sheet_name = sheet.attrib.get("name", "Sheet")
            rid = sheet.attrib.get(tag(REL_NS, "id"))
            if rid not in rels:
                continue
            target = rels[rid]
            if not target.startswith("xl/"):
                target = "xl/" + target
            if target not in names:
                continue
            ws_root = ET.fromstring(zf.read(target))
            values_by_position = {}
            max_row = 0
            max_col = 0
            for cell in ws_root.iter(tag(MAIN_NS, "c")):
                row_idx, col_idx = col_to_index(cell.attrib.get("r"))
                if row_idx is None:
                    continue
                cell_type = cell.attrib.get("t")
                value_node = cell.find(tag(MAIN_NS, "v"))
                value = None
                if cell_type == "s" and value_node is not None and value_node.text is not None:
                    idx = int(value_node.text)
                    value = shared_strings[idx] if idx < len(shared_strings) else value_node.text
                elif cell_type == "inlineStr":
                    inline = cell.find(tag(MAIN_NS, "is"))
                    if inline is not None:
                        value = "".join(t.text or "" for t in inline.iter(tag(MAIN_NS, "t")))
                elif value_node is not None:
                    value = value_node.text
                values_by_position[(row_idx, col_idx)] = value
                max_row = max(max_row, row_idx)
                max_col = max(max_col, col_idx)
            matrix = []
            for row_idx in range(1, max_row + 1):
                row = [values_by_position.get((row_idx, col_idx)) for col_idx in range(1, max_col + 1)]
                matrix.append(row)
            workbook[sheet_name] = pd.DataFrame(matrix)
        if not workbook:
            raise ValueError("No readable worksheets found in uploaded xlsx.")
        return workbook
def read_workbook_as_raw_dataframes(uploaded):
    file_bytes = uploaded.getvalue()
    try:
        workbook = pd.read_excel(
            io.BytesIO(file_bytes),
            sheet_name=None,
            engine="openpyxl",
            header=None,
            dtype=object,
        )
        if not workbook:
            raise ValueError("No sheets found by openpyxl.")
        return workbook, "openpyxl"
    except Exception as openpyxl_error:
        workbook = strict_xlsx_to_dataframes(file_bytes)
        st.info(
            "The workbook was read using the strict-OOXML fallback reader because openpyxl could not read it. "
            f"Original openpyxl error: {openpyxl_error}"
        )
        return workbook, "strict_ooxml_fallback"
def build_join_key_from_row(row_dict):
    product_event_ids = extract_ids(row_dict.get("Product Event ID"))
    pe_pli_ids = extract_ids(row_dict.get("PE - PLI #"))
    peid = product_event_ids[0] if product_event_ids else ""
    pepli = pe_pli_ids[0] if pe_pli_ids else ""
    if peid and pepli:
        return f"PEID::{peid}::PEPLI::{pepli}"
    if pepli:
        return f"PEPLI::{pepli}"
    if peid:
        return f"PEID::{peid}"
    return None
def add_join_key(df):
    df = ensure_key_columns(df)
    df = df.copy()
    df["join_key"] = df.apply(lambda row: build_join_key_from_row(row.to_dict()), axis=1)
    return df
def build_complaint_record(row_dict, row_number):
    return {
        "rowNumber": row_number,
        "currentPli": row_dict,
        "relatedPlis": [],
        "focusChecks": [
            "Coding vs. Event Description",
            "Coding vs. Regulatory Decisions",
            "Coding vs. Investigation Decisions",
        ],
        "data": row_dict,
    }
PLI_CONTEXT_FIELDS = [
    "Product Event ID",
    "PE - PLI #",
    "Complaint? - PE",
    "Product Description - PE PLI",
    "RFR Code",
    "FDP Code",
    "Reportable?",
    "Investigation Required?",
    "Event Description - PE",
    "Summary of Investigation Results",
    "PLI Tasks",
    "Rationale for no return - PE PLI",
]
def build_related_pli_lookup(df):
    related_by_event = {}
    for idx, row in df.iterrows():
        row_dict = clean_row(row.drop(labels=["join_key"], errors="ignore").to_dict())
        product_event_ids = extract_ids(row_dict.get("Product Event ID"))
        if not product_event_ids:
            continue
        context = {
            "sourceRowNumber": int(idx) + 1,
            **{field: row_dict.get(field) for field in PLI_CONTEXT_FIELDS},
        }
        related_by_event.setdefault(product_event_ids[0], []).append(context)
    return related_by_event
def add_related_plis(complaint_record, row_dict, related_pli_lookup):
    product_event_ids = extract_ids(row_dict.get("Product Event ID"))
    related_plis = related_pli_lookup.get(product_event_ids[0], []) if product_event_ids else []
    complaint_record["relatedPlis"] = related_plis
    complaint_record["pliEvaluationInstruction"] = (
        "Evaluate currentPli using relatedPlis collectively. Do not treat a sibling PLI as "
        "miscoded solely because the event description concerns a different PLI."
    )
    return complaint_record
def build_user_prompt(complaint_record):
    initial_json = json.dumps(complaint_record, ensure_ascii=False, default=str, indent=2)
    return USER_PROMPT_TEMPLATE.format(initial_json=initial_json)
def build_model_request_json(complaint_record):
    request_json = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(complaint_record)},
        ],
        "temperature": temperature,
        "top_p": top_p,
        "max_completion_tokens": int(max_completion_tokens),
        "stream": bool(stream),
    }
    return request_json
def get_model_endpoint():
    return f"{base_models_url.rstrip('/')}/{model_id.strip()}"
TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}
def send_row_to_model(session, token, complaint_record, timeout, attempts=3, wait_seconds=3):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            response = session.post(
                get_model_endpoint(),
                headers=headers,
                json=build_model_request_json(complaint_record),
                timeout=timeout,
            )
            if response.status_code in TRANSIENT_STATUS_CODES and attempt < attempts:
                time.sleep(wait_seconds)
                continue
            return response
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.RequestException,
        ) as e:
            last_error = e
            if attempt < attempts:
                time.sleep(wait_seconds)
            else:
                raise RuntimeError(
                    f"MDTGPT request failed after {attempts} attempts for Excel row "
                    f"{complaint_record.get('rowNumber')}: {e}"
                ) from e
    raise RuntimeError(
        f"MDTGPT request failed after {attempts} attempts for Excel row "
        f"{complaint_record.get('rowNumber')}: {last_error}"
    )
def clean_excel_cell_value(value):
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, default=str)
    if value is None:
        return ""
    return value
def collect_text_for_keyword_scan(row_dict):
    fields = [
        "Event Description - PE",
        "Summary of Investigation Results",
        "PLI Tasks",
        "Rationale for no return - PE PLI",
        "Product Description - PE PLI",
        "RFR Code",
        "FDP Code",
    ]
    parts = []
    for field in fields:
        value = row_dict.get(field)
        if value is not None and str(value).strip() and str(value).strip().lower() != "nan":
            parts.append(str(value).strip())
    return " ".join(parts)
def find_matched_keywords(text, keywords):
    matched = []
    search_text = lower_str(text)
    for keyword in keywords:
        pattern = r"\b" + re.escape(lower_str(keyword)) + r"\b"
        if re.search(pattern, search_text):
            matched.append(keyword)
    return matched
def any_regional_fer_yes(row_dict):
    fer_fields = ["Brazil FER", "China FER", "Japan FER", "Korea FER"]
    return any(yes_like(row_dict.get(field)) for field in fer_fields)
def layer1_rule_based_screening(row_dict, related_plis=None):
    flags = []
    reasons = []
    score = 0
    missing_fields = [field for field in RAW_REQUIRED_FIELDS if not get_value(row_dict, field)]
    if missing_fields:
        flags.append("missing_required_fields")
        reasons.append(f"Missing raw fields: {', '.join(missing_fields)}")
        score += 2
    event_description = safe_text(row_dict.get("Event Description - PE"))
    summary_results = safe_text(row_dict.get("Summary of Investigation Results"))
    rfr_code = safe_text(row_dict.get("RFR Code"))
    fdp_code = safe_text(row_dict.get("FDP Code"))
    reportable = row_dict.get("Reportable?")
    investigation_required = row_dict.get("Investigation Required?")
    keyword_scan_text = collect_text_for_keyword_scan(row_dict)
    death_matches = find_matched_keywords(keyword_scan_text, DEATH_KEYWORDS)
    if death_matches:
        flags.append("death_keyword_present")
        reasons.append(f"Death-related keyword(s) found in raw text: {', '.join(sorted(set(death_matches)))}")
        score += 4
    serious_injury_matches = find_matched_keywords(keyword_scan_text, SERIOUS_INJURY_KEYWORDS)
    if serious_injury_matches:
        flags.append("serious_injury_keyword_present")
        reasons.append(
            f"Serious injury keyword(s) found in raw text: {', '.join(sorted(set(serious_injury_matches)))}"
        )
        score += 4
    fire_matches = find_matched_keywords(keyword_scan_text, FIRE_KEYWORDS)
    if fire_matches:
        flags.append("fire_keyword_present")
        reasons.append(f"Fire-related keyword(s) found in raw text: {', '.join(sorted(set(fire_matches)))}")
        score += 4
    severe_signal_present = bool(death_matches or serious_injury_matches or fire_matches)
    related_plis = related_plis or []
    sibling_complaint_is_coded = any(
        yes_like(pli.get("Complaint? - PE"))
        and (safe_text(pli.get("RFR Code")) or safe_text(pli.get("FDP Code")))
        for pli in related_plis
    )
    current_is_non_complaint = no_like(row_dict.get("Complaint? - PE"))
    if (
        event_description
        and not rfr_code
        and not fdp_code
        and not (current_is_non_complaint and sibling_complaint_is_coded)
    ):
        flags.append("coding_event_description_rule_flag")
        reasons.append("Event Description is present but both RFR Code and FDP Code are blank")
        score += 3
    if severe_signal_present and no_like(reportable):
        flags.append("coding_regulatory_decision_rule_flag")
        reasons.append("Severe event wording is present while Reportable is marked No or Not Reportable")
        score += 3
    if severe_signal_present and not safe_text(reportable):
        flags.append("coding_regulatory_decision_missing_flag")
        reasons.append("Severe event wording is present but Reportable is blank")
        score += 2
    if any_regional_fer_yes(row_dict) and no_like(reportable):
        flags.append("regional_fer_reportable_mismatch")
        reasons.append("At least one country FER field is Yes while Reportable is marked No or Not Reportable")
        score += 3
    if yes_like(investigation_required) and not summary_results:
        flags.append("coding_investigation_decision_rule_flag")
        reasons.append("Investigation Required is Yes but Summary of Investigation Results is blank")
        score += 3
    if severe_signal_present and no_like(investigation_required):
        flags.append("investigation_required_mismatch")
        reasons.append("Severe event wording is present while Investigation Required is marked No or Not Required")
        score += 3
    return {
        "layer1_flags": flags,
        "layer1_reasons": reasons,
        "layer1_score": score,
    }
def extract_model_content(response_body):
    if isinstance(response_body, dict):
        choices = response_body.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict) and message.get("content") is not None:
                    return str(message.get("content"))
                if first_choice.get("text") is not None:
                    return str(first_choice.get("text"))
        for key in ["content", "output", "response", "result", "text"]:
            if response_body.get(key) is not None:
                return str(response_body.get(key))
    if isinstance(response_body, str):
        return response_body
    return json.dumps(response_body, default=str)
def parse_key_value_text(text):
    expected_keys = [
        "coding_event_description_inconsistency",
        "coding_event_description_reason",
        "coding_regulatory_decision_inconsistency",
        "coding_regulatory_decision_reason",
        "coding_investigation_decision_inconsistency",
        "coding_investigation_decision_reason",
        "layer2_flag",
        "concern_level",
        "layer2_reason",
    ]
    parsed = {}
    current_key = None
    current_parts = []
    key_pattern = re.compile(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$")
    for raw_line in str(text).splitlines():
        line = raw_line.rstrip()
        match = key_pattern.match(line.strip())
        if match and match.group(1) in expected_keys:
            if current_key is not None:
                parsed[current_key] = "\n".join(current_parts).strip()
            current_key = match.group(1)
            current_parts = [match.group(2).strip()] if match.group(2).strip() else []
        elif current_key is not None:
            if line.strip():
                current_parts.append(line.strip())
    if current_key is not None:
        parsed[current_key] = "\n".join(current_parts).strip()
    return parsed
def parse_layer2_response(response_body):
    if isinstance(response_body, str):
        try:
            loaded = json.loads(response_body)
            return parse_layer2_response(loaded)
        except Exception:
            return parse_key_value_text(response_body)
    content = extract_model_content(response_body)
    try:
        loaded_content = json.loads(content)
        if isinstance(loaded_content, dict):
            return loaded_content
    except Exception:
        pass
    return parse_key_value_text(content)
def build_exact_inconsistency_found(layer2_result, row_dict):
    event_flag = str(layer2_result.get("coding_event_description_inconsistency", "")).strip().lower() == "yes"
    reg_flag = str(layer2_result.get("coding_regulatory_decision_inconsistency", "")).strip().lower() == "yes"
    inv_flag = str(layer2_result.get("coding_investigation_decision_inconsistency", "")).strip().lower() == "yes"
    flagged_areas = []
    if event_flag:
        flagged_areas.append("event description")
    if reg_flag:
        flagged_areas.append("regulatory decision")
    if inv_flag:
        flagged_areas.append("investigation decision")
    if not flagged_areas:
        return ""
    rfr_code = safe_text(row_dict.get("RFR Code"))
    fdp_code = safe_text(row_dict.get("FDP Code"))
    code_parts = []
    if rfr_code:
        code_parts.append(f'RFR "{rfr_code}"')
    if fdp_code:
        code_parts.append(f'FDP "{fdp_code}"')
    if code_parts:
        coding_text = " and ".join(code_parts)
        return f"Assigned coding ({coding_text}) does not align with the {', '.join(flagged_areas)}."
    return f"Assigned coding does not align with the {', '.join(flagged_areas)}."
def layer3_prioritization(layer1_result, layer2_result):
    score = layer1_result.get("layer1_score", 0)
    reasons = []
    if layer1_result.get("layer1_flags"):
        reasons.append("Layer 1 flags present")
    inconsistency_fields = [
        "coding_event_description_inconsistency",
        "coding_regulatory_decision_inconsistency",
        "coding_investigation_decision_inconsistency",
    ]
    inconsistency_count = 0
    for field in inconsistency_fields:
        if str(layer2_result.get(field, "")).strip().lower() == "yes":
            inconsistency_count += 1
    if inconsistency_count > 0:
        score += inconsistency_count * 2
        reasons.append(f"{inconsistency_count} Layer 2 inconsistency checks flagged")
    concern_level = str(layer2_result.get("concern_level", "")).strip().lower()
    if concern_level == "high":
        score += 4
        reasons.append("Layer 2 concern level = High")
    elif concern_level == "medium":
        score += 2
        reasons.append("Layer 2 concern level = Medium")
    elif concern_level == "low":
        score += 1
        reasons.append("Layer 2 concern level = Low")
    if inconsistency_count >= 2 or concern_level == "high" or score >= 8:
        tier = 1
    elif inconsistency_count == 1 or concern_level == "medium" or score >= 5:
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
def build_clear_categorization(layer1_result, layer2_result, layer3_result, row_dict):
    layer1_flags = layer1_result.get("layer1_flags", [])
    layer1_reasons = layer1_result.get("layer1_reasons", [])
    priority_tier = layer3_result.get("priority_tier")
    priority_score = layer3_result.get("priority_score")
    event_flag = str(layer2_result.get("coding_event_description_inconsistency", "")).strip().lower() == "yes"
    reg_flag = str(layer2_result.get("coding_regulatory_decision_inconsistency", "")).strip().lower() == "yes"
    inv_flag = str(layer2_result.get("coding_investigation_decision_inconsistency", "")).strip().lower() == "yes"
    inconsistency_types = []
    specific_findings = []
    if event_flag:
        inconsistency_types.append("Coding vs Event Description")
        if safe_text(layer2_result.get("coding_event_description_reason")):
            specific_findings.append(
                f"Event Description: {safe_text(layer2_result.get('coding_event_description_reason'))}"
            )
    if reg_flag:
        inconsistency_types.append("Coding vs Regulatory Decisions")
        if safe_text(layer2_result.get("coding_regulatory_decision_reason")):
            specific_findings.append(
                f"Regulatory Decisions: {safe_text(layer2_result.get('coding_regulatory_decision_reason'))}"
            )
    if inv_flag:
        inconsistency_types.append("Coding vs Investigation Decisions")
        if safe_text(layer2_result.get("coding_investigation_decision_reason")):
            specific_findings.append(
                f"Investigation Decisions: {safe_text(layer2_result.get('coding_investigation_decision_reason'))}"
            )
    inconsistency_count = len(inconsistency_types)
    concern_level = safe_text(layer2_result.get("concern_level"))
    layer2_flag = safe_text(layer2_result.get("layer2_flag"))
    layer2_reason = safe_text(layer2_result.get("layer2_reason"))
    if priority_tier == 1:
        category_name = TIER_LABELS[1]
        recommended_action = "Immediate QA review recommended"
    elif priority_tier == 2:
        category_name = TIER_LABELS[2]
        recommended_action = "QA review recommended"
    elif priority_tier == 3:
        category_name = TIER_LABELS[3]
        recommended_action = "Documentation follow-up or secondary review recommended"
    elif priority_tier == 4:
        category_name = TIER_LABELS[4]
        recommended_action = "No immediate review signal; retain for routine monitoring"
    else:
        category_name = "Uncategorized"
        recommended_action = "Manual review needed"
    primary_basis = []
    supporting_basis = []
    if inconsistency_count >= 2:
        primary_basis.append(f"{inconsistency_count} inconsistency checks were flagged")
    elif inconsistency_count == 1:
        primary_basis.append(f"1 inconsistency check was flagged: {inconsistency_types[0]}")
    if concern_level:
        primary_basis.append(f"Concern level assessed as {concern_level}")
    if layer2_flag:
        primary_basis.append(f"Layer 2 flag = {layer2_flag}")
    if priority_score is not None:
        primary_basis.append(f"Priority score = {priority_score}")
    if "missing_required_fields" in layer1_flags:
        supporting_basis.append("One or more key raw fields are missing")
    if "coding_event_description_rule_flag" in layer1_flags:
        supporting_basis.append("Rule-based screening flagged a coding vs event-description issue")
    if "coding_regulatory_decision_rule_flag" in layer1_flags:
        supporting_basis.append("Rule-based screening flagged a coding vs regulatory issue")
    if "coding_regulatory_decision_missing_flag" in layer1_flags:
        supporting_basis.append("Rule-based screening found severe wording with Reportable blank")
    if "regional_fer_reportable_mismatch" in layer1_flags:
        supporting_basis.append("Country FER fields do not align with Reportable")
    if "coding_investigation_decision_rule_flag" in layer1_flags:
        supporting_basis.append("Rule-based screening flagged an investigation decision issue")
    if "investigation_required_mismatch" in layer1_flags:
        supporting_basis.append("Severe wording does not align with Investigation Required")
    if "death_keyword_present" in layer1_flags:
        supporting_basis.append("Death-related wording was found in raw text")
    if "serious_injury_keyword_present" in layer1_flags:
        supporting_basis.append("Serious injury wording was found in raw text")
    if "fire_keyword_present" in layer1_flags:
        supporting_basis.append("Fire-related wording was found in raw text")
    if not primary_basis and priority_tier == 4:
        primary_basis.append("No inconsistency was identified and no material escalation signal was found")
    if not primary_basis and priority_tier == 3:
        primary_basis.append("No direct model inconsistency was identified, but supporting review signals were present")
    short_reason_parts = []
    if inconsistency_count > 0:
        short_reason_parts.append(f"Inconsistencies flagged: {', '.join(inconsistency_types)}")
    else:
        short_reason_parts.append("No direct inconsistency flagged by Layer 2")
    if priority_tier == 4:
        short_reason_parts.append("Assigned to routine monitoring")
    if priority_tier == 3 and any(flag in layer1_flags for flag in [
        "death_keyword_present",
        "serious_injury_keyword_present",
        "fire_keyword_present",
        "missing_required_fields",
    ]):
        short_reason_parts.append("Layer 1 review signals increased priority")
    category_short_reason = "; ".join(short_reason_parts)
    detailed_parts = []
    if primary_basis:
        detailed_parts.append("Primary basis: " + "; ".join(primary_basis))
    if specific_findings:
        detailed_parts.append("Specific findings: " + "; ".join(specific_findings))
    if layer2_reason:
        detailed_parts.append("Layer 2 summary: " + layer2_reason)
    if supporting_basis:
        detailed_parts.append("Supporting signals: " + "; ".join(supporting_basis))
    if layer1_reasons:
        detailed_parts.append(
            "Layer 1 details: " + "; ".join([safe_text(x) for x in layer1_reasons if safe_text(x)])
        )
    category_detailed_reason = " | ".join(detailed_parts)
    return {
        "category_name": category_name,
        "category_short_reason": category_short_reason,
        "category_detailed_reason": category_detailed_reason,
        "recommended_action": recommended_action,
        "inconsistency_count": inconsistency_count,
        "inconsistency_types": " | ".join(inconsistency_types),
    }
def build_overall_judgment(row):
    concern = str(row.get("concern_level", "")).strip().lower()
    tier = pd.to_numeric(row.get("priority_tier"), errors="coerce")
    yes_count = 0
    for col in [
        "coding_event_description_inconsistency",
        "coding_regulatory_decision_inconsistency",
        "coding_investigation_decision_inconsistency",
    ]:
        if str(row.get(col, "")).strip().lower() == "yes":
            yes_count += 1
    if concern == "high" or yes_count >= 2 or tier == 1:
        return "Bad"
    if concern == "medium" or yes_count == 1 or tier == 2:
        return "IDK - Leaning Bad"
    if concern == "low" or tier == 3:
        return "IDK - Leaning Good"
    return "Good"
def format_tier_label(value):
    tier = pd.to_numeric(value, errors="coerce")
    if pd.isna(tier):
        return "Unknown"
    tier = int(tier)
    return TIER_LABELS.get(tier, f"Tier {tier}")
def build_pretty_review_df(results_df):
    if results_df.empty:
        return pd.DataFrame()
    df = results_df.copy()
    df["priority_tier"] = pd.to_numeric(df.get("priority_tier"), errors="coerce")
    df["priority_score"] = pd.to_numeric(df.get("priority_score"), errors="coerce")
    df["overall_judgment"] = df.apply(build_overall_judgment, axis=1)
    df["tier_label"] = df["priority_tier"].apply(format_tier_label)
    display_cols = [
        "row_number",
        "product_event_id",
        "pe_pli_number",
        "tier_label",
        "priority_score",
        "overall_judgment",
        "concern_level",
        "reportable",
        "investigation_required",
        "coding_event_description_inconsistency",
        "coding_regulatory_decision_inconsistency",
        "coding_investigation_decision_inconsistency",
        "category_short_reason",
        "exact_inconsistency_found",
        "recommended_action",
        "country",
        "rfr_code",
        "fdp_code",
    ]
    display_cols = [c for c in display_cols if c in df.columns]
    df = df[display_cols].copy()
    return df.rename(columns={
        "row_number": "Row Number",
        "product_event_id": "Product Event ID",
        "pe_pli_number": "PE - PLI #",
        "tier_label": "Tier",
        "priority_score": "Priority Score",
        "overall_judgment": "Overall Judgment",
        "concern_level": "Concern Level",
        "reportable": "Reportable",
        "investigation_required": "Investigation Required",
        "coding_event_description_inconsistency": "Event Description Inconsistency",
        "coding_regulatory_decision_inconsistency": "Regulatory Inconsistency",
        "coding_investigation_decision_inconsistency": "Investigation Inconsistency",
        "category_short_reason": "Short Reason",
        "exact_inconsistency_found": "Exact Inconsistency Found",
        "recommended_action": "Recommended Action",
        "country": "Country",
        "rfr_code": "RFR Code",
        "fdp_code": "FDP Code",
    })
def count_by_tier(results_df, tier_num):
    if results_df.empty or "priority_tier" not in results_df.columns:
        return 0
    return int((pd.to_numeric(results_df["priority_tier"], errors="coerce") == tier_num).sum())
def tier_badge_html(tier_label):
    text = str(tier_label)
    if "Tier 1" in text:
        css_class = "tier1"
    elif "Tier 2" in text:
        css_class = "tier2"
    elif "Tier 3" in text:
        css_class = "tier3"
    elif "Tier 4" in text:
        css_class = "tier4"
    else:
        css_class = "tier4"
    return f'<span class="badge {css_class}">{text}</span>'
def judgment_badge_html(judgment):
    text = str(judgment)
    if text == "Bad":
        css_class = "bad"
    elif text == "Good":
        css_class = "good"
    elif text == "IDK - Leaning Bad":
        css_class = "idk-bad"
    else:
        css_class = "idk-good"
    return f'<span class="badge {css_class}">{text}</span>'
def build_html_review_df(results_df):
    if results_df.empty:
        return pd.DataFrame()
    df = results_df.copy()
    df["priority_tier"] = pd.to_numeric(df.get("priority_tier"), errors="coerce")
    df["priority_score"] = pd.to_numeric(df.get("priority_score"), errors="coerce")
    df["overall_judgment"] = df.apply(build_overall_judgment, axis=1)
    df["tier_label"] = df["priority_tier"].apply(format_tier_label)
    display_cols = [
        "row_number",
        "product_event_id",
        "pe_pli_number",
        "tier_label",
        "priority_score",
        "overall_judgment",
        "concern_level",
        "reportable",
        "investigation_required",
        "coding_event_description_inconsistency",
        "coding_regulatory_decision_inconsistency",
        "coding_investigation_decision_inconsistency",
        "category_short_reason",
        "exact_inconsistency_found",
        "recommended_action",
        "country",
        "rfr_code",
        "fdp_code",
    ]
    display_cols = [c for c in display_cols if c in df.columns]
    df = df[display_cols].copy()
    df = df.rename(columns={
        "row_number": "Row Number",
        "product_event_id": "Product Event ID",
        "pe_pli_number": "PE - PLI #",
        "tier_label": "Tier",
        "priority_score": "Priority Score",
        "overall_judgment": "Overall Judgment",
        "concern_level": "Concern Level",
        "reportable": "Reportable",
        "investigation_required": "Investigation Required",
        "coding_event_description_inconsistency": "Event Description Inconsistency",
        "coding_regulatory_decision_inconsistency": "Regulatory Inconsistency",
        "coding_investigation_decision_inconsistency": "Investigation Inconsistency",
        "category_short_reason": "Short Reason",
        "exact_inconsistency_found": "Exact Inconsistency Found",
        "recommended_action": "Recommended Action",
        "country": "Country",
        "rfr_code": "RFR Code",
        "fdp_code": "FDP Code",
    })
    if "Tier" in df.columns:
        df["Tier"] = df["Tier"].apply(tier_badge_html)
    if "Overall Judgment" in df.columns:
        df["Overall Judgment"] = df["Overall Judgment"].apply(judgment_badge_html)
    return df
def render_html_table(df):
    if df.empty:
        st.info("No rows to display.")
        return
    html = df.to_html(index=False, escape=False, classes="review-table")
    st.markdown(f'<div class="review-table-wrapper">{html}</div>', unsafe_allow_html=True)
def build_clean_display_df(results_df):
    if results_df.empty:
        return pd.DataFrame()
    display_df = results_df.copy()
    if "priority_tier" in display_df.columns:
        display_df["priority_tier"] = pd.to_numeric(display_df["priority_tier"], errors="coerce")
    if "priority_score" in display_df.columns:
        display_df["priority_score"] = pd.to_numeric(display_df["priority_score"], errors="coerce")
    sort_cols = [c for c in ["priority_tier", "priority_score", "row_number"] if c in display_df.columns]
    if sort_cols:
        ascending = [True, False, True][:len(sort_cols)]
        display_df = display_df.sort_values(by=sort_cols, ascending=ascending, na_position="last").copy()
    preferred_columns = [
        "row_number",
        "product_event_id",
        "pe_pli_number",
        "complaint_indicator",
        "country",
        "product_description",
        "rfr_code",
        "fdp_code",
        "reportable",
        "investigation_required",
        "category_name",
        "priority_tier",
        "priority_score",
        "recommended_action",
        "category_short_reason",
        "exact_inconsistency_found",
        "category_detailed_reason",
        "concern_level",
        "layer2_flag",
        "inconsistency_count",
        "inconsistency_types",
        "coding_event_description_inconsistency",
        "coding_event_description_reason",
        "coding_regulatory_decision_inconsistency",
        "coding_regulatory_decision_reason",
        "coding_investigation_decision_inconsistency",
        "coding_investigation_decision_reason",
        "layer1_score",
        "layer1_flags",
        "layer1_reasons",
        "priority_reasons",
        "event_description",
        "investigation_summary",
        "success",
        "status_code",
    ]
    preferred_columns = [c for c in preferred_columns if c in display_df.columns]
    display_df = display_df[preferred_columns].copy()
    rename_map = {
        "row_number": "Row Number",
        "product_event_id": "Product Event ID",
        "pe_pli_number": "PE - PLI #",
        "complaint_indicator": "Complaint? - PE",
        "country": "Country - PE",
        "product_description": "Product Description - PE PLI",
        "rfr_code": "RFR Code",
        "fdp_code": "FDP Code",
        "reportable": "Reportable",
        "investigation_required": "Investigation Required",
        "category_name": "Category",
        "priority_tier": "Priority Tier",
        "priority_score": "Priority Score",
        "recommended_action": "Recommended Action",
        "category_short_reason": "Short Categorization Reason",
        "exact_inconsistency_found": "Exact Inconsistency Found",
        "category_detailed_reason": "Detailed Categorization Reason",
        "concern_level": "Concern Level",
        "layer2_flag": "Layer 2 Flag",
        "inconsistency_count": "Inconsistency Count",
        "inconsistency_types": "Inconsistency Types",
        "coding_event_description_inconsistency": "Event Description Inconsistency",
        "coding_event_description_reason": "Event Description Reason",
        "coding_regulatory_decision_inconsistency": "Regulatory Decision Inconsistency",
        "coding_regulatory_decision_reason": "Regulatory Decision Reason",
        "coding_investigation_decision_inconsistency": "Investigation Decision Inconsistency",
        "coding_investigation_decision_reason": "Investigation Decision Reason",
        "layer1_score": "Layer 1 Score",
        "layer1_flags": "Layer 1 Flags",
        "layer1_reasons": "Layer 1 Reasons",
        "priority_reasons": "Priority Reasons",
        "event_description": "Event Description - PE",
        "investigation_summary": "Summary of Investigation Results",
        "success": "API Success",
        "status_code": "Status Code",
    }
    return display_df.rename(columns=rename_map)
def build_tier_organization(results_df):
    if results_df is None or results_df.empty:
        return pd.DataFrame(), pd.DataFrame()
    organized_df = results_df.copy()
    if "priority_tier" not in organized_df.columns:
        organized_df["priority_tier"] = None
    if "priority_score" not in organized_df.columns:
        organized_df["priority_score"] = None
    if "concern_level" not in organized_df.columns:
        organized_df["concern_level"] = ""
    if "inconsistency_count" not in organized_df.columns:
        organized_df["inconsistency_count"] = 0
    if "row_number" not in organized_df.columns:
        organized_df["row_number"] = range(1, len(organized_df) + 1)
    organized_df["priority_tier"] = pd.to_numeric(
        organized_df["priority_tier"],
        errors="coerce"
    )
    organized_df["priority_score"] = pd.to_numeric(
        organized_df["priority_score"],
        errors="coerce"
    )
    organized_df["inconsistency_count"] = pd.to_numeric(
        organized_df["inconsistency_count"],
        errors="coerce"
    ).fillna(0)
    organized_df["row_number"] = pd.to_numeric(
        organized_df["row_number"],
        errors="coerce"
    )
    concern_rank_map = {
        "high": 1,
        "medium": 2,
        "low": 3,
        "": 4,
        "none": 4,
        "nan": 4,
    }
    organized_df["_concern_rank"] = (
        organized_df["concern_level"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(concern_rank_map)
        .fillna(4)
    )
    organized_df["_priority_tier_sort"] = organized_df["priority_tier"].fillna(999)
    organized_df["_priority_score_sort"] = organized_df["priority_score"].fillna(-999)
    organized_df["_row_number_sort"] = organized_df["row_number"].fillna(999999)
    organized_df = organized_df.sort_values(
        by=[
            "_priority_tier_sort",
            "_concern_rank",
            "_priority_score_sort",
            "inconsistency_count",
            "_row_number_sort",
        ],
        ascending=[
            True,
            True,
            False,
            False,
            True,
        ],
        na_position="last",
    ).reset_index(drop=True)
    organized_df["review_order"] = range(1, len(organized_df) + 1)
    organized_df["tier_review_rank"] = (
        organized_df
        .groupby("priority_tier", dropna=False)
        .cumcount() + 1
    )
    organized_df["tier_label"] = organized_df["priority_tier"].apply(format_tier_label)
    if "overall_judgment" not in organized_df.columns:
        organized_df["overall_judgment"] = organized_df.apply(build_overall_judgment, axis=1)
    tier_organization_summary_df = (
        organized_df
        .groupby(["priority_tier", "tier_label"], dropna=False)
        .agg(
            row_count=("row_number", "count"),
            avg_priority_score=("priority_score", "mean"),
            max_priority_score=("priority_score", "max"),
            min_priority_score=("priority_score", "min"),
            high_concern_count=(
                "concern_level",
                lambda x: (x.astype(str).str.strip().str.lower() == "high").sum()
            ),
            medium_concern_count=(
                "concern_level",
                lambda x: (x.astype(str).str.strip().str.lower() == "medium").sum()
            ),
            low_concern_count=(
                "concern_level",
                lambda x: (x.astype(str).str.strip().str.lower() == "low").sum()
            ),
            bad_count=(
                "overall_judgment",
                lambda x: (x.astype(str).str.strip() == "Bad").sum()
            ),
            idk_leaning_bad_count=(
                "overall_judgment",
                lambda x: (x.astype(str).str.strip() == "IDK - Leaning Bad").sum()
            ),
            idk_leaning_good_count=(
                "overall_judgment",
                lambda x: (x.astype(str).str.strip() == "IDK - Leaning Good").sum()
            ),
            good_count=(
                "overall_judgment",
                lambda x: (x.astype(str).str.strip() == "Good").sum()
            ),
        )
        .reset_index()
    )
    tier_organization_summary_df["avg_priority_score"] = (
        tier_organization_summary_df["avg_priority_score"].round(2)
    )
    tier_organization_summary_df = tier_organization_summary_df.rename(columns={
        "priority_tier": "Priority Tier",
        "tier_label": "Tier",
        "row_count": "Row Count",
        "avg_priority_score": "Average Priority Score",
        "max_priority_score": "Max Priority Score",
        "min_priority_score": "Min Priority Score",
        "high_concern_count": "High Concern Count",
        "medium_concern_count": "Medium Concern Count",
        "low_concern_count": "Low Concern Count",
        "bad_count": "Bad Count",
        "idk_leaning_bad_count": "IDK - Leaning Bad Count",
        "idk_leaning_good_count": "IDK - Leaning Good Count",
        "good_count": "Good Count",
    })
    organized_df = organized_df.drop(
        columns=[
            "_concern_rank",
            "_priority_tier_sort",
            "_priority_score_sort",
            "_row_number_sort",
        ],
        errors="ignore",
    )
    return organized_df, tier_organization_summary_df
def build_enhanced_tier_summary(results_df):
    if results_df.empty:
        return pd.DataFrame()
    working_df = results_df.copy()
    working_df["priority_tier"] = pd.to_numeric(working_df.get("priority_tier"), errors="coerce")
    working_df["priority_score"] = pd.to_numeric(working_df.get("priority_score"), errors="coerce")
    working_df["category_name"] = working_df["priority_tier"].map(TIER_LABELS)
    summary_df = (
        working_df.groupby(["priority_tier", "category_name"], dropna=False)
        .agg(
            complaint_count=("row_number", "count"),
            avg_priority_score=("priority_score", "mean"),
            high_concern_count=("concern_level", lambda x: (x.astype(str).str.lower() == "high").sum()),
            medium_concern_count=("concern_level", lambda x: (x.astype(str).str.lower() == "medium").sum()),
            low_concern_count=("concern_level", lambda x: (x.astype(str).str.lower() == "low").sum()),
            event_inconsistency_count=("coding_event_description_inconsistency", lambda x: (x.astype(str).str.lower() == "yes").sum()),
            regulatory_inconsistency_count=("coding_regulatory_decision_inconsistency", lambda x: (x.astype(str).str.lower() == "yes").sum()),
            investigation_inconsistency_count=("coding_investigation_decision_inconsistency", lambda x: (x.astype(str).str.lower() == "yes").sum()),
        )
        .reset_index()
    )
    summary_df["avg_priority_score"] = summary_df["avg_priority_score"].round(2)
    summary_df = summary_df.rename(columns={
        "priority_tier": "Priority Tier",
        "category_name": "Category",
        "complaint_count": "Complaint Count",
        "avg_priority_score": "Average Priority Score",
        "high_concern_count": "High Concern Count",
        "medium_concern_count": "Medium Concern Count",
        "low_concern_count": "Low Concern Count",
        "event_inconsistency_count": "Event Inconsistency Count",
        "regulatory_inconsistency_count": "Regulatory Inconsistency Count",
        "investigation_inconsistency_count": "Investigation Inconsistency Count",
    })
    return summary_df
def make_results_xlsx_bytes(
    results_df,
    preview_df,
    workbook_info,
    tier_summary_df=None,
    organized_results_df=None,
    clean_display_df=None,
    pretty_review_df=None,
):
    output = io.BytesIO()
    def write_sheet(writer, df, sheet_name):
        export_df = df.copy()
        for col in export_df.columns:
            export_df[col] = export_df[col].map(clean_excel_cell_value)
        export_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        worksheet = writer.sheets[sheet_name[:31]]
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        for col_idx, column_name in enumerate(export_df.columns, start=1):
            letter = worksheet.cell(row=1, column=col_idx).column_letter
            sample_values = export_df[column_name].head(50).tolist()
            max_len = max(
                [len(str(column_name))] +
                [len("" if pd.isna(v) else str(v)) for v in sample_values]
            )
            worksheet.column_dimensions[letter].width = min(max(max_len + 2, 12), 70)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame({"status": ["results workbook"]}).to_excel(writer, sheet_name="README", index=False)
        write_sheet(writer, results_df, "Model Results")
        if pretty_review_df is not None and not pretty_review_df.empty:
            write_sheet(writer, pretty_review_df, "Reviewer View")
        if clean_display_df is not None and not clean_display_df.empty:
            write_sheet(writer, clean_display_df, "Categorized Complaints")
        if organized_results_df is not None and not organized_results_df.empty:
            write_sheet(writer, organized_results_df, "Organized by Tier")
        if tier_summary_df is not None and not tier_summary_df.empty:
            write_sheet(writer, tier_summary_df, "Tier Summary")
        if organized_results_df is not None and not organized_results_df.empty:
            for tier in [1, 2, 3, 4]:
                tier_df = organized_results_df[
                    pd.to_numeric(organized_results_df["priority_tier"], errors="coerce") == tier
                ].copy()
                if not tier_df.empty:
                    tier_clean_df = build_clean_display_df(tier_df)
                    write_sheet(writer, tier_clean_df, f"Tier {tier}")
        write_sheet(writer, preview_df.drop(columns=["join_key"], errors="ignore"), "Input Preview")
        write_sheet(writer, pd.DataFrame(workbook_info), "Workbook Summary")
    output.seek(0)
    return output.getvalue()
def read_partial_results_workbook(uploaded):
    try:
        results_df = pd.read_excel(
            io.BytesIO(uploaded.getvalue()),
            sheet_name="Model Results",
            engine="openpyxl",
        )
    except ValueError as exc:
        raise ValueError(
            f"{uploaded.name} does not contain a 'Model Results' sheet. "
            "Please upload an XLSX exported by this tool."
        ) from exc
    required_columns = {"row_number", "success"}
    missing_columns = required_columns.difference(results_df.columns)
    if missing_columns:
        raise ValueError(
            f"{uploaded.name} is missing required result column(s): "
            f"{', '.join(sorted(missing_columns))}."
        )
    results_df = results_df.copy()
    results_df["row_number"] = pd.to_numeric(results_df["row_number"], errors="coerce")
    return results_df[results_df["row_number"].notna()].copy()
def read_embedded_input_workbook(uploaded):
    try:
        input_df = pd.read_excel(
            io.BytesIO(uploaded.getvalue()),
            sheet_name="Input Preview",
            engine="openpyxl",
            dtype=object,
        )
    except ValueError as exc:
        raise ValueError(
            f"{uploaded.name} does not contain an 'Input Preview' sheet. "
            "Upload the original raw complaint workbook with this older results workbook."
        ) from exc
    if input_df.empty:
        raise ValueError(f"{uploaded.name} contains an empty 'Input Preview' sheet.")
    input_df.columns = dedupe_columns(input_df.columns)
    required_columns = {"Product Event ID", "Event Description - PE"}
    missing_columns = required_columns.difference(input_df.columns)
    if missing_columns:
        raise ValueError(
            f"{uploaded.name}'s 'Input Preview' sheet is missing required input column(s): "
            f"{', '.join(sorted(missing_columns))}."
        )
    return {"Input Preview": pd.DataFrame(
        [input_df.columns.tolist(), *input_df.values.tolist()]
    )}
def is_success_value(value):
    return value is True or normalize_text(value) in {"true", "1", "yes"}
def has_http_200_response(row):
    status_code = pd.to_numeric(row.get("status_code"), errors="coerce")
    return pd.notna(status_code) and int(status_code) == 200
def successful_result_rows(results_df):
    if results_df is None or results_df.empty:
        return set()
    success_mask = results_df.apply(has_http_200_response, axis=1)
    return set(
        pd.to_numeric(results_df.loc[success_mask, "row_number"], errors="coerce")
        .dropna().astype(int).tolist()
    )
def merge_result_frames(*frames):
    usable_frames = [frame.copy() for frame in frames if frame is not None and not frame.empty]
    if not usable_frames:
        return pd.DataFrame()
    combined = pd.concat(usable_frames, ignore_index=True, sort=False)
    combined["row_number"] = pd.to_numeric(combined["row_number"], errors="coerce")
    combined = combined[combined["row_number"].notna()].copy()
    combined["_successful"] = combined.apply(has_http_200_response, axis=1)    
    combined = combined.sort_values("_successful", kind="stable")
    combined = combined.drop_duplicates(subset=["row_number"], keep="last")
    return combined.drop(columns=["_successful"]).sort_values("row_number").reset_index(drop=True)
def save_processing_checkpoint(results, preview_df, workbook_info):
    results_df = pd.DataFrame(results)
    organized_results_df, _ = build_tier_organization(results_df)
    clean_display_df = build_clean_display_df(organized_results_df)
    tier_summary_df = build_enhanced_tier_summary(organized_results_df)
    pretty_review_df = build_pretty_review_df(organized_results_df)
    st.session_state.processed_results = results_df
    st.session_state.processed_preview_df = preview_df
    st.session_state.processed_workbook_info = workbook_info
    st.session_state.processed_tier_summary_df = tier_summary_df
    st.session_state.processed_organized_results_df = organized_results_df
    st.session_state.processed_clean_display_df = clean_display_df
    st.session_state.processed_pretty_review_df = pretty_review_df
    st.session_state.processed_html_review_df = build_html_review_df(organized_results_df)
    st.session_state.processed_results_xlsx = make_results_xlsx_bytes(
        results_df=results_df,
        preview_df=preview_df,
        workbook_info=workbook_info,
        tier_summary_df=tier_summary_df,
        organized_results_df=organized_results_df,
        clean_display_df=clean_display_df,
        pretty_review_df=pretty_review_df,
    )
def render_saved_results():
    if st.session_state.processed_organized_results_df is None:
        return
    organized_results_df = st.session_state.processed_organized_results_df
    clean_display_df = st.session_state.processed_clean_display_df
    tier_summary_df = st.session_state.processed_tier_summary_df
    st.markdown('<div class="pretty-section"></div>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Rows", len(organized_results_df))
    col2.metric("Tier 1", count_by_tier(organized_results_df, 1))
    col3.metric("Tier 2", count_by_tier(organized_results_df, 2))
    col4.metric("Tier 3", count_by_tier(organized_results_df, 3))
    col5.metric("Tier 4", count_by_tier(organized_results_df, 4))
    tab1, tab2, tab3 = st.tabs(["Overview", "Tiered Review", "Raw Results"])
    with tab1:
        st.subheader("Tier Summary")
        st.dataframe(tier_summary_df, use_container_width=True)
        st.subheader("Review Table")
        st.markdown(
            '<div class="small-note">Compact reviewer-friendly view with color-coded tiers and judgments.</div>',
            unsafe_allow_html=True
        )
        tier_filter = st.multiselect(
            "Filter by Tier",
            options=list(TIER_LABELS.values()),
            default=[],
            key="overview_tier_filter"
        )
        filtered_base_df = organized_results_df.copy()
        if tier_filter:
            allowed_tiers = [
                tier_num for tier_num, tier_name in TIER_LABELS.items()
                if tier_name in tier_filter
            ]
            filtered_base_df = filtered_base_df[
                pd.to_numeric(filtered_base_df["priority_tier"], errors="coerce").isin(allowed_tiers)
            ].copy()
        filtered_html_df = build_html_review_df(filtered_base_df)
        render_html_table(filtered_html_df)
    with tab2:
        for tier in [1, 2, 3, 4]:
            tier_raw_df = organized_results_df[
                pd.to_numeric(organized_results_df["priority_tier"], errors="coerce") == tier
            ].copy()
            if not tier_raw_df.empty:
                tier_name = TIER_LABELS.get(tier, f"Tier {tier}")
                st.subheader(tier_name)
                tier_html_df = build_html_review_df(tier_raw_df)
                render_html_table(tier_html_df)
    with tab3:
        st.subheader("Full Raw Categorized Output")
        st.markdown(
            '<div class="small-note">This includes all detailed fields used for traceability and debugging.</div>',
            unsafe_allow_html=True
        )
        st.dataframe(clean_display_df, use_container_width=True, height=600)
    if st.session_state.processed_results_xlsx is not None:
        st.download_button(
            "Download results workbook as XLSX",
            data=st.session_state.processed_results_xlsx,
            file_name="mdtgpt_raw_model_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="persistent_download_button"
        )
if uploaded_files:
    try:
        uploaded_file = None
        raw_workbook = None
        reader_name = None
        partial_result_files = []
        for candidate_file in uploaded_files:
            candidate_bytes = io.BytesIO(candidate_file.getvalue())
            candidate_excel = pd.ExcelFile(candidate_bytes, engine="openpyxl")
            if "Model Results" in candidate_excel.sheet_names:
                partial_result_files.append(candidate_file)
                continue
            candidate_workbook, candidate_reader = read_workbook_as_raw_dataframes(candidate_file)
            has_main_sheet = any(
                infer_sheet_role(sheet_name, prepare_sheet_dataframe(raw_df)) == "main"
                for sheet_name, raw_df in candidate_workbook.items()
            )
            if has_main_sheet:
                if uploaded_file is not None:
                    raise ValueError(
                        "More than one raw complaint workbook was uploaded. Upload one raw "
                        "workbook plus any number of results workbooks."
                    )
                uploaded_file = candidate_file
                raw_workbook = candidate_workbook
                reader_name = candidate_reader
            else:
                raise ValueError(
                    f"{candidate_file.name} is neither a raw complaint workbook nor a "
                    "results workbook exported by this tool."
                )
        if uploaded_file is None:
            if not partial_result_files:
                raise ValueError("Upload a raw complaint workbook or an exported results workbook.")
            uploaded_file = partial_result_files[0]
            raw_workbook = read_embedded_input_workbook(uploaded_file)
            reader_name = "embedded Input Preview"
        current_uploaded_fingerprint = hashlib.sha256(uploaded_file.getvalue()).hexdigest()
        if st.session_state.last_uploaded_fingerprint != current_uploaded_fingerprint:
            st.session_state.processed_results = None
            st.session_state.processed_preview_df = None
            st.session_state.processed_workbook_info = None
            st.session_state.processed_tier_summary_df = None
            st.session_state.processed_organized_results_df = None
            st.session_state.processed_clean_display_df = None
            st.session_state.processed_pretty_review_df = None
            st.session_state.processed_html_review_df = None
            st.session_state.processed_results_xlsx = None
            st.session_state.loaded_partial_fingerprints = set()
            st.session_state.last_uploaded_filename = uploaded_file.name
            st.session_state.last_uploaded_fingerprint = current_uploaded_fingerprint
        main_sheet_name = None
        workbook_info = []
        processed_sheets = {}
        for sheet_name, raw_df in raw_workbook.items():
            df = prepare_sheet_dataframe(raw_df)
            role = infer_sheet_role(sheet_name, df)
            processed_sheets[sheet_name] = {"role": role, "df": df}
            if role == "main" and main_sheet_name is None:
                main_sheet_name = sheet_name
            workbook_info.append({
                "sheet_name": sheet_name,
                "role": role,
                "rows_after_header": len(df),
                "columns": ", ".join(df.columns.astype(str).tolist()),
            })
        st.subheader("Workbook Summary")
        st.write(f"Workbook reader: {reader_name}")
        st.dataframe(pd.DataFrame(workbook_info), use_container_width=True)
        if main_sheet_name is None:
            st.error("Could not identify a raw main sheet containing Product Event ID and Event Description - PE.")
            st.stop()
        main_df = ensure_key_columns(processed_sheets[main_sheet_name]["df"])
        main_df = add_join_key(main_df)
        main_df = main_df[main_df["join_key"].notna() & (main_df["join_key"].astype(str) != "")].copy()
        related_pli_lookup = build_related_pli_lookup(main_df)
        preview_df = main_df.copy()
        st.subheader("Main Sheet Preview")
        st.dataframe(preview_df.head(10).drop(columns=["join_key"], errors="ignore"), use_container_width=True)
        st.write(f"Main sheet: {main_sheet_name}")
        st.write(f"Main rows found: {len(main_df)}")
        st.write(f"Model endpoint: `{get_model_endpoint()}`")
        newly_loaded_partials = []
        for partial_file in partial_result_files:
            partial_fingerprint = hashlib.sha256(partial_file.getvalue()).hexdigest()
            if partial_fingerprint in st.session_state.loaded_partial_fingerprints:
                continue
            partial_df = read_partial_results_workbook(partial_file)
            valid_row_numbers = set((main_df.index + 1).astype(int).tolist())
            partial_df = partial_df[
                partial_df["row_number"].astype(int).isin(valid_row_numbers)
            ].copy()
            newly_loaded_partials.append(partial_df)
            st.session_state.loaded_partial_fingerprints.add(partial_fingerprint)
        if newly_loaded_partials:
            st.session_state.processed_results = merge_result_frames(
                st.session_state.processed_results,
                *newly_loaded_partials,
            )
            save_processing_checkpoint(
                st.session_state.processed_results.to_dict("records"),
                preview_df,
                workbook_info,
            )
            st.success(
                f"Loaded {len(newly_loaded_partials)} partial workbook(s). "
                "Successful rows will not be sent again."
            )
        previous_results = st.session_state.processed_results
        completed_row_numbers = successful_result_rows(previous_results)
        all_row_numbers = set((main_df.index + 1).astype(int).tolist())
        missing_row_numbers = all_row_numbers.difference(completed_row_numbers)
        failed_row_numbers = set()
        if previous_results is not None and not previous_results.empty:
            failed_mask = ~previous_results.apply(has_http_200_response, axis=1)
            failed_row_numbers = set(
                pd.to_numeric(previous_results.loc[failed_mask, "row_number"], errors="coerce")
                .dropna().astype(int).tolist()
            )
        retry_only_failed = st.checkbox(
            "Retry only failed rows from the saved run",
            value=bool(failed_row_numbers),
            disabled=not failed_row_numbers,
            help="Keeps successful results and sends only rows that previously failed.",
        )
        automatic_retry_failed = st.checkbox(
            "Automatically retry failed rows at the end",
            value=False,
            help="Leave this off to avoid a long-running retry cycle. Failed rows can be retried later.",
        )
        batch_size = st.number_input(
            "Rows to process before pausing",
            min_value=1,
            max_value=max(1, len(main_df)),
            value=min(25, max(1, len(missing_row_numbers))),
            help=(
                "The run automatically pauses after this many rows. A downloadable "
                "checkpoint is rebuilt after every row, so you can safely stop between batches."
            ),
        )
        st.info(
            f"{len(completed_row_numbers)} row(s) complete; "
            f"{len(missing_row_numbers)} row(s) remain."
        )
        button_label = (
            f"Retry {len(failed_row_numbers)} failed row(s)"
            if retry_only_failed and failed_row_numbers
            else f"Process next {min(int(batch_size), len(missing_row_numbers))} row(s)"
        )
        if st.button(button_label, disabled=not missing_row_numbers):
            errors = []
            if selected_portfolio == "Select Portfolio":
                errors.append("Please select a Portfolio.")
            if selected_ou == "Select OU":
                errors.append("Please select an Operating Unit (OU).")
            if not base_models_url:
                errors.append("Please enter the MDTGPT Models Base URL.")
            if not model_id:
                errors.append("Please enter the Model ID.")
            if not bearer_token:
                errors.append("Please enter a Bearer Token.")
            if errors:
                for error in errors:
                    st.error(error)
                st.stop()
            session = requests.Session()
            rows_to_run = failed_row_numbers if retry_only_failed and failed_row_numbers else missing_row_numbers
            run_df = main_df[
                pd.Series(main_df.index + 1, index=main_df.index).isin(rows_to_run)
            ].head(int(batch_size)).copy()
            results = [] if previous_results is None else previous_results.to_dict("records")
            selected_row_numbers = set((run_df.index + 1).astype(int).tolist())
            if previous_results is not None and not previous_results.empty:
                results = previous_results[
                    ~pd.to_numeric(previous_results["row_number"], errors="coerce")
                    .isin(selected_row_numbers)
                ].to_dict("records")
            failed_rows = []
            success_count = sum(is_success_value(record.get("success")) for record in results)
            failure_count = sum(not is_success_value(record.get("success")) for record in results)
            progress = st.progress(0)
            status_box = st.empty()
            for processed_index, (idx, row) in enumerate(run_df.iterrows(), start=1):
                row_number = int(idx) + 1
                row_dict = clean_row(row.drop(labels=["join_key"], errors="ignore").to_dict())
                complaint_record = add_related_plis(
                    build_complaint_record(row_dict=row_dict, row_number=row_number),
                    row_dict=row_dict,
                    related_pli_lookup=related_pli_lookup,
                )
                layer1_result = layer1_rule_based_screening(
                    row_dict=row_dict,
                    related_plis=complaint_record["relatedPlis"],
                )
                request_json = build_model_request_json(complaint_record)
                try:
                    response = send_row_to_model(
                        session=session,
                        token=bearer_token,
                        complaint_record=complaint_record,
                        timeout=int(timeout_seconds),
                        attempts=3,
                        wait_seconds=2,
                    )
                    if not response.ok:
                        raise RuntimeError(
                        f"MDTGPT returned HTTP {response.status_code} for Excel row "
                        f"{row_number}: {response.text[:1500]}"
                    )
                    result_record = {
                        "row_number": row_number,
                        "product_event_id": row_dict.get("Product Event ID"),
                        "pe_pli_number": row_dict.get("PE - PLI #"),
                        "complaint_indicator": row_dict.get("Complaint? - PE"),
                        "country": get_country_value(row_dict),
                        "product_description": row_dict.get("Product Description - PE PLI"),
                        "rfr_code": row_dict.get("RFR Code"),
                        "fdp_code": row_dict.get("FDP Code"),
                        "reportable": row_dict.get("Reportable?"),
                        "investigation_required": row_dict.get("Investigation Required?"),
                        "event_description": row_dict.get("Event Description - PE"),
                        "investigation_summary": row_dict.get("Summary of Investigation Results"),
                        "status_code": response.status_code,
                        "success": response.ok,
                        "model_endpoint": get_model_endpoint(),
                        "request_json": json.dumps(request_json, ensure_ascii=False, default=str),
                        "complaint_record_json": json.dumps(complaint_record, ensure_ascii=False, default=str),
                        "layer1_flags": " | ".join(layer1_result["layer1_flags"]),
                        "layer1_reasons": " | ".join(layer1_result["layer1_reasons"]),
                        "layer1_score": layer1_result["layer1_score"],
                    }
                    try:
                        response_body = response.json()
                    except Exception:
                        response_body = response.text
                    model_content = extract_model_content(response_body)
                    layer2_result = parse_layer2_response(response_body)
                    layer3_result = layer3_prioritization(layer1_result, layer2_result)
                    categorization_result = build_clear_categorization(
                        layer1_result=layer1_result,
                        layer2_result=layer2_result,
                        layer3_result=layer3_result,
                        row_dict=row_dict,
                    )
                    result_record["response_body"] = (
                        json.dumps(response_body, ensure_ascii=False, default=str)
                        if isinstance(response_body, dict)
                        else response_body
                    )
                    result_record["model_content"] = model_content
                    result_record["coding_event_description_inconsistency"] = layer2_result.get("coding_event_description_inconsistency")
                    result_record["coding_event_description_reason"] = layer2_result.get("coding_event_description_reason")
                    result_record["coding_regulatory_decision_inconsistency"] = layer2_result.get("coding_regulatory_decision_inconsistency")
                    result_record["coding_regulatory_decision_reason"] = layer2_result.get("coding_regulatory_decision_reason")
                    result_record["coding_investigation_decision_inconsistency"] = layer2_result.get("coding_investigation_decision_inconsistency")
                    result_record["coding_investigation_decision_reason"] = layer2_result.get("coding_investigation_decision_reason")
                    result_record["layer2_flag"] = layer2_result.get("layer2_flag")
                    result_record["concern_level"] = layer2_result.get("concern_level")
                    result_record["layer2_reason"] = layer2_result.get("layer2_reason")
                    result_record["priority_tier"] = layer3_result["priority_tier"]
                    result_record["priority_score"] = layer3_result["priority_score"]
                    result_record["priority_reasons"] = " | ".join(layer3_result["priority_reasons"])
                    result_record["category_name"] = categorization_result["category_name"]
                    result_record["category_short_reason"] = categorization_result["category_short_reason"]
                    result_record["category_detailed_reason"] = categorization_result["category_detailed_reason"]
                    result_record["recommended_action"] = categorization_result["recommended_action"]
                    result_record["inconsistency_count"] = categorization_result["inconsistency_count"]
                    result_record["inconsistency_types"] = categorization_result["inconsistency_types"]
                    result_record["exact_inconsistency_found"] = build_exact_inconsistency_found(layer2_result, row_dict)
                    if response.ok:
                        success_count += 1
                    else:
                        failure_count += 1
                    results.append(result_record)
                except Exception as e:
                    failure_count += 1
                    results.append({
                        "row_number": row_number,
                        "product_event_id": row_dict.get("Product Event ID"),
                        "pe_pli_number": row_dict.get("PE - PLI #"),
                        "complaint_indicator": row_dict.get("Complaint? - PE"),
                        "country": get_country_value(row_dict),
                        "product_description": row_dict.get("Product Description - PE PLI"),
                        "rfr_code": row_dict.get("RFR Code"),
                        "fdp_code": row_dict.get("FDP Code"),
                        "reportable": row_dict.get("Reportable?"),
                        "investigation_required": row_dict.get("Investigation Required?"),
                        "event_description": row_dict.get("Event Description - PE"),
                        "investigation_summary": row_dict.get("Summary of Investigation Results"),
                        "status_code": None,
                        "success": False,
                        "model_endpoint": get_model_endpoint(),
                        "request_json": json.dumps(request_json, ensure_ascii=False, default=str),
                        "complaint_record_json": json.dumps(complaint_record, ensure_ascii=False, default=str),
                        "response_body": str(e),
                        "model_content": None,
                        "layer1_flags": " | ".join(layer1_result["layer1_flags"]),
                        "layer1_reasons": " | ".join(layer1_result["layer1_reasons"]),
                        "layer1_score": layer1_result["layer1_score"],
                        "coding_event_description_inconsistency": None,
                        "coding_event_description_reason": None,
                        "coding_regulatory_decision_inconsistency": None,
                        "coding_regulatory_decision_reason": None,
                        "coding_investigation_decision_inconsistency": None,
                        "coding_investigation_decision_reason": None,
                        "layer2_flag": None,
                        "concern_level": None,
                        "layer2_reason": None,
                        "priority_tier": None,
                        "priority_score": None,
                        "priority_reasons": "API call failed before Layer 3",
                        "category_name": "Uncategorized - API Failure",
                        "category_short_reason": "The product event could not be categorized because the API call failed.",
                        "category_detailed_reason": (
                            "The product event could not be categorized because the model call failed "
                            f"before Layer 2 and Layer 3 outputs were produced. Error: {str(e)}"
                        ),
                        "recommended_action": "Manual review required",
                        "inconsistency_count": None,
                        "inconsistency_types": None,
                        "exact_inconsistency_found": None,
                    })
                    failed_rows.append({
                        "row_number": row_number,
                        "row_dict": row_dict,
                        "complaint_record": complaint_record,
                        "request_json": request_json,
                    })
                save_processing_checkpoint(results, preview_df, workbook_info)
                percent_complete = int((processed_index / len(run_df)) * 100)
                progress.progress(percent_complete)
                status_box.write(
                    f"Processed {processed_index}/{len(run_df)} rows. "
                    f"Success: {success_count}, Failed: {failure_count}"
                )
            if failed_rows and automatic_retry_failed:
                st.write(f"Retrying {len(failed_rows)} failed rows...")
                retry_session = requests.Session()
                retry_success_count = 0
                retry_failure_count = 0
                for failed_item in failed_rows:
                    row_number = failed_item["row_number"]
                    row_dict = failed_item["row_dict"]
                    complaint_record = failed_item["complaint_record"]
                    request_json = failed_item["request_json"]
                    try:
                        response = send_row_to_model(
                            session=retry_session,
                            token=bearer_token,
                            complaint_record=complaint_record,
                            timeout=int(timeout_seconds),
                            attempts=5,
                            wait_seconds=5,
                        )
                        if not response.ok:
                            retry_failure_count += 1
                            continue
                        try:
                            response_body = response.json()
                        except Exception:
                            response_body = response.text
                        model_content = extract_model_content(response_body)
                        layer2_result = parse_layer2_response(response_body)
                        layer1_result = layer1_rule_based_screening(
                            row_dict=row_dict,
                            related_plis=complaint_record.get("relatedPlis", []),
                        )
                        layer3_result = layer3_prioritization(layer1_result, layer2_result)
                        categorization_result = build_clear_categorization(
                            layer1_result=layer1_result,
                            layer2_result=layer2_result,
                            layer3_result=layer3_result,
                            row_dict=row_dict,
                        )
                        result_record = {
                            "row_number": row_number,
                            "product_event_id": row_dict.get("Product Event ID"),
                            "pe_pli_number": row_dict.get("PE - PLI #"),
                            "complaint_indicator": row_dict.get("Complaint? - PE"),
                            "country": get_country_value(row_dict),
                            "product_description": row_dict.get("Product Description - PE PLI"),
                            "rfr_code": row_dict.get("RFR Code"),
                            "fdp_code": row_dict.get("FDP Code"),
                            "reportable": row_dict.get("Reportable?"),
                            "investigation_required": row_dict.get("Investigation Required?"),
                            "event_description": row_dict.get("Event Description - PE"),
                            "investigation_summary": row_dict.get("Summary of Investigation Results"),
                            "status_code": response.status_code,
                            "success": response.ok,
                            "model_endpoint": get_model_endpoint(),
                            "request_json": json.dumps(request_json, ensure_ascii=False, default=str),
                            "complaint_record_json": json.dumps(complaint_record, ensure_ascii=False, default=str),
                            "layer1_flags": " | ".join(layer1_result["layer1_flags"]),
                            "layer1_reasons": " | ".join(layer1_result["layer1_reasons"]),
                            "layer1_score": layer1_result["layer1_score"],
                            "response_body": (
                                json.dumps(response_body, ensure_ascii=False, default=str)
                                if isinstance(response_body, dict)
                                else response_body
                            ),
                            "model_content": model_content,
                            "coding_event_description_inconsistency": layer2_result.get("coding_event_description_inconsistency"),
                            "coding_event_description_reason": layer2_result.get("coding_event_description_reason"),
                            "coding_regulatory_decision_inconsistency": layer2_result.get("coding_regulatory_decision_inconsistency"),
                            "coding_regulatory_decision_reason": layer2_result.get("coding_regulatory_decision_reason"),
                            "coding_investigation_decision_inconsistency": layer2_result.get("coding_investigation_decision_inconsistency"),
                            "coding_investigation_decision_reason": layer2_result.get("coding_investigation_decision_reason"),
                            "layer2_flag": layer2_result.get("layer2_flag"),
                            "concern_level": layer2_result.get("concern_level"),
                            "layer2_reason": layer2_result.get("layer2_reason"),
                            "priority_tier": layer3_result["priority_tier"],
                            "priority_score": layer3_result["priority_score"],
                            "priority_reasons": " | ".join(layer3_result["priority_reasons"]),
                            "category_name": categorization_result["category_name"],
                            "category_short_reason": categorization_result["category_short_reason"],
                            "category_detailed_reason": categorization_result["category_detailed_reason"],
                            "recommended_action": categorization_result["recommended_action"],
                            "inconsistency_count": categorization_result["inconsistency_count"],
                            "inconsistency_types": categorization_result["inconsistency_types"],
                            "exact_inconsistency_found": build_exact_inconsistency_found(layer2_result, row_dict),
                        }
                        for i, rec in enumerate(results):
                            if rec.get("row_number") == row_number:
                                results[i] = result_record
                                break
                        failure_count -= 1
                        success_count += 1
                        retry_success_count += 1
                    except Exception as retry_error:
                        retry_failure_count += 1
                        st.write(f"Row {row_number} still failed on retry: {retry_error}")
                st.write(
                    f"Retry complete. Retry successes: {retry_success_count}, "
                    f"Retry failures: {retry_failure_count}"
                )
            st.subheader("Summary")
            st.write(f"Successful rows: {success_count}")
            st.write(f"Failed rows: {failure_count}")
            results_df = pd.DataFrame(results)
            organized_results_df, _ = build_tier_organization(results_df)
            clean_display_df = build_clean_display_df(organized_results_df)
            tier_summary_df = build_enhanced_tier_summary(organized_results_df)
            pretty_review_df = build_pretty_review_df(organized_results_df)
            html_review_df = build_html_review_df(organized_results_df)
            results_xlsx = make_results_xlsx_bytes(
                results_df=results_df,
                preview_df=preview_df,
                workbook_info=workbook_info,
                tier_summary_df=tier_summary_df,
                organized_results_df=organized_results_df,
                clean_display_df=clean_display_df,
                pretty_review_df=pretty_review_df,
            )
            st.session_state.processed_results = results_df
            st.session_state.processed_preview_df = preview_df
            st.session_state.processed_workbook_info = workbook_info
            st.session_state.processed_tier_summary_df = tier_summary_df
            st.session_state.processed_organized_results_df = organized_results_df
            st.session_state.processed_clean_display_df = clean_display_df
            st.session_state.processed_pretty_review_df = pretty_review_df
            st.session_state.processed_html_review_df = html_review_df
            st.session_state.processed_results_xlsx = results_xlsx
            remaining_count = len(all_row_numbers.difference(successful_result_rows(results_df)))
            if remaining_count:
                st.success(
                    f"Checkpoint saved. Processing is paused with {remaining_count} row(s) remaining. "
                    "Download the workbook below or process another batch when ready."
                )
            else:
                st.success("All rows are complete and the final workbook is ready to download.")
        render_saved_results()
    except Exception as e:
        st.error(f"Failed to read or process the workbook: {e}")
        st.exception(e)