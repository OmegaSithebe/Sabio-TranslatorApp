"""
utils/excel_reader.py

In-place XLSX translation via the shared-string table.

Speed approach
--------------
All unique strings from xl/sharedStrings.xml are collected, passed to
translate_many() in one batched+parallel call, then written back.
Cell formatting, borders, merged cells, formulas, and charts are untouched.
"""

import io
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Callable, Optional

for _pfx, _uri in {
    "":       "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r":      "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "mc":     "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "x14ac":  "http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac",
    "xr":     "http://schemas.microsoft.com/office/spreadsheetml/2014/revision",
}.items():
    try:
        ET.register_namespace(_pfx, _uri)
    except Exception:
        pass

_SS   = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_SI   = f"{{{_SS}}}si"
_T    = f"{{{_SS}}}t"
_RPH  = f"{{{_SS}}}rPh"
_IS   = f"{{{_SS}}}is"
_XSPACE = "{http://www.w3.org/XML/1998/namespace}space"


# ══════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════

def extract_excel_text(file) -> Optional[str]:
    """Return flat text for language detection only."""
    try:
        import pandas as pd
        file.seek(0)
        xf    = pd.ExcelFile(file)
        parts = []
        for sheet in xf.sheet_names:
            file.seek(0)
            df = pd.read_excel(file, sheet_name=sheet, dtype=str).fillna("")
            for col in df.columns:
                if str(col).strip():
                    parts.append(str(col))
            for _, row in df.iterrows():
                for val in row:
                    if str(val).strip():
                        parts.append(str(val))
        return "\n".join(parts)
    except Exception as exc:
        raise RuntimeError(f"Could not read Excel file: {exc}") from exc


def translate_xlsx_inplace(
    file,
    translate_fn:      Callable[[str], Optional[str]],
    translate_many_fn: Optional[Callable[[list[str]], dict[str, str]]] = None,
) -> Optional[io.BytesIO]:
    """
    Translate only the text in an XLSX; all formatting is preserved.

    Parameters
    ----------
    file              : Seekable uploaded file (.xlsx).
    translate_fn      : Single-string fallback.
    translate_many_fn : Fast path — takes list[str], returns dict.
    """
    try:
        file.seek(0)
        raw = file.read()
    except Exception as exc:
        raise RuntimeError(f"Could not read file: {exc}") from exc

    if raw[:2] == b"\xd0\xcf":
        raise RuntimeError(
            "Legacy .xls files cannot be translated in-place (binary format). "
            "Open in Excel, save as .xlsx, then re-upload."
        )

    try:
        src = zipfile.ZipFile(io.BytesIO(raw), "r")
    except Exception as exc:
        raise RuntimeError(f"File does not appear to be a valid XLSX: {exc}") from exc

    # ── Pass 1: parse shared strings, collect all translatable strings ────
    ss_data: Optional[bytes]       = None
    ss_root: Optional[ET.Element]  = None
    ss_decl: str                   = ""
    all_texts: list[str]           = []

    if "xl/sharedStrings.xml" in src.namelist():
        ss_data          = src.read("xl/sharedStrings.xml")
        ss_xml           = ss_data.decode("utf-8")
        ss_decl, ss_body = _split_decl(ss_xml)
        ss_root          = ET.fromstring(ss_body)
        for si in ss_root.iter(_SI):
            t = _si_text(si)
            if t:
                all_texts.append(t)

    # Also collect inline strings from sheet XML
    sheet_parts: dict[str, tuple[ET.Element, str, bytes]] = {}
    for name in src.namelist():
        if re.match(r"xl/worksheets/sheet\d+\.xml$", name):
            raw_xml      = src.read(name)
            xml_str      = raw_xml.decode("utf-8")
            decl, body   = _split_decl(xml_str)
            root         = ET.fromstring(body)
            sheet_parts[name] = (root, decl, raw_xml)
            for is_node in root.iter(_IS):
                t = _node_text(is_node)
                if t:
                    all_texts.append(t)

    # ── Pass 2: batch-translate all unique strings ─────────────────────────
    unique = list(dict.fromkeys(all_texts))
    if translate_many_fn and unique:
        translations = translate_many_fn(unique)
    else:
        translations = {t: (translate_fn(t) or t) for t in unique}

    # ── Pass 3: write back and repack ─────────────────────────────────────
    out_buf = io.BytesIO()
    with zipfile.ZipFile(out_buf, "w", compression=zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)

            if item.filename == "xl/sharedStrings.xml" and ss_root is not None:
                for si in ss_root.iter(_SI):
                    _apply_si(si, translations)
                xml_out = ss_decl + ET.tostring(ss_root, encoding="unicode",
                                                xml_declaration=False)
                data = xml_out.encode("utf-8")

            elif item.filename in sheet_parts:
                root, decl, _ = sheet_parts[item.filename]
                for is_node in root.iter(_IS):
                    _apply_inline(is_node, translations)
                xml_out = decl + ET.tostring(root, encoding="unicode",
                                             xml_declaration=False)
                data = xml_out.encode("utf-8")

            dst.writestr(item, data)

    src.close()
    out_buf.seek(0)
    return out_buf


# ══════════════════════════════════════════════════════════════════════════
# Internal helpers
# ══════════════════════════════════════════════════════════════════════════

def _si_text(si: ET.Element) -> str:
    """Return combined text of <si>, excluding phonetic runs."""
    parts = []
    for t in si.iter(_T):
        if not _inside_rph(si, t):
            parts.append(t.text or "")
    text = "".join(parts).strip()
    return text if text and not _skip(text) else ""


def _node_text(node: ET.Element) -> str:
    parts = [t.text or "" for t in node.iter(_T)]
    text  = "".join(parts).strip()
    return text if text and not _skip(text) else ""


def _apply_si(si: ET.Element, translations: dict[str, str]) -> None:
    t_nodes = [t for t in si.iter(_T) if not _inside_rph(si, t)]
    if not t_nodes:
        return
    original = "".join(t.text or "" for t in t_nodes).strip()
    translated = translations.get(original, "")
    if not translated or translated.strip() == original:
        return
    t_nodes[0].text = translated
    _set_space(t_nodes[0], translated)
    for t in t_nodes[1:]:
        t.text = ""
        t.attrib.pop(_XSPACE, None)


def _apply_inline(is_node: ET.Element, translations: dict[str, str]) -> None:
    t_nodes = list(is_node.iter(_T))
    if not t_nodes:
        return
    original = "".join(t.text or "" for t in t_nodes).strip()
    translated = translations.get(original, "")
    if not translated or translated.strip() == original:
        return
    t_nodes[0].text = translated
    _set_space(t_nodes[0], translated)
    for t in t_nodes[1:]:
        t.text = ""


def _inside_rph(root: ET.Element, target: ET.Element) -> bool:
    stack = [(root, False)]
    while stack:
        node, in_rph = stack.pop()
        if node is target:
            return in_rph
        for child in node:
            stack.append((child, in_rph or node.tag == _RPH))
    return False


def _set_space(node: ET.Element, text: str) -> None:
    if text and (text[0] == " " or text[-1] == " "):
        node.set(_XSPACE, "preserve")
    else:
        node.attrib.pop(_XSPACE, None)


def _split_decl(xml: str):
    if xml.startswith("<?xml"):
        idx = xml.index("?>") + 2
        return xml[:idx], xml[idx:]
    return "", xml


def _skip(text: str) -> bool:
    if len(text) <= 1:
        return True
    if re.fullmatch(r"[\d\s.,\-/\\:;()+%$€£@#&*=<>_|~`'\"!?]+", text):
        return True
    if re.match(r"https?://\S+", text):
        return True
    return False


def is_excel_file(filename: str) -> bool:
    return filename.lower().endswith((".xlsx", ".xls", ".xlsm"))
