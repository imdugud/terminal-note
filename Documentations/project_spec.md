# Terminal Note — Project Spec

## Product Requirements

### Who is the product for

A single user (the author) who works primarily in the terminal and wants to
capture tasks, daily journal entries, and (later) ideas and calendar events
without leaving the shell. It is not designed as a multi-user or shared tool —
the data is personal, local, and plain text.

### What problems does it solve

- Context-switching to a separate note/task app breaks focus; capturing a
  thought or task should take one command, not an app switch.
- Task lists tend to sprawl and lose focus. Capping active work to at most 3
  domains keeps the list small and intentional instead of infinite.
- "What do I need to do today?" should be answerable with a single command,
  combining today's tasks, overdue tasks, and today's journal entries.
- Notes/tasks locked inside a proprietary app or database format aren't truly
  owned by the user. Plain text that can be read, searched, and edited with
  any standard tool (vim, cat, grep) keeps the data portable and legible.
- The tool should be small enough to understand fully and grow step by step,
  rather than being designed upfront as a large system.

### What the product does

**MVP**

- `domain add` / `domain list` — register up to 3 domains (categories) for
  tasks; domains must be registered before they can be used.
- `task add "<text>" -d <domain> [-t <tag> ...] [--date today|tomorrow|gün.ay.yıl]`
  — add a task to a required domain, with optional tags and an optional date
  (defaults to today).
- `task list today` — list today's tasks.
- `task done <id>` — mark a task complete by its ID.
- `journal add "<text>"` — append a timestamped journal entry for today.
- `journal list today` — list today's journal entries.
- `today` — combined view of today's + overdue tasks and today's journal
  entries.
- `help` — list available commands.
- All data is stored in plain, human-readable text files with persistent,
  never-reused IDs.

**v1**

- `task edit`, `task remove`, `task undone`.
- Task filters: `week`, `overdue`, `all`, `-d <domain>`.
- Journal listing by arbitrary date, not just today.
- `domain remove`, with a rule for reassigning/moving any tasks still
  assigned to that domain.
- Tags (`-t`) and `tag list`.
- Date validation.

**v2**

- Calendar: `add`, `list week/month`, `edit`, `remove`, optional time of day.
- Ideas: `add`, `list`, `remove`, and idea → task conversion.
- Calendar entries folded into the `today` view.
- General `search` across tasks, journal, and ideas.

**Later**

- Short command aliases.
- Git-based backup/sync of the `~/Documents/note/` directory.
- Recurring events.
- Markdown export.
- Colored output.

## Technical Design

### Technologies used

- **Python 3** — the implementation language, chosen over a shell script for
  reliable text/date parsing and filtering logic needed from v1 onward, and
  over a compiled binary (Go/Rust) to keep iteration fast and the codebase
  easy to read and modify by hand. Startup overhead (~tens of ms) is
  negligible for a command run a few times a day.
- **Thin shell wrapper/alias** — a shell function or alias named `note` that
  invokes the Python entry point (e.g. `note() { python3 ~/bin/termnote/main.py "$@"; }`),
  so the tool is invoked like any other terminal command without leaving the
  shell.
- **`argparse` (stdlib)** — parses the `note <entity> <action> [flags]`
  command structure via two-level subparsers (entity, then action), with
  `-t` using `action="append"` to collect repeated tags.
- **`configparser` (stdlib)** — reads/writes the `config` file. Chosen over
  JSON/YAML to avoid external dependencies and because INI syntax is more
  forgiving of manual edits (tolerates comments and formatting slips that
  would break strict JSON).
- No third-party dependencies are required for the MVP/v1/v2 scope.

### Architecture

- **Entry point**: the `note` shell alias calls the Python CLI, which parses
  the command via `argparse` and dispatches to an entity-specific handler
  (`task`, `journal`, `domain`, `today`, `help`).
- **Storage layer**: all state lives under `~/Documents/note/` as plain text files.
  Each command handler reads the relevant file(s) fully into memory, applies
  the requested operation, and rewrites the file. The dataset size expected
  for personal use makes full read/rewrite simple and sufficient — no
  database or incremental indexing is needed.
- **Parsing strategy**: task lines are parsed by extracting metadata tokens
  (date, domain, tags, ID) from anywhere in the line via regex, independent
  of their order or position, rather than matching a strict fixed-order
  pattern. This is a deliberate choice to tolerate hand-editing: if the user
  manually edits a line in vim (reorders tokens, deletes a tag, adds a blank
  line), the parser degrades gracefully instead of breaking, with missing
  fields simply coming back empty.
- **ID assignment (self-healing)**: IDs are global (not scoped per domain)
  and monotonically increasing, and are never reused after a task is
  removed. On every `task add`, the next ID is computed as
  `max(config.last_id, max ^id found by scanning tasks.md) + 1`, rather than
  trusting the stored counter alone. This guards against drift if the user
  hand-edits `tasks.md` and introduces an ID higher than what `config`
  currently tracks, preventing future collisions.
- **Validation boundary**: `task add` hard-errors if `-d <domain>` is not
  already registered via `domain add` — domains are never auto-created
  on the fly. This keeps the "max 3 domains" constraint meaningful and
  enforced in one place.

### File format

All data lives under `~/Documents/note/`:

```
~/Documents/note/
  config               # domain list, last-used ID counter (INI format)
  tasks.md              # all tasks, across all domains
  calendar.md            # calendar entries (v2)
  ideas.md              # ideas (v2)
  journal/
    2026-10-17.md        # one file per day of journal entries
    2026-10-18.md
```

**`config`** (INI, via `configparser`):

```ini
[note]
domains = iş, kişisel, sağlık
last_id = 43
```

**`tasks.md`** — one task per line, Markdown task-list syntax as the base,
with inline metadata tokens in any order:

```
- [ ] PR'ı incele (2026-10-18) @iş #frontend #acil ^43
- [x] Haftalık raporu yaz (2026-10-15) @iş ^41
```

- `- [ ]` / `- [x]` — done state; doubles as both the CLI's and the human's
  way of marking a task complete, since toggling the `x` by hand in vim has
  the same effect as `task done <id>`.
- `(DD-MM-YYYY)` — task date.
- `@domain` — required, single-value, must be a registered domain.
- `#tag` — optional, repeatable.
- `^id` — the persistent, globally unique, never-reused ID.

Metadata tokens are recognized by their leading character (`(`, `@`, `#`,
`^`) and can appear in any order within the line; whatever remains after
stripping recognized tokens is the task's text.

**`journal/DD-MM-YYYY.md`** — one entry per line, no ID (journal entries are
never individually addressed by `edit`/`remove`, only listed by day):

```
- 14:32 Bugün odaklanmak zordu
- 23:58 Deploy script'i düzelttim
```

`.md` is used as the extension for `tasks.md`, `calendar.md`, `ideas.md`, and
journal files so that any Markdown-aware editor renders checkboxes and lists
correctly; `config` intentionally has no extension since it is structured
state rather than prose meant to be read directly.
