# papers

Turns a folder of Granola dinner notes into a static "case file" site: the
dinners themselves, plus pages that cut *across* them (every unanswered
question, every unverified claim, every good line).

Built for [the_wilmington_papers](../../the_wilmington_papers/), but nothing in
here is specific to that trip. A new trip is a folder and a `trip.json`.

## Adding a trip

```
mkdir -p the_reno_papers/granola_notes
# drop one .md per dinner into granola_notes/
# write the_reno_papers/trip.json          (public config, see below)
# write the_reno_papers/trip.private.json  (names to redact, gitignored)

python3 _tools/papers/build.py the_reno_papers --check   # parse, report, write nothing
python3 _tools/papers/build.py the_reno_papers           # write the pages

git ls-files the_reno_papers | xargs grep -il "<a real name>"   # expect no output
```

Run that last line before every push. It is the check that catches a name
reaching a tracked file, and it is cheap compared to un-publishing one.

Output lands in the trip folder: `index.html`, `record.html`,
`cold-cases.html`, `canon.html`, `quotable.html`, and `dinners/<slug>.html`.
Jekyll passes these through untouched, so the folder is live at
`www.hjeeb.us/<trip>/` once pushed. Re-running is safe and idempotent — it
overwrites its own output and never edits the notes.

`_data/dinners.json` is also written: the parsed notes as structured data, handy
for grepping or feeding something else. It stays out of git along with the notes.

## trip.json

Every reader-visible string comes from here. All keys are optional except that
you'll want a `title`.

Anything holding a real name or a verbatim quote belongs in
`trip.private.json`, which is gitignored and merged over this file at build
time. The `file` column says where each key goes.

| key | file | what it does |
| --- | --- | --- |
| `title` | public | Site title, `<title>` suffix, footer |
| `tagline` | public | Home-page dek and meta description |
| `footer` | public | Second footer segment, e.g. `field notes, Aug 2026` |
| `notes_dir` | public | Notes subfolder (default `granola_notes`) |
| `noindex` | public | `true` adds `<meta name="robots" content="noindex,nofollow">` |
| `order` | public | Slugs in reading order; omit to sort by date |
| `venues` | public | Per-slug `{name, kind, date}` overrides |
| `facts` | public | Extra masthead counts: `[{n, label}]` |
| `closing_stat` | public | Fourth home stat `{n, label}`; omit for a computed one |
| `threads` | public | `{label: regex}` — recurring subjects to track |
| `thread_min_sittings` | public | Sittings a thread needs to appear (default 2) |
| `sections` | public | Per-page `kicker` / `title` / `dek` overrides |
| `drop_sections` | public | Section field names to omit entirely |
| `hero_quote` | **private** | Prefix of the line to feature as Exhibit A |
| `companion_aliases` | **private** | `{"Real Name": ["variant", ...]}` spelling fixes |
| `redact_names` | **private** | `{"Real Name": "stand-in"}` replacements |
| `suppress` | **private** | Patterns whose matching entries are withheld |

`drop_sections` is public because a field name reveals nothing; `suppress`
patterns are private because they quote the text they are withholding.

`dek` strings may reference `{questions}`, `{loops}`, `{theories}`,
`{quotes}`, and `{dinners}`.

Minimum viable config:

```json
{
  "title": "The Reno Papers",
  "tagline": "Four nights. Nothing was resolved.",
  "threads": { "the bet": "blackjack|the bet" }
}
```

## Privacy

The notes are the private source; only generated pages are published. These are
gitignored and excluded from the Jekyll build:

- `<trip>/granola_notes/` — the raw notes
- `<trip>/_data/` — parsed note data, regenerate any time
- `<trip>/trip.private.json` — real names and suppression patterns

That last one matters: a name-to-initial map is a decoder ring for the redacted
pages, so publishing it would defeat the redaction. Keep it out of the repo.
`trip.private.json` is merged over `trip.json` at build time (dicts merge, lists
concatenate), so put anything sensitive there and nothing else changes.

Three controls, applied in this order:

| key | effect |
| --- | --- |
| `suppress` | Drops individual entries matching a substring or regex, leaving the rest of the section intact |
| `redact_names` | Replaces `{"Real Name": "stand-in"}` throughout, longest name first |
| `drop_sections` | Omits whole sections by field name, e.g. `["undercurrent"]` |

`suppress` runs before `redact_names` so patterns match the original wording.
Replacements are word-bounded and case-sensitive, and obvious artifacts (`B..`,
`the server the server`) are cleaned up automatically.

After changing any of this, audit what would actually ship:

```
git ls-files <trip> | xargs grep -il "<a real name>"
```

Expect no matches.

### Redact before the first push

Redaction only shapes generated output. It cannot retract anything already
pushed, and checking the current working tree is not enough — **every past
commit is still readable.** Pages generated before a redaction rule existed keep
the un-redacted text in their history, so a repo whose tip is clean can still
serve the original wording from an earlier commit.

To audit history rather than just the tip:

```
git log --remotes --oneline -S "<a real name>"   # what is actually published
git log --all --oneline -S "<a real name>"       # includes local-only commits
```

Use `--remotes` to answer "is this public?". Prefer `--all` only when you also
want local commits — after a squash and force-push the replaced commits linger in
your own reflog until git collects them, so `--all` reports names that are no
longer reachable from anywhere on the remote.

Any output from the `--remotes` form means the name is still published. On an
unmerged branch the fix is to squash to a single commit built from redacted
output and force-push; on shared history it is far more disruptive. Either way,
assume anything briefly public may have been fetched, forked, or cached.

Also note that a public repo serves the notes two ways: through the repo itself,
and through Jekyll, which renders `.md` files as pages. The gitignore entries
handle the first and the `exclude:` list in `_config.yml` handles the second.
Both are needed.

`noindex: true` in a trip's config adds `<meta name="robots" content="noindex,
nofollow">` to every page of that trip. Useful when the notes cover events that
are searchable in their own right — anonymizing the guests does nothing about
the incidents around them. It keeps the pages live and link-shareable while
keeping them out of results, and it is reversible with a rebuild.

## Deep links

Every quote, question, loop, claim, and side quest gets a stable `id`, so any
single item is linkable:

```
.../quotable.html#x-dbdd7262      one line
.../cold-cases.html#q-4a1c33f0    one unanswered question
.../canon.html#c-9e2b71dd         one claim
```

Hovering an item reveals a `#` handle carrying that URL. The prefix marks the
kind (`x` line, `q` question, `l` loop, `p` promised, `c` claim, `s` side
quest); the suffix is a hash of the item's own text.

Because the id derives from the text and not from position, it survives
reordering and new dinners, and the same quote has the same id on Quotable and
on its dinner page. Rewording an item does change its id — links to the old
wording will no longer resolve.

On Quotable, opening a `#x-...` URL shows that specific line instead of a
random one, and pulling a new line updates the address bar so whatever is on
screen is always what gets copied.

## What the parser expects

Granola's default export shape — an `# H1` venue name, a
`Sun, 09 Aug 26 · Companion Name` byline, then `### ` sections. Recognized
headings (see `SECTION_MAP` in `parse.py`):

`Attendees`, `Setting and Vibe`, `Main Conversation Threads`,
`Stories Started`, `Best Lines and Bits`, `Theories and Claims`,
`Side Quests`, `Emotional Undercurrents`, `Unanswered Questions`,
`Things People Promised To Send`, `Open Loops`, `Decisions or Plans`,
`Next Dinner`.

Anything else is kept and rendered at the bottom of that dinner's page rather
than dropped, so an unfamiliar section is visible instead of silently lost.

Handled automatically: missing sections, missing bylines, absent dates,
straight *and* curly quotes, attributions in trailing parentheses, speaker
lead-ins (`The server, on the burrata: "..."`), and notes accidentally pasted
several times in one file (identical repeats collapse to one).

Sections whose only content is a variant of "No firm decisions" render as quiet
italics instead of a one-item list.

## Files

- `build.py` — CLI, page generation
- `parse.py` — notes to structured records
- `theme.py` — inline CSS and page chrome
