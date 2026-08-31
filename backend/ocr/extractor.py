import re
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

_reader = None

def _get_reader():
    global _reader
    if _reader is False:
        return False
    if _reader is not None:
        return _reader
    try:
        import easyocr
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    except Exception:
        _reader = False
    return _reader

def _preprocess(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Could not read image. It may be corrupted or unsupported.")
    h, w = img.shape[:2]
    if min(h, w) < 900:
        scale = 2
        img = cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.fastNlMeansDenoising(gray, h=10)

# IMPORTANT: order matters. More specific / narrower labels MUST come before
# broader labels that share the same keyword (e.g. "Highest Kills" and
# "Headshot Kills" both contain "kills", so they must be resolved — and their
# label+value boxes marked as consumed — before the generic "Total_Kills"
# pattern (bare "\bkills?\b") gets a turn. Same logic applies to
# Avg_Damage_Per_Match vs. Total_Damage ("damage" is generic).
PARSERS: List[Tuple[str, str, Any, str]] = [
    # --- specific / compound labels first ---
    (r"\bhighest\s*(?:kills?|eliminations?)\b|\bmost\s*eliminations?\b", r"(\d[\d,]*)", lambda x: int(x.replace(",", "")), "Highest_Kills_Single_Match"),
    (r"\bhighest\s*damage\b", r"([\d,]+(?:\.\d+)?)", lambda x: float(x.replace(",", "")), "Highest_Damage_Single_Match"),
    (r"\bheadshot\s*kills?\b|\bheadshots\b", r"(\d[\d,]*)", lambda x: int(x.replace(",", "")), "Headshot_Kills"),
    (r"\bheadshot\s*(?:rate|ratio|%)\b", r"(\d+(?:\.\d+)?)\s*%", float, "Headshot_Ratio"),
    (r"\bavg\.?\s*kills?\b|\bkills?\s*/\s*match\b", r"(\d+(?:\.\d+)?)", float, "Avg_Kills_Per_Match"),
    (r"\bavg\.?\s*damage\b|\bdamage\s*/\s*match\b", r"(\d+(?:\.\d+)?)", float, "Avg_Damage_Per_Match"),
    (r"\bwin\s*(?:rate|ratio)\b", r"(\d+(?:\.\d+)?)\s*%", float, "Win_Ratio"),
    (r"\btop\s*10\s*(?:rate|ratio)\b", r"(\d+(?:\.\d+)?)\s*%", float, "Top10_Ratio"),
    (r"\bf\s*/\s*d\b|\bk\s*/\s*d\b|\bkd\s*(?:rate|ratio)?\b", r"(\d+(?:\.\d+)?)", float, "KD_Ratio"),
    (r"\baccuracy\b|\bacc\.?\s*%\b", r"(\d+(?:\.\d+)?)\s*%", float, "Accuracy"),
    (r"\bshots?\s*fired\b", r"(\d[\d,]*)", lambda x: int(x.replace(",", "")), "Shots_Fired"),
    (r"\bshots?\s*hit\b", r"(\d[\d,]*)", lambda x: int(x.replace(",", "")), "Shots_Hit"),
    (r"\btotal\s*assists?\b|\bassists?\b", r"(\d[\d,]*)", lambda x: int(x.replace(",", "")), "Total_Assists"),
    (r"\btop\s*10\b", r"(\d[\d,]*)", lambda x: int(x.replace(",", "")), "Top10_Finishes"),
    # --- generic / broad labels last (they'll skip boxes already claimed above) ---
    (r"\bmatches?\b", r"(\d[\d,]*)", lambda x: int(x.replace(",", "")), "Matches_Played"),
    (r"\bwins?\b", r"(\d[\d,]*)", lambda x: int(x.replace(",", "")), "Wins"),
    (r"\beliminations?\b|\bkills?\b", r"(\d[\d,]*)", lambda x: int(x.replace(",", "")), "Total_Kills"),
    (r"\btotal\s*damage\b|\bdamage\b", r"([\d,]+(?:\.\d+)?)", lambda x: float(x.replace(",", "")), "Total_Damage"),
]

MODE_PATTERNS = [(r"\bsolo\b", "Solo"), (r"\bduo\b", "Duo"), (r"\bsquad\b", "Squad")]

STRUCTURAL_MARKERS = [
    r"\bmatches?\b",
    r"\bwins?\b",
    r"\bf\s*/\s*d\b|\bk\s*/\s*d\b|\bkd\s*(?:rate|ratio)?\b",
    r"\bheadshot",
    r"\baccuracy\b|\bacc\.?\s*%\b",
    r"\btop\s*10\b",
    r"\bsurvival\b|\bsurvived\b",
    r"\bdamage\b",
    r"\beliminations?\b",
]
MIN_STRUCTURAL_MARKERS = 3

# Set to True temporarily to print each OCR box's text, confidence, and
# center coordinates (cx, cy) on the image. Useful for tuning
# MAX_LABEL_VALUE_DISTANCE below on a new screenshot layout.
DEBUG_PRINT_BOXES = False

# Max pixel distance allowed between a label box and its value box. This is
# what prevents a value from a completely different part of the screenshot
# (e.g. a radar chart on the left) from being matched to a label in an
# unrelated table on the right, just because it appeared nearby in OCR's
# internal box ordering. Tune this per typical screenshot resolution: it
# should be comfortably smaller than the gap between distinct UI regions
# (e.g. the radar-chart column vs. the stats-table column) but large enough
# to cover a label sitting just above/below or beside its own value.
MAX_LABEL_VALUE_DISTANCE = 250

def _detect_mode(text: str) -> Optional[str]:
    lower = text.lower()
    for pattern, mode in MODE_PATTERNS:
        if re.search(pattern, lower):
            return mode
    return None

def _count_structural_markers(text: str) -> int:
    lower = text.lower()
    return sum(1 for pattern in STRUCTURAL_MARKERS if re.search(pattern, lower))

def _distance(cx1: float, cy1: float, cx2: float, cy2: float) -> float:
    return ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5

# EasyOCR sometimes splits ONE decimal number into two separate boxes when
# the decimal point renders faintly — e.g. "11.4%" gets read as a lone
# digit box "11" plus a second box "4%", dropping the "." entirely. Taken
# alone, "4%" still satisfies a percentage value_pattern, so without this
# check it gets accepted as a complete (and very wrong) value on its own.
# These control how close two boxes must be, spatially, to be treated as
# fragments of the same original number rather than two unrelated values.
NUMBER_FRAGMENT_ROW_TOLERANCE = 20   # max vertical (cy) difference, in px
NUMBER_FRAGMENT_MAX_GAP = 60         # max horizontal gap between fragments, in px
_PURE_DIGIT_FRAGMENT = re.compile(r"^\d+\.?$")

# EasyOCR frequently confuses certain letters with visually similar digits
# inside otherwise-numeric text — most commonly a capital 'I' or lowercase
# 'l' being read instead of '1' (e.g. the real text "11.4%" comes back as
# "Il.4%"). Left uncorrected, a value_pattern regex just skips past the
# corrupted letters and matches whatever bare digits are left (e.g. "4%"
# out of "Il.4%"), silently producing a wrong-but-plausible-looking number.
_DIGIT_LOOKALIKE_TRANSLATION = str.maketrans({
    "I": "1", "l": "1", "|": "1", "!": "1",
    "O": "0", "o": "0",
})

def _normalize_digit_lookalikes(text: str) -> str:
    return text.translate(_DIGIT_LOOKALIKE_TRANSLATION)

def _best_value_match(text: str, value_pattern: str) -> Tuple[Optional["re.Match[str]"], str, bool]:
    """Match value_pattern against `text`, but also try a version with
    common OCR digit-lookalike letters corrected — and prefer whichever
    match captures a longer (more complete) number, since a corrected
    match capturing more digits is far more likely to be the real value
    than a shorter match that only found what was left after skipping
    over misread characters.

    Only attempts the correction on text that already contains at least
    one real digit, so it can't turn an ordinary word into a fake number.
    Returns (match, text_used, was_corrected).
    """
    raw_match = re.search(value_pattern, text, flags=re.IGNORECASE)
    if not re.search(r"\d", text):
        return raw_match, text, False

    normalized = _normalize_digit_lookalikes(text)
    if normalized == text:
        return raw_match, text, False

    norm_match = re.search(value_pattern, normalized, flags=re.IGNORECASE)
    if norm_match and (not raw_match or len(norm_match.group(0)) > len(raw_match.group(0))):
        return norm_match, normalized, True
    return raw_match, text, False

def _try_reconstruct_split_number(
    boxes: List[Tuple[str, float, float, float]],
    value_idx: int,
    value_text: str,
    value_pattern: str,
    exclude: set,
) -> Optional[Tuple[int, str, "re.Match[str]"]]:
    """If `value_text` alone doesn't look like a complete number for this
    stat, check whether a plain-digit box sits immediately to its left on
    the same row — a likely leading-digit fragment that OCR split off.
    Returns (partner_index, merged_text, match) if reconstructing that way
    produces a valid match, else None.
    """
    _text, _conf, vx, vy = boxes[value_idx]
    for k, (ktext, _kconf, kx, ky) in enumerate(boxes):
        if k == value_idx or k in exclude:
            continue
        if not _PURE_DIGIT_FRAGMENT.match(ktext):
            continue
        if abs(ky - vy) > NUMBER_FRAGMENT_ROW_TOLERANCE:
            continue
        gap = vx - kx
        if not (0 < gap <= NUMBER_FRAGMENT_MAX_GAP):
            continue  # not immediately to the left, or on the wrong side
        merged_text = (ktext if ktext.endswith(".") else ktext + ".") + value_text
        m = re.search(value_pattern, merged_text, flags=re.IGNORECASE)
        if m:
            return k, merged_text, m
    return None

def _label_owner_index(box_text: str) -> Optional[int]:
    """Return the index of the FIRST PARSERS entry whose label_pattern
    matches this box's text.

    PARSERS is ordered specific -> generic on purpose. A box can often
    satisfy more than one pattern textually — e.g. a "Win Ratio" label also
    satisfies the bare r"\bwins?\b" pattern meant for "Wins", and
    "Highest Damage in a Match" also satisfies the bare r"\bdamage\b"
    pattern meant for "Total_Damage". Without a single fixed "owner", a box
    like that would only be safely excluded from the wrong stat WHEN the
    correct, more specific stat successfully finds a nearby value for it —
    but if that specific stat fails (e.g. the real percentage/number is far
    away or missing), the box was previously left unclaimed and could leak
    into a broader/generic pattern's search later, pairing with an
    unrelated number.

    Assigning one fixed owner up front — independent of whether that owner
    ultimately finds a valid value — closes that leak permanently.
    """
    for idx, (label_pattern, _, _, _) in enumerate(PARSERS):
        if re.search(label_pattern, box_text, flags=re.IGNORECASE):
            return idx
    return None

def extract_stats(image_path: str) -> Dict[str, Any]:
    reader = _get_reader()
    warnings: List[str] = []
    stats: Dict[str, Dict[str, Any]] = {}

    if reader is False:
        return {
            "mode": None,
            "stats": {},
            "warnings": ["OCR engine unavailable. Install EasyOCR or add a manual-entry layer."],
            "is_valid_screenshot": False,
        }

    gray = _preprocess(image_path)
    try:
        results = reader.readtext(gray, detail=1, paragraph=False)
    except Exception as exc:
        return {"mode": None, "stats": {}, "warnings": [f"OCR failed: {exc}"], "is_valid_screenshot": False}

    # boxes: (text, confidence, center_x, center_y)
    boxes: List[Tuple[str, float, float, float]] = []
    for bbox, text, conf in results:
        text = text.strip()
        if not text:
            continue
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        cx = sum(xs) / 4.0
        cy = sum(ys) / 4.0
        boxes.append((text, float(conf), cx, cy))

    if DEBUG_PRINT_BOXES:
        print("---- OCR BOXES (text | conf | cx | cy) ----")
        for text, conf, cx, cy in boxes:
            print(f"{text!r:35s} conf={conf:.2f} cx={cx:7.1f} cy={cy:7.1f}")
        print("--------------------------------------------")

    full_text = "\n".join(t for t, _, _, _ in boxes)
    mode = _detect_mode(full_text)

    marker_count = _count_structural_markers(full_text)
    is_valid_screenshot = marker_count >= MIN_STRUCTURAL_MARKERS
    if not is_valid_screenshot:
        warnings.append(
            f"Only {marker_count} BGMI stat label(s) detected — this doesn't look "
            f"like a valid stats screenshot."
        )

    if not mode:
        warnings.append("Could not confidently detect Solo, Duo or Squad mode.")

    # Fix each box's single "owner" pattern up front (see _label_owner_index)
    # so a box that textually matches more than one pattern can only ever be
    # treated as a label for the most specific one — regardless of whether
    # that pattern later succeeds in finding a nearby value for it.
    label_owner: List[Optional[int]] = [
        _label_owner_index(text) for text, _conf, _cx, _cy in boxes
    ]

    # Track which boxes have already been claimed as a LABEL or a VALUE for
    # some stat, so the same box can never be double-counted across two
    # different stats.
    used_label_indices: set = set()
    used_value_indices: set = set()

    for pi, (label_pattern, value_pattern, parser, stat_name) in enumerate(PARSERS):
        best_value = None
        best_conf = 0.0
        best_distance = float("inf")
        best_label_idx: Optional[int] = None
        best_value_idx: Optional[int] = None
        best_fragment_partner: Optional[int] = None

        for i, (box_text, conf, lx, ly) in enumerate(boxes):
            if i in used_label_indices:
                continue
            if label_owner[i] != pi:
                continue

            # Try same-box match first (handles combined "Label 123" boxes).
            same_box_match = re.search(value_pattern, box_text, flags=re.IGNORECASE)

            # Each candidate: (value_idx, text_used, confidence, vx, vy, match, fragment_partner_idx_or_None)
            candidates: List[Tuple[int, str, float, float, float, "re.Match[str]", Optional[int]]] = []
            if same_box_match:
                candidates.append((i, box_text, conf, lx, ly, same_box_match, None))
            else:
                for j, (vtext, vconf, vx, vy) in enumerate(boxes):
                    if j == i or j in used_value_indices:
                        continue
                    # Skip boxes that look like another label rather than a value.
                    if re.search(r"[a-zA-Z]{4,}", vtext) and not re.search(value_pattern, vtext):
                        continue
                    m, vtext_used, was_corrected = _best_value_match(vtext, value_pattern)
                    fragment_partner = None
                    if m and _PURE_DIGIT_FRAGMENT.match(m.group(0).rstrip("%").strip()) and not was_corrected:
                        # This candidate is JUST digits (e.g. "4%") with no
                        # decimal point, and correcting digit-lookalikes
                        # didn't change anything — check whether it's
                        # actually the tail of a larger number split
                        # across two separate boxes before trusting it as
                        # the whole value.
                        reconstructed = _try_reconstruct_split_number(
                            boxes, j, vtext, value_pattern,
                            exclude=used_value_indices | {i},
                        )
                        if reconstructed:
                            fragment_partner, vtext_used, m = reconstructed
                    if not m:
                        continue
                    dist = _distance(lx, ly, vx, vy)
                    if dist > MAX_LABEL_VALUE_DISTANCE:
                        continue  # too far away — almost certainly a different UI region
                    candidates.append((j, vtext_used, vconf * (0.85 if was_corrected else 1.0), vx, vy, m, fragment_partner))

            if not candidates:
                continue

            # Pick the closest matching value box to this label box.
            j, vtext, vconf, vx, vy, m, fragment_partner = min(
                candidates, key=lambda c: _distance(lx, ly, c[3], c[4])
            )
            dist = _distance(lx, ly, vx, vy)

            try:
                value = parser(m.group(1) if m.lastindex else m.group(0))
            except Exception:
                continue

            confidence = max(0.0, min(1.0, min(conf, vconf)))
            if fragment_partner is not None:
                confidence = min(confidence, boxes[fragment_partner][1])
            # Across all candidate label boxes for this stat (handles
            # duplicate label text appearing more than once), keep the
            # closest label/value pair overall.
            if best_value is None or dist < best_distance:
                best_value, best_conf, best_distance = value, confidence, dist
                best_label_idx, best_value_idx = i, j
                best_fragment_partner = fragment_partner

        if best_value is not None:
            used_label_indices.add(best_label_idx)
            used_value_indices.add(best_value_idx)
            if best_fragment_partner is not None:
                used_value_indices.add(best_fragment_partner)

            confidence = round(best_conf, 3)
            if confidence < 0.5:
                warnings.append(f"Low OCR confidence on '{stat_name}'.")
            stats[stat_name] = {
                "value": best_value,
                "raw": str(best_value),
                "confidence": confidence,
                "source": "ocr",
            }

    if mode == "Solo" and stats.get("Total_Assists", {}).get("value", 0) > 0:
        warnings.append("Solo mode shows non-zero assists; treat this as a data-integrity warning.")

    if not stats:
        warnings.append("No supported statistics could be extracted from the screenshot.")
        is_valid_screenshot = False

    return {
        "mode": mode,
        "stats": stats,
        "warnings": warnings,
        "is_valid_screenshot": is_valid_screenshot,
    }