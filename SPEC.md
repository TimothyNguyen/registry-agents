# SPEC — book-to-skill migration into registry-agents

Source: `../book-to-skill` (standalone repo). Target: `registry-agents/skills/book-to-skill/`.
Scope decided w/ user: skill + runtime deps only. ⊥ docs/, tests/, mkdocs site, graphify-out/, CHANGELOG, BACKERS, tools/validate_skill.py, tools/discovery_tax.py.

## §I — Invariants

I1: `skills/<name>/SKILL.md` ! exist ∀ skill in `scripts/build_manifests.py` SKILLS tuple → else `--check` fails silent-wrong.
I2: `manifests/core.yaml` generated file ∴ never hand-edit; regen via `py scripts/build_manifests.py` after any source payload change.
I3: book-to-skill frontmatter stays host-neutral across supported hosts (Copilot/Claude/Codex). ⊥ add registry-specific frontmatter fields; would break portability contract stated in SKILL.md's own host notes.
I4: `scripts/extract.py` sys.path-inserts `dirname(dirname(__file__))` → book_to_skill package ! sit 2 levels up from `scripts/extract.py`, i.e. @ `skills/book-to-skill/book_to_skill/`. Same for `tools/scan_generated_skill.py` (1 level up).
I5: copied package ! import-clean & runnable standalone (`py scripts/extract.py --check`, `py tools/scan_generated_skill.py --help`) before commit.
I6: README.md resource counts (agents/skills/MCP/plugin) ! match actual manifest doc count → run `py scripts/build_manifests.py --check` + eyeball counts after any add/remove.
I7: `build_manifests.py` SKILLS/AGENTS tuples ! stay in sync w/ `skills/`/`agents/` dirs on disk — adding a dir alone ∉ enough, tuple entry required.

## §T — Tasks

id\|status\|task\|cites
T1\|x\|copy SKILL.md, pyproject.toml, LICENSE.md → `skills/book-to-skill/`\|I3
T2\|x\|copy `book_to_skill/` package (incl. `parsers/`) verbatim\|I4,I5
T3\|x\|copy `scripts/extract.py`, `tools/scan_generated_skill.py`\|I4
T4\|x\|add `"book-to-skill"` to SKILLS tuple in `build_manifests.py`\|I1,I7
T5\|x\|regen `manifests/core.yaml`, verify `--check` passes\|I2,I6
T6\|x\|update README.md skill list + resource counts (6→7 skills)\|I6
T7\|x\|smoke-test `extract.py --check` & `scan_generated_skill.py --help` from new path\|I5
T8\|x\|`uv run tregistry apply -f manifests/core.yaml --dry-run` against live tregistry, confirm catalog shows 7 skills\|I1,I2

## §B — Bugs

id\|date\|cause\|fix
(none yet)
