# CLAUDE.md

Terminal Note (`note`): a single-user CLI for tasks and journaling, stored as
plain text. Goals and roadmap (MVP → v1 → v2) are in
`Documentations/project_spec.md`; `Documentations/brainstorm.md` is the original
idea (Turkish). The MVP is implemented; check the spec for a feature's version
before adding it.

## Running

```sh
bin/note <entity> <action> [flags]     # or: python3 main.py ...
bin/note domain add iş
bin/note task add "PR'ı incele" -d iş -t frontend --date tomorrow
bin/note today
```

Tests: `python3 -m unittest discover -s tests -t .` (no linter or build step).

**Every command touches real user data** in `~/Documents/note/`, which is
hardcoded via `Path.home()`. When trying things out, use a throwaway home:

```sh
HOME="$(mktemp -d)" bin/note domain add test
```

## Architecture

`bin/note` → `main.py` → `termnote/cli.py` (argparse, entity then action).

- `cli.py`: parsing and dispatch; prints results. Handlers raise `ValueError`
  for user errors, which `main` prints to stderr with exit code 1.
- `tasks.py`: task line parse/format, ID assignment, queries
- `domains.py`, `config.py`: registered domains and `last_id` (INI)
- `journal.py`: append/list per-day entries
- `today_view.py`: combined today + overdue + journal output
- `dates.py`: all date parsing/formatting
- `storage.py`: all paths; add new ones here

## Rules to preserve

- Python stdlib only.
- Task line: `- [ ] text (DD-MM-YYYY) @domain #tag ^id`. Metadata tokens may
  appear in any order, because users hand-edit these files in vim.
  Tokens must be whitespace-delimited; the last date, `@` and `^` win and earlier
  ones are text.
- Never rewrite lines that aren't being changed: `add` appends, `done` edits only
  the checkbox. Lines that aren't tasks must survive.
- IDs are global and never reused:
  `max(config.last_id, highest id in tasks.md) + 1`.
- At most 3 domains; `task add` rejects unregistered ones and never creates them.
- Dates are `DD-MM-YYYY` for input and task lines. Journal filenames are ISO
  (`YYYY-MM-DD.md`) so they sort. Some spec examples disagree; follow the code.

## Known issues

- A standalone `#word` in task text is always read as a tag.
- Domain and tag names aren't validated (spaces, commas, `%`).
- Files are opened without an explicit encoding, though content is Turkish.
- File writes are not atomic.
