"""Parse Granola-style dinner notes into structured records.

Granola exports a stable set of `### ` sections per note. Everything here keys
off those headings, so a new trip needs no code changes -- only a trip.json.

Sections are read into `SECTION_MAP` keys; any heading not in the map is kept
under its own lowercased name so unexpected sections are never silently lost.
Dates parse from the `Sun, 09 Aug 26` byline; `companion` comes from the same
line after the middot separator.
"""
import json
import os
import re

SECTION_MAP = {
    "attendees": "attendees",
    "setting and vibe": "setting",
    "main conversation threads": "threads",
    "stories started": "stories",
    "best lines and bits": "quotes",
    "theories and claims": "theories",
    "side quests": "sidequests",
    "emotional undercurrents": "undercurrent",
    "unanswered questions": "questions",
    "things people promised to send": "promised",
    "open loops": "loops",
    "decisions or plans": "decisions",
    "next dinner": "next",
}

LIST_FIELDS = [
    "attendees", "setting", "threads", "stories", "theories", "sidequests",
    "undercurrent", "questions", "promised", "loops", "decisions", "next",
]

MONTHS = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
    "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}

DAY_RE = r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)"
NOTHING_RE = re.compile(
    r"^(no |nothing |none\b)", re.I
)


def dedupe(text):
    """Some exports paste the same note repeatedly; keep one copy.

    Splits on the H1 and collapses only when every segment is identical, so a
    file that genuinely concatenates different notes is left alone.
    """
    lines = text.split("\n")
    head = lines[0].strip()
    if not head.startswith("# "):
        return text
    segs = [s for s in text.split(head) if s.strip()]
    if len(segs) > 1 and len(set(s.strip() for s in segs)) == 1:
        return head + segs[0]
    return text


def parse_byline(line):
    """`Sun, 09 Aug 26 - Name` -> (iso_date, companion)."""
    date, companion = "", ""
    m = re.match(
        r"^%s,?\s+(\d{1,2})\s+([A-Za-z]{3})[a-z]*\.?\s+(\d{2,4})" % DAY_RE, line
    )
    if m:
        d, mon, y = m.groups()
        year = y if len(y) == 4 else "20" + y
        date = "%s-%s-%02d" % (year, MONTHS.get(mon.lower(), "01"), int(d))
    parts = [p.strip() for p in re.split(r"[·|]", line)]
    if len(parts) > 1:
        companion = parts[1]
    return date, companion


def split_sections(raw):
    """Return {heading: [raw lines]} for every `### ` block."""
    out, current = {}, None
    for ln in raw.split("\n"):
        m = re.match(r"^#{2,4}\s+(.*)$", ln)
        if m:
            current = m.group(1).strip()
            out.setdefault(current, [])
            continue
        if current is None:
            continue
        if ln.strip().startswith("Chat with meeting transcript"):
            continue
        out[current].append(ln)
    return out


def collect(lines):
    """Flatten a section into a list of entries, bullets first then prose.

    Sub-headings inside a section (Granola sometimes emits bold or bare-line
    group labels) are folded in as plain entries rather than dropped.
    """
    bullets, prose = [], []
    for ln in lines:
        s = ln.strip()
        if not s or s == "---":
            continue
        if s.startswith(("- ", "* ")):
            bullets.append(s[2:].strip())
        elif s.startswith(("+ ",)):
            bullets.append(s[2:].strip())
        elif len(s) > 3:
            prose.append(re.sub(r"^\*+|\*+$", "", s).strip())
    return bullets + prose


CLOSERS = {"“": "”", '"': '"', "‘": "’", "'": "'"}


def clean_quote(q):
    """Split a `"line" (attribution)` bullet into (text, attribution).

    Matches the closing delimiter to the opening one and scans from the END of
    the line, so apostrophes inside the quote are never mistaken for the close.
    An unbalanced line degrades to the whole string with no attribution.
    """
    q = q.strip().lstrip("-*+").strip()
    if not q:
        return "", ""

    # `Speaker, on the thing: "line"` -> keep the lead-in as the attribution.
    lead = re.match(r'^([^“"]{2,60}?):\s*([“"].*)$', q, re.S)
    if lead:
        text, inner = clean_quote(lead.group(2))
        return text, inner or lead.group(1).strip()

    opener = q[0]
    if opener in CLOSERS:
        closer = CLOSERS[opener]
        # Prefer a closer whose remainder is empty or a single parenthetical --
        # attributions may themselves contain quotes, so scanning from the end
        # would swallow the whole line.
        best = -1
        for i in range(1, len(q)):
            if q[i] != closer:
                continue
            rest = q[i + 1:].strip()
            if not rest or re.fullmatch(r"\(.*\)", rest, re.S):
                best = i
                break
            if best < 0:
                best = i
        if best > 0:
            return q[1:best].strip(), q[best + 1:].strip().strip("()").strip(" —-")
        return q[1:].strip(), ""

    # Unquoted bullet: peel a trailing parenthetical as the attribution.
    m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", q)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return q, ""


def is_nothing(items):
    """True when a section only says some variant of 'nothing happened'."""
    return len(items) == 1 and bool(NOTHING_RE.match(items[0]))


def title_case_venue(slug, title):
    """Prefer the note's own H1; fall back to a tidied slug."""
    t = (title or "").strip()
    if t and t.lower() != slug.lower():
        return t if not t.islower() else t.title()
    return slug.replace("_", " ").title()


def parse_note(path):
    raw = dedupe(open(path).read())
    lines = raw.split("\n")
    slug = os.path.splitext(os.path.basename(path))[0]

    title = lines[0].lstrip("#").strip() if lines[0].startswith("#") else slug
    byline, date, companion = "", "", ""
    for ln in lines[1:8]:
        if re.match(r"^%s," % DAY_RE, ln.strip()):
            byline = ln.strip()
            date, companion = parse_byline(byline)
            break

    sections = split_sections(raw)
    rec = {
        "slug": slug,
        "title": title,
        "venue": title_case_venue(slug, title),
        "byline": byline,
        "date": date,
        "companion": companion,
        "extra": {},
    }
    for f in LIST_FIELDS:
        rec[f] = []
    rec["quotes"] = []

    for heading, body in sections.items():
        items = collect(body)
        key = SECTION_MAP.get(heading.strip().lower())
        if key == "quotes":
            for b in items:
                text, attrib = clean_quote(b)
                if text:
                    rec["quotes"].append({"text": text, "attrib": attrib})
        elif key:
            rec[key] = items
        elif items:
            rec["extra"][heading] = items

    m = re.search(r"(https://notes\.granola\.ai/\S+)", raw)
    rec["transcript"] = m.group(1).rstrip("#") if m else ""

    for f in ("decisions", "next", "promised"):
        rec[f + "_empty"] = is_nothing(rec[f])

    return rec


def redact_text(s, pairs):
    """Replace each configured name with its stand-in.

    Longest patterns run first so a full name is handled before its first name,
    and matching is word-bounded and case-sensitive to avoid mangling ordinary
    words that happen to contain a name.
    """
    for rx, repl in pairs:
        s = rx.sub(repl, s)
    # An initial ending in "." next to sentence punctuation, and a role stand-in
    # landing after the noun it replaces, both read as typos.
    s = re.sub(r"\.\.(?=\s|$)", ".", s)
    s = re.sub(r"\b([Tt]he)\s+(\w+)\s+the\s+\2\b", r"\1 \2", s)
    s = re.sub(r"\b([Tt]he)\s+the\b", r"\1", s)
    return s


def compile_redactions(names):
    """Build (regex, replacement) pairs, longest name first."""
    pairs = []
    for name in sorted(names or {}, key=len, reverse=True):
        pairs.append((re.compile(r"\b%s\b" % re.escape(name)), names[name]))
    return pairs


def suppress(rec, patterns):
    """Drop individual entries matching any pattern, section by section.

    Lets a single sensitive line be withheld without losing the section around
    it. Patterns are case-insensitive substrings or regexes.
    """
    if not patterns:
        return rec
    rxs = [re.compile(p, re.I) for p in patterns]
    hit = lambda s: any(r.search(s) for r in rxs)
    for f in LIST_FIELDS:
        rec[f] = [x for x in rec.get(f) or [] if not hit(x)]
    rec["quotes"] = [q for q in rec.get("quotes") or []
                     if not hit(q["text"]) and not hit(q["attrib"])]
    rec["extra"] = {k: [v for v in vals if not hit(v)]
                    for k, vals in (rec.get("extra") or {}).items()}
    rec["extra"] = {k: v for k, v in rec["extra"].items() if v}
    return rec


def redact_record(rec, pairs, drop):
    """Apply name redaction and drop suppressed sections from one dinner."""
    for key in drop or []:
        if key in rec:
            rec[key] = []
            rec[key + "_empty"] = False
    if not pairs:
        return rec
    for f in LIST_FIELDS:
        rec[f] = [redact_text(x, pairs) for x in rec.get(f) or []]
    rec["quotes"] = [
        {"text": redact_text(q["text"], pairs),
         "attrib": redact_text(q["attrib"], pairs)}
        for q in rec.get("quotes") or []
    ]
    rec["extra"] = {
        redact_text(k, pairs): [redact_text(v, pairs) for v in vals]
        for k, vals in (rec.get("extra") or {}).items()
    }
    for f in ("title", "venue", "companion", "byline"):
        rec[f] = redact_text(rec.get(f) or "", pairs)
    return rec


def apply_aliases(dinners, aliases):
    """Normalize companion spellings, e.g. a run-together Granola handle."""
    if not aliases:
        return
    lookup = {}
    for canonical, variants in aliases.items():
        lookup[re.sub(r"[^a-z]", "", canonical.lower())] = canonical
        for v in variants:
            lookup[re.sub(r"[^a-z]", "", v.lower())] = canonical
    for d in dinners:
        key = re.sub(r"[^a-z]", "", (d.get("companion") or "").lower())
        if key in lookup:
            d["companion"] = lookup[key]


def deep_merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        elif isinstance(v, list) and isinstance(out.get(k), list):
            out[k] = out[k] + v
        else:
            out[k] = v
    return out


def load_trip(trip_dir):
    """Read trip.json (+ optional trip.private.json) and return (cfg, dinners).

    `trip.private.json` holds anything that must not be published -- real names
    and suppression patterns are a decoder ring for the redacted output, so they
    live in a gitignored sibling and are merged over the public config.
    """
    cfg_path = os.path.join(trip_dir, "trip.json")
    cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}

    priv_path = os.path.join(trip_dir, "trip.private.json")
    if os.path.exists(priv_path):
        cfg = deep_merge(cfg, json.load(open(priv_path)))

    notes_dir = os.path.join(trip_dir, cfg.get("notes_dir", "granola_notes"))
    if not os.path.isdir(notes_dir):
        raise SystemExit("no notes directory: %s" % notes_dir)

    found = sorted(f for f in os.listdir(notes_dir) if f.endswith(".md"))
    order = cfg.get("order") or []
    slugs = [s for s in order if s + ".md" in found]
    slugs += [os.path.splitext(f)[0] for f in found
              if os.path.splitext(f)[0] not in slugs]

    dinners = [parse_note(os.path.join(notes_dir, s + ".md")) for s in slugs]

    meta = cfg.get("venues", {})
    for d in dinners:
        over = meta.get(d["slug"], {})
        d["venue"] = over.get("name", d["venue"])
        d["kind"] = over.get("kind", "")
        if over.get("date"):
            d["date"] = over["date"]

    apply_aliases(dinners, cfg.get("companion_aliases"))

    # Suppression runs on the original text; redaction would rewrite the very
    # names the patterns match on.
    suppressed = cfg.get("suppress") or []
    if suppressed:
        dinners = [suppress(d, suppressed) for d in dinners]

    pairs = compile_redactions(cfg.get("redact_names"))
    drop = cfg.get("drop_sections") or []
    if pairs or drop:
        dinners = [redact_record(d, pairs, drop) for d in dinners]

    if not cfg.get("order"):
        dinners.sort(key=lambda d: (d["date"] or "9999", d["slug"]))

    return cfg, dinners
