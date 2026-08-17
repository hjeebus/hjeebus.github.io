#!/usr/bin/env python3
"""Build a case-file site from a folder of Granola dinner notes.

    python3 _tools/papers/build.py the_wilmington_papers

Reads `<trip>/trip.json` plus `<trip>/granola_notes/*.md` and writes the five
top-level pages and one page per dinner into `<trip>/`. Every string shown to a
reader comes from trip.json, so a new trip is config plus notes and no code.

Pass `--check` to validate and report without writing files. Generated markup
carries all content inline; the theme toggle and quote shuffle are the only
scripted behavior and the pages remain complete with JavaScript disabled.
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parse import load_trip
from theme import CSS, TABS, THEME_JS

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII",
         "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"]
MONTH_ABBR = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
              "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

DEFAULTS = {
    "title": "The Papers",
    "tagline": "Dinners, transcribed and entered into evidence.",
    "footer": "field notes",
    "noindex": False,
    "sections": {
        "cold_cases": {
            "kicker": "Section I - unresolved",
            "title": "Cold Cases",
            "dek": "{questions} questions asked and never answered. {loops} loops left open.",
        },
        "record": {
            "kicker": "Section II",
            "title": "The Record",
            "dek": "{dinners} sittings, chronological. Each one catalogued in full.",
        },
        "canon": {
            "kicker": "Section III - the record of claims",
            "title": "Canon",
            "dek": "{theories} assertions made with total confidence and zero verification.",
        },
        "quotable": {
            "kicker": "Section IV",
            "title": "Quotable",
            "dek": "Every line worth preserving, served one at a time.",
        },
    },
}


def e(s):
    return html.escape(str(s), quote=True)


def merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def datestamp(iso):
    if not iso:
        return ""
    try:
        y, m, d = iso.split("-")
        return "%d %s %s" % (int(d), MONTH_ABBR[int(m) - 1], y)
    except (ValueError, IndexError):
        return iso


def roman(i):
    return ROMAN[i] if i < len(ROMAN) else str(i + 1)


def total(dinners, key):
    return sum(len(d.get(key) or []) for d in dinners)


def real_items(dinners, key):
    """Yield (dinner, item) skipping sections that only say 'nothing'."""
    for d in dinners:
        if d.get(key + "_empty"):
            continue
        for item in d.get(key) or []:
            yield d, item


# ---------------------------------------------------------------- threads

def find_threads(dinners, probes, min_hits=2):
    """Match configured regexes against each dinner; keep multi-sitting hits."""
    out = []
    for label, pattern in (probes or {}).items():
        try:
            rx = re.compile(pattern, re.I)
        except re.error:
            print("  ! bad regex for thread %r, skipped" % label, file=sys.stderr)
            continue
        hits = [d for d in dinners if rx.search(json.dumps(d, ensure_ascii=False))]
        if len(hits) >= min_hits:
            out.append((label, hits))
    return sorted(out, key=lambda kv: -len(kv[1]))


# ---------------------------------------------------------------- chrome

def page(cfg, title, body, current, depth=0):
    up = "../" * depth
    tabs = "".join(
        '<a href="%s%s"%s>%s</a>' % (
            up, href, ' aria-current="page"' if key == current else "", e(label))
        for href, label, key in TABS
    )
    tabs += '<a class="themer" href="#" id="themer" title="Toggle light and dark">&#9686;</a>'
    robots = ('\n<meta name="robots" content="noindex,nofollow">'
              if cfg.get("noindex") else "")
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">%s
<style>%s</style>
</head>
<body>
<div class="wrap">
<nav class="tabs">%s</nav>
%s
<footer class="foot">
  %s &middot; %s &middot; <a href="%sindex.html">return to file</a>
</footer>
</div>
<script>%s</script>
</body>
</html>
""" % (e(title), e(cfg["tagline"][:150]), robots, CSS, tabs, body,
       e(cfg["title"]), e(cfg["footer"]), up, THEME_JS)


def suffix(cfg):
    return " - " + cfg["title"]


# ---------------------------------------------------------------- pages

def build_home(cfg, dinners, threads):
    nq = total(dinners, "quotes")
    stats = {
        "questions": total(dinners, "questions"),
        "loops": total(dinners, "loops"),
        "theories": total(dinners, "theories"),
        "dinners": len(dinners),
    }

    hero, hero_d = None, None
    want = cfg.get("hero_quote", "")
    for d in dinners:
        for q in d["quotes"]:
            if want and q["text"].startswith(want):
                hero, hero_d = q, d
    if hero is None:
        for d in dinners:
            if d["quotes"]:
                hero, hero_d = d["quotes"][0], d
                break

    facts = "".join(
        "<span><b>%s</b> %s</span>" % (e(v), e(k))
        for k, v in [
            ("dinners", len(dinners)),
            ("venues", len({d["venue"] for d in dinners})),
            ("days", len({d["date"] for d in dinners if d["date"]})),
        ]
    )
    for f in cfg.get("facts", []):
        facts += "<span><b>%s</b> %s</span>" % (e(f.get("n", "")), e(f.get("label", "")))

    body = """
<header class="mast">
  <div class="kicker">Exhibits 1&ndash;%d &middot; entered into evidence</div>
  <h1 class="title">%s</h1>
  <p class="dek">%s</p>
  <div class="mast-meta">%s</div>
</header>
""" % (nq, e(cfg["title"]), e(cfg["tagline"]), facts)

    if hero:
        body += """
<div class="exhibit">
  <p class="q">&ldquo;%s&rdquo;</p>
  <div class="src">Exhibit A &middot; %s &middot; %s</div>
</div>
""" % (e(hero["text"]), e(hero_d["venue"]), datestamp(hero_d["date"]))

    rows = [
        (stats["questions"], "questions unanswered"),
        (stats["loops"], "loops left open"),
        (stats["theories"], "claims on record"),
    ]
    kicker = cfg.get("closing_stat")
    if kicker:
        rows.append((kicker.get("n", 0), kicker.get("label", "")))
    else:
        rows.append((sum(1 for d in dinners if not d.get("decisions_empty")),
                     "nights with a decision"))

    body += '<div class="stat-row">'
    for n, label in rows:
        body += '<div class="stat"><b>%s</b><span>%s</span></div>' % (e(n), e(label))
    body += "</div>"

    if threads:
        body += ('<h2 class="sec">Recurring threads</h2>'
                 '<p class="sec-note">Subjects that refused to die across multiple sittings.</p>'
                 '<hr class="rule">')
        for label, ds in threads:
            where = ", ".join(
                '<a href="dinners/%s.html">%s</a>' % (e(d["slug"]), e(d["venue"])) for d in ds)
            body += ('<div class="thread"><h3>%s <span class="count">%d sittings</span></h3>'
                     '<div class="where">%s</div></div>') % (e(label), len(ds), where)

    sec = cfg["sections"]
    body += '<h2 class="sec">Where to start</h2><hr class="rule"><div class="docket">'
    for i, (href, key, blurb, count) in enumerate([
        ("cold-cases.html", "cold_cases",
         "Every question nobody answered, and every loop still spinning.",
         "%d items" % (stats["questions"] + stats["loops"])),
        ("record.html", "record", "All the dinners, in the order they happened.",
         "%d nights" % len(dinners)),
        ("canon.html", "canon", "Claims asserted confidently, verified never.",
         "%d claims" % stats["theories"]),
        ("quotable.html", "quotable", "Pull a line at random from the transcript.",
         "%d lines" % nq),
    ]):
        body += ('<a class="doc" href="%s"><span class="num">%02d</span>'
                 '<span><span class="v">%s</span><br><span class="k">%s</span></span>'
                 '<span class="d">%s</span></a>') % (
            href, i + 1, e(sec[key]["title"]), e(blurb), e(count))
    body += "</div>"

    return page(cfg, cfg["title"], body, "index")


def masthead(cfg, key, stats):
    s = cfg["sections"][key]
    return """
<header class="mast">
  <div class="kicker">%s</div>
  <h1 class="title">%s</h1>
  <p class="dek">%s</p>
</header>
""" % (e(s["kicker"]), e(s["title"]), e(s["dek"].format(**stats)))


def build_record(cfg, dinners, stats):
    body = masthead(cfg, "record", stats) + '<div class="docket">'
    for i, d in enumerate(dinners):
        kind = ('<span class="k">%s</span>' % e(d["kind"])) if d.get("kind") else ""
        body += """  <a class="doc" href="dinners/%s.html">
    <span class="num">%s</span>
    <span><span class="v">%s</span><br>%s
      <span class="tally">%d lines &middot; %d unanswered &middot; %d claims</span></span>
    <span class="d">%s</span>
  </a>
""" % (e(d["slug"]), roman(i), e(d["venue"]), kind, len(d["quotes"]),
       len(d["questions"]), len(d["theories"]), datestamp(d["date"]))
    return page(cfg, cfg["sections"]["record"]["title"] + suffix(cfg), body + "</div>", "record")


def anchor_id(prefix, text):
    """Stable per-item id: survives reordering, changes only if the text does."""
    digest = hashlib.sha1(text.strip().encode("utf-8")).hexdigest()[:8]
    return "%s-%s" % (prefix, digest)


def permalink(item_id, depth=0, page_name=""):
    """Anchor + copy-link control rendered inside a list item."""
    target = "%s%s#%s" % ("../" * depth, page_name, item_id)
    return (' <a class="plink" href="%s" aria-label="Link to this item"'
            ' title="Link to this item">#</a>') % e(target)


def evidence_list(dinners, key, cls, depth=0, page_name="", prefix=None):
    up = "../" * depth
    rows = ""
    for d, item in real_items(dinners, key):
        item_id = anchor_id(prefix or key[:1], item)
        rows += (
            '  <li id="{id}">{text}{link}<span class="src">'
            '<a href="{up}dinners/{slug}.html">{venue}</a> &middot; {date}</span></li>\n'
        ).format(
            id=e(item_id),
            text=e(item),
            link=permalink(item_id, depth, page_name),
            up=up,
            slug=e(d["slug"]),
            venue=e(d["venue"]),
            date=datestamp(d["date"]),
        )
    if not rows:
        return '<p class="quiet">Nothing on record.</p>'
    return '<ul class="evid %s">\n%s</ul>' % (cls, rows)


def build_cold(cfg, dinners, stats):
    body = masthead(cfg, "cold_cases", stats)
    body += ('<h2 class="sec">Unanswered questions</h2>'
             '<p class="sec-note">Raised at the table. Never resolved.</p><hr class="rule">')
    body += evidence_list(dinners, "questions", "", page_name="cold-cases.html", prefix="q")
    body += ('<h2 class="sec">Open loops</h2>'
             '<p class="sec-note">Still spinning. Possibly forever.</p><hr class="rule">')
    body += evidence_list(dinners, "loops", "loop", page_name="cold-cases.html", prefix="l")
    if any(True for _ in real_items(dinners, "promised")):
        body += ('<h2 class="sec">Promised, pending</h2>'
                 '<p class="sec-note">Things people said they would send.</p><hr class="rule">')
        body += evidence_list(dinners, "promised", "quest",
                              page_name="cold-cases.html", prefix="p")
    return page(cfg, cfg["sections"]["cold_cases"]["title"] + suffix(cfg), body, "cold-cases")


def build_canon(cfg, dinners, stats):
    body = masthead(cfg, "canon", stats)
    body += '<h2 class="sec">Entered into evidence</h2><hr class="rule">'
    body += evidence_list(dinners, "theories", "claim", page_name="canon.html", prefix="c")
    nsq = total(dinners, "sidequests")
    if nsq:
        body += ('<h2 class="sec">Side quests</h2>'
                 '<p class="sec-note">%d digressions that took over the table.</p>'
                 '<hr class="rule">') % nsq
        body += evidence_list(dinners, "sidequests", "quest",
                              page_name="canon.html", prefix="s")
    return page(cfg, cfg["sections"]["canon"]["title"] + suffix(cfg), body, "canon")


def build_quotable(cfg, dinners, stats):
    pool = [{"t": q["text"], "a": q["attrib"], "v": d["venue"],
             "d": datestamp(d["date"]), "s": d["slug"],
             "id": anchor_id("x", q["text"])}
            for d in dinners for q in d["quotes"]]

    body = masthead(cfg, "quotable", stats)
    if not pool:
        return page(cfg, cfg["sections"]["quotable"]["title"] + suffix(cfg),
                    body + '<p class="quiet">No lines on record.</p>', "quotable")

    body += '<div id="slot"></div><button class="btn" id="again">Pull another line</button>'
    body += '<h2 class="sec">The complete set</h2><hr class="rule"><ul class="evid quest">'
    for p in pool:
        gloss = " <em>(%s)</em>" % e(p["a"]) if p["a"] else ""
        body += (
            '<li id="{id}">&ldquo;{text}&rdquo;{gloss}{link}<span class="src">'
            '<a href="dinners/{slug}.html">{venue}</a> &middot; {date}</span></li>'
        ).format(
            id=e(p["id"]),
            text=e(p["t"]),
            gloss=gloss,
            link=permalink(p["id"], 0, "quotable.html"),
            slug=e(p["s"]),
            venue=e(p["v"]),
            date=p["d"],
        )
    body += "</ul>"

    body += """
<script>
var Q = %s, last = -1, syncing = false;

function show(i, setHash){
  last = i;
  var q = Q[i], slot = document.getElementById('slot');
  slot.textContent = '';
  var card = document.createElement('div');
  card.className = 'exhibit';
  card.style.width = '100%%';
  var p = document.createElement('p');
  p.className = 'q';
  p.textContent = '\\u201c' + q.t + '\\u201d';
  card.appendChild(p);
  if (q.a) {
    var g = document.createElement('div');
    g.className = 'gloss'; g.textContent = q.a; card.appendChild(g);
  }
  var s = document.createElement('div');
  s.className = 'src';
  s.textContent = q.v + ' \\u00b7 ' + q.d + ' \\u00b7 ';
  var link = document.createElement('a');
  link.href = '#' + q.id;
  link.textContent = 'link to this line';
  s.appendChild(link);
  card.appendChild(s);
  slot.appendChild(card);
  // Assigning location.hash (not replaceState) so :target follows the card and
  // the previously linked row stops being highlighted. The scroll position is
  // restored because the shuffle button is what the reader is looking at.
  if (setHash && location.hash !== '#' + q.id) {
    var x = window.pageXOffset, y = window.pageYOffset;
    syncing = true;
    location.hash = q.id;
    window.scrollTo(x, y);
  }
}

function pull(){
  var i = Math.floor(Math.random()*Q.length);
  if (Q.length > 1) { while (i === last) i = Math.floor(Math.random()*Q.length); }
  show(i, true);
}

function fromHash(){
  var h = location.hash.replace(/^#/, '');
  if (!h) return -1;
  for (var i = 0; i < Q.length; i++) { if (Q[i].id === h) return i; }
  return -1;
}

document.getElementById('again').addEventListener('click', pull);

var start = fromHash();
show(start >= 0 ? start : Math.floor(Math.random()*Q.length), false);

window.addEventListener('hashchange', function(){
  if (syncing) { syncing = false; return; }
  var i = fromHash();
  if (i >= 0) show(i, false);
});
</script>
""" % json.dumps(pool, ensure_ascii=False)
    return page(cfg, cfg["sections"]["quotable"]["title"] + suffix(cfg), body, "quotable")


def block(label, items, cls="plain", note=None, empty=False):
    if not items:
        return ""
    out = '<h2 class="sec">%s</h2>' % e(label)
    if note:
        out += '<p class="sec-note">%s</p>' % e(note)
    out += '<hr class="rule">'
    if empty:
        return out + '<p class="quiet">%s</p>' % e(items[0])
    if cls == "plain":
        return out + '<ul class="plain">%s</ul>' % "".join("<li>%s</li>" % e(i) for i in items)
    return out + '<ul class="evid %s">%s</ul>' % (cls, "".join("<li>%s</li>" % e(i) for i in items))


def build_dinner(cfg, dinners, i):
    d = dinners[i]
    prev = dinners[i - 1] if i > 0 else None
    nxt = dinners[i + 1] if i < len(dinners) - 1 else None

    sub = " &middot; ".join(filter(None, [
        e(d["kind"]) if d.get("kind") else "",
        datestamp(d["date"]),
        "with " + e(d["companion"]) if d.get("companion") else "",
    ]))

    body = """
<header class="dinner-head">
  <div class="num">Sitting %s of %d</div>
  <h1>%s</h1>
  <p class="sub">%s</p>
</header>
<div class="mast-meta">
  <span><b>%d</b> lines</span><span><b>%d</b> unanswered</span>
  <span><b>%d</b> claims</span><span><b>%d</b> open loops</span>
</div>
""" % (roman(i), len(dinners), e(d["venue"]), sub, len(d["quotes"]),
       len(d["questions"]), len(d["theories"]), len(d["loops"]))

    if d["setting"]:
        body += '<h2 class="sec">Setting and vibe</h2><hr class="rule">'
        body += "".join('<p class="setting">%s</p>' % e(s) for s in d["setting"])

    if d["quotes"]:
        body += ('<h2 class="sec">Exhibits</h2>'
                 '<p class="sec-note">Lines entered into the record.</p><hr class="rule">')
        for q in d["quotes"]:
            gloss = '<div class="gloss">%s</div>' % e(q["attrib"]) if q["attrib"] else ""
            qid = anchor_id("x", q["text"])
            body += (
                '<div class="exhibit" id="{id}"><p class="q">&ldquo;{text}&rdquo;'
                '<a class="plink" href="#{id}" aria-label="Link to this line"'
                ' title="Link to this line">#</a></p>{gloss}</div>'
            ).format(id=e(qid), text=e(q["text"]), gloss=gloss)

    body += block("Main conversation threads", d["threads"])
    body += block("Stories started", d["stories"])
    body += block("Theories and claims", d["theories"], "claim")
    body += block("Side quests", d["sidequests"], "quest")

    if d["undercurrent"]:
        body += '<h2 class="sec">Emotional undercurrents</h2><hr class="rule">'
        body += "".join('<div class="undercurrent">%s</div>' % e(u) for u in d["undercurrent"])

    body += block("Unanswered questions", d["questions"], "")
    body += block("Promised to send", d["promised"], "quest", empty=d.get("promised_empty"))
    body += block("Open loops", d["loops"], "loop")
    body += block("Decisions or plans", d["decisions"], empty=d.get("decisions_empty"))
    body += block("Next dinner", d["next"], empty=d.get("next_empty"))

    for heading, items in (d.get("extra") or {}).items():
        body += block(heading, items)

    if d["transcript"]:
        body += ('<p style="margin-top:34px"><a class="mono" style="font-size:.68rem;'
                 'letter-spacing:.1em;text-transform:uppercase;color:var(--faded)" '
                 'href="%s">Full transcript &rarr;</a></p>') % e(d["transcript"])

    body += '<div class="pager">'
    body += ('<a href="%s.html">&larr; %s</a>' % (e(prev["slug"]), e(prev["venue"])) if prev
             else '<a href="../record.html">&larr; The Record</a>')
    body += ('<a href="%s.html">%s &rarr;</a>' % (e(nxt["slug"]), e(nxt["venue"])) if nxt
             else '<a href="../cold-cases.html">Cold Cases &rarr;</a>')
    body += "</div>"

    return page(cfg, d["venue"] + suffix(cfg), body, "record", depth=1)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Build a case-file site from dinner notes.")
    ap.add_argument("trip", help="path to the trip folder (contains trip.json)")
    ap.add_argument("--check", action="store_true",
                    help="parse and report without writing any files")
    args = ap.parse_args()

    trip_dir = os.path.abspath(args.trip.rstrip("/"))
    if not os.path.isdir(trip_dir):
        sys.exit("not a directory: %s" % trip_dir)

    raw_cfg, dinners = load_trip(trip_dir)
    if not dinners:
        sys.exit("no notes found in %s" % trip_dir)
    cfg = merge(DEFAULTS, raw_cfg)

    stats = {
        "questions": total(dinners, "questions"),
        "loops": total(dinners, "loops"),
        "theories": total(dinners, "theories"),
        "quotes": total(dinners, "quotes"),
        "dinners": len(dinners),
    }
    threads = find_threads(dinners, cfg.get("threads"), cfg.get("thread_min_sittings", 2))

    print("%s -- %d dinners" % (cfg["title"], len(dinners)))
    for d in dinners:
        missing = [k for k in ("setting", "quotes", "questions") if not d.get(k)]
        flag = "   <-- empty: " + ",".join(missing) if missing else ""
        print("  %-14s %-22s %s  q=%-3d ?=%-3d%s" % (
            d["slug"], d["venue"][:22], d["date"] or "no-date",
            len(d["quotes"]), len(d["questions"]), flag))
    print("  totals: %(quotes)d lines, %(questions)d unanswered, "
          "%(loops)d loops, %(theories)d claims" % stats)
    if threads:
        print("  threads: " + ", ".join("%s (%d)" % (l, len(h)) for l, h in threads))
    for label in (cfg.get("threads") or {}):
        if label not in [l for l, _ in threads]:
            print("  note: thread %r below the %d-sitting cutoff" % (
                label, cfg.get("thread_min_sittings", 2)))

    if args.check:
        print("\n--check: nothing written")
        return

    data_dir = os.path.join(trip_dir, "_data")
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, "dinners.json"), "w") as f:
        json.dump(dinners, f, indent=2, ensure_ascii=False)

    pages = [
        ("index.html", build_home(cfg, dinners, threads)),
        ("record.html", build_record(cfg, dinners, stats)),
        ("cold-cases.html", build_cold(cfg, dinners, stats)),
        ("canon.html", build_canon(cfg, dinners, stats)),
        ("quotable.html", build_quotable(cfg, dinners, stats)),
    ]
    os.makedirs(os.path.join(trip_dir, "dinners"), exist_ok=True)
    for i, d in enumerate(dinners):
        pages.append((os.path.join("dinners", d["slug"] + ".html"),
                      build_dinner(cfg, dinners, i)))

    for name, content in pages:
        with open(os.path.join(trip_dir, name), "w") as f:
            f.write(content)

    print("\nwrote %d pages to %s" % (len(pages), trip_dir))


if __name__ == "__main__":
    main()
