"""Documentation-contract tests for this repository's agent customization tree.

The restructure produced sixteen skills, nine instruction files, three agent
definitions, one reference file, and two mirrored prompts. The properties that
keep that tree coherent — every documented command exists, each skill stays
inside its budget, every asset is routed from its ``SKILL.md``, the prompt
mirror is the prompt directory itself — hold only because every author was
careful. Each test below turns one property into a contract, reports every
violation at once, and names the file and the rule that broke.

Every contract reads a structure and never searches prose. ``package.json``
goes through `json`, frontmatter and the payee data files through
`pydantic_yaml`, the budget table through the fenced block that carries it,
headings and table rows through the lines that state them, prelude payees
through the directive each line spells, and the assets a ``SKILL.md`` routes
through the link targets and inline-code spans it quotes. A formatting change
moves none of those, so a green run states that the structure holds rather than
that some phrase survived a search.
"""

import json
import os
import re
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from pydantic import BaseModel, RootModel
from pydantic_yaml import parse_yaml_raw_as

from scripts import clopen

"""Public symbols exported by this module (none)."""
__all__ = ()

"""The repository root, resolved from this test file's own location."""
REPO_ROOT = Path(__file__).parents[2]

"""The agent-customization tree every contract below governs."""
AGENTS_DIR = REPO_ROOT / ".agents"

"""The prompt sources, which the OpenCode command mirror must copy byte for byte."""
PROMPTS_DIR = AGENTS_DIR / "prompts"

"""The OpenCode command mirror, a tracked symlink to the prompt sources."""
MIRROR_DIR = REPO_ROOT / ".opencode" / "commands"

"""The instruction file that owns the skill layout, budgets, and data conventions."""
SKILL_AUTHORING = AGENTS_DIR / "instructions" / "skill-authoring.instructions.md"

"""The header of the budget table, as its cells read once split into words."""
BUDGET_HEADER = ("skill", "SKILL.md", "<=", "lines")

"""The header of `AGENTS.md`'s command table, in the order it declares."""
COMMAND_TABLE_HEADER = ("command", "use when")

"""The prefix every owner-run maintenance command begins with."""
MAINTENANCE_PREFIX = "uv run --locked -m scripts.clopen"

"""The command spellings this repository retired; no table cell may name one."""
RETIRED_COMMANDS = ("clopen", "verify:migration", "clopen_verify")

"""The retired names that would be a `package.json` script rather than a module."""
RETIRED_SCRIPTS = ("clopen", "verify:migration")

"""The frontmatter keys that make a file an agent definition."""
_AGENT_KEYS = ("model", "tools")

"""The sections an `ingest-*` aspect runs, in the order `skill-authoring` states."""
_ASPECT_SECTIONS = (
    "When to use",
    "Rules",
    "Procedure",
    "Worked example",
    "Stop and ask",
)

"""The sections `add-payee` runs: the same five, with the questions before the example."""
_PAYEE_SECTIONS = (
    "When to use",
    "Rules",
    "Procedure",
    "Stop and ask",
    "Worked example",
)

"""The fence that opens and closes a markdown code block."""
_FENCE = "```"

"""The tail of a markdown link, read as the target it points at."""
_LINK_TARGET = re.compile(r"\]\(([^)\s]+)\)")

"""A markdown inline-code span, read as the text it quotes."""
_CODE_SPAN = re.compile(r"`([^`\n]+)`")

"""The punctuation a table cell wraps a command spelling in."""
_CELL_PUNCTUATION = "`*_()[],.;:'\""


class _Frontmatter(RootModel[dict[str, str]]):
    """A document's frontmatter block: a flat ``key: value`` mapping."""


class _IdentifierOrdering(BaseModel):
    """One payee's identifier orders and the regex hint each identifier has."""

    orders: list[list[str]]
    regex: dict[str, str]


class _IdentifierMappings(RootModel[dict[str, _IdentifierOrdering]]):
    """The id mappings data file: each payee and its identifier shapes."""


def _read(document: Path) -> str:
    """Return ``document``'s text."""
    return document.read_text(encoding="utf-8")


def _relative(path: Path) -> str:
    """Return ``path`` as the repository-relative string a message quotes."""
    return path.relative_to(REPO_ROOT).as_posix()


def _report(document: Path, detail: str) -> str:
    """Name one violation by the file it is in and the defect it is."""
    return f"{_relative(document)}: {detail}"


def _check(rule: str, violations: list[str]) -> None:
    """Assert a contract found nothing, naming its rule and every offender."""
    detail = "\n".join(f"- {violation}" for violation in violations)
    assert not violations, f"{rule}: {len(violations)} violation(s)\n{detail}"


def _fenced_blocks(text: str) -> list[tuple[str, str]]:
    """Return each fenced block as its opening line and the text it encloses."""
    blocks: list[tuple[str, str]] = []
    opener: str | None = None
    body: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith(_FENCE):
            if opener is None:
                opener = line.strip()
            else:
                blocks.append((opener, "\n".join(body)))
                opener, body = None, []
        elif opener is not None:
            body.append(line)
    if opener is not None:
        blocks.append((opener, "\n".join(body)))
    return blocks


def _unfenced(text: str) -> str:
    """Return ``text`` without the lines that any fenced block encloses."""
    kept: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.lstrip().startswith(_FENCE):
            inside = not inside
        elif not inside:
            kept.append(line)
    return "\n".join(kept)


def _table_rows(text: str, header: tuple[str, ...]) -> list[tuple[str, ...]]:
    """Return the data rows of the table whose header cells are ``header``.

    A row is read as the cells it states: the line is split on ``|``, each cell
    is stripped, and the separator row is dropped. ``header`` is matched
    case-insensitively, and the table ends at the first line that is no row.
    """
    rows: list[tuple[str, ...]] = []
    inside = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            inside = False
            continue
        cells = tuple(cell.strip() for cell in stripped.strip("|").split("|"))
        if not inside:
            inside = tuple(cell.lower() for cell in cells) == header
            continue
        if all(cell and set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)
    return rows


def _frontmatter(document: Path) -> dict[str, str]:
    """Return ``document``'s frontmatter, parsed as a flat YAML mapping.

    The block is the text between the first two ``---`` lines, and a file that
    does not open with one has none. The block is a mapping of scalars, so a
    block that is anything else fails the contract's parse instead of being
    read as loose text; an unclosed block is no frontmatter at all.
    """
    lines = _read(document).splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    block: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            return parse_yaml_raw_as(_Frontmatter, "\n".join(block)).root
        block.append(line)
    return {}


def _skill_dirs() -> list[Path]:
    """Return every skill directory, sorted by name."""
    skills = (AGENTS_DIR / "skills").iterdir()
    return sorted(entry for entry in skills if entry.is_dir())


def _sections(text: str) -> list[str]:
    """Return ``text``'s second-level headings, in file order, outside any fence."""
    return [
        line.removeprefix("## ").strip()
        for line in _unfenced(text).splitlines()
        if line.startswith("## ")
    ]


def _file_names(directory: Path) -> set[str]:
    """Return the names of the files one prompt directory holds."""
    return {path.name for path in directory.iterdir() if path.is_file()}


def _skill_budget() -> tuple[dict[str, int], list[str]]:
    """Return each skill's line budget and every row the table states badly.

    The table is the one fenced block under ``BUDGET_HEADER``, so each row is a
    skill name and a line count; a row of any other shape is reported here
    rather than skipped, and a table declared twice leaves no budget to check.
    """
    blocks = [body.splitlines() for _, body in _fenced_blocks(_read(SKILL_AUTHORING))]
    tables = [
        lines for lines in blocks if lines and lines[0].split() == list(BUDGET_HEADER)
    ]
    if len(tables) != 1:
        return {}, [f"the budget table is declared {len(tables)} times"]
    budget: dict[str, int] = {}
    malformed: list[str] = []
    for line in tables[0][1:]:
        parts = line.split()
        if not parts:
            continue
        if len(parts) == 2 and parts[1].isdigit():
            budget[parts[0]] = int(parts[1])
        else:
            malformed.append(f"`{line.strip()}` is not a skill name and a line count")
    return budget, malformed


def _named_files(text: str) -> set[str]:
    """Return the file names ``text`` names in a link target or an inline-code span.

    A link is read as the target it points at and a code span as the text it
    quotes, so a file counts as routed when the document links to it or quotes
    it, and prose that merely contains the name does not route it.
    """
    tokens = _LINK_TARGET.findall(text)
    tokens.extend(_CODE_SPAN.findall(text))
    return {Path(token).name for token in tokens}


def _retired_tokens(cell: str) -> list[str]:
    """Return the retired command spellings ``cell`` names, wherever it names them.

    A cell is split into the words it spells, so a retired name is caught as the
    word it is whether it follows ``bun run``, stands alone, or sits inside the
    module path of a deleted file.
    """
    words = (word.strip(_CELL_PUNCTUATION) for word in cell.replace("`", " ").split())
    return sorted(
        word for word in words if word in RETIRED_COMMANDS or "clopen_verify" in word
    )


def _clopen_accepts(argv: list[str]) -> bool:
    """Report whether ``scripts/clopen.py``'s own parser accepts ``argv``.

    The subcommand names are the CLI's to state, so a documented invocation is
    handed to the parser rather than compared with a list kept here. The parser
    prints its usage before exiting, which the capture keeps out of a report.
    """
    with redirect_stderr(StringIO()):
        try:
            clopen.parser().parse_args(argv)
        except SystemExit:
            return False
    return True


def _command_violations(document: Path, cell: str, scripts: set[str]) -> list[str]:
    """Return every defect in one command-table cell's first column."""
    spelled = cell.strip("`").strip()
    words = spelled.split()
    if words[:2] == ["bun", "run"]:
        if len(words) < 3:
            return [_report(document, f"`{spelled}` names no script")]
        name = words[2]
        if name in scripts:
            return []
        return [_report(document, f"`bun run {name}` names no `package.json` script")]
    if spelled.startswith(MAINTENANCE_PREFIX):
        argv = spelled.removeprefix(MAINTENANCE_PREFIX).split()
        if not argv:
            return [_report(document, f"`{spelled}` names no subcommand")]
        if _clopen_accepts(argv):
            return []
        return [_report(document, f"`{spelled}` is no `scripts.clopen` invocation")]
    return [_report(document, f"`{spelled}` names no command this repository keeps")]


def _payee_directives(prelude: Path) -> list[tuple[int, str]]:
    """Return each ``payee`` directive's line number and value, in file order.

    The prelude grammar is one directive per line, so a line declares a payee
    when its first word is ``payee`` and its value is the rest of the line.
    """
    directives: list[tuple[int, str]] = []
    for number, line in enumerate(_read(prelude).splitlines(), 1):
        directive = line.split(maxsplit=1)
        if len(directive) == 2 and directive[0] == "payee":
            directives.append((number, directive[1]))
    return directives


def _preludes() -> list[Path]:
    """Return every prelude journal, sorted by name."""
    return sorted((REPO_ROOT / "preludes").glob("*.journal"))


def _declared_payees() -> set[str]:
    """Return every payee name the preludes declare."""
    return {name for prelude in _preludes() for _, name in _payee_directives(prelude)}


def _payee_declaration_violations() -> list[str]:
    """Return every prelude payee block out of byte order or repeating a name."""
    violations: list[str] = []
    for prelude in _preludes():
        where = _relative(prelude)
        directives = _payee_directives(prelude)
        for (number, name), (earlier, previous) in zip(directives[1:], directives):
            if name == previous:
                violations.append(f"{where}:{number}: `{name}` repeats line {earlier}")
            elif name < previous:
                violations.append(
                    f"{where}:{number}: `{name}` sorts before `{previous}`"
                )
    return violations


def _unparseable(error: Exception) -> list[str]:
    """Report a document the YAML reader refused, by the error it raised.

    ``pydantic_yaml`` declares no error type of its own: a shape violation
    arrives as pydantic's ``ValidationError`` and a syntax error from the reader
    ``pydantic_yaml`` wraps, which no manifest here declares. A repeated key is
    one of those syntax errors, so duplicates are reported here too. Both are
    reported as one violation rather than escaping the contract as a traceback.
    """
    return [f"does not parse: {error}"]


def _payee_mapping_violations(text: str) -> list[str]:
    """Return every mapping whose target no prelude declares or that maps to itself."""
    try:
        mappings = parse_yaml_raw_as(RootModel[dict[str, list[str]]], text).root
    except Exception as error:
        return _unparseable(error)
    declared = _declared_payees()
    violations: list[str] = []
    for alias, targets in sorted(mappings.items()):
        for target in targets:
            if target == alias:
                violations.append(f"`{alias}` maps to itself")
            elif target not in declared:
                violations.append(f"`{alias}` maps to undeclared `{target}`")
    return violations


def _id_mapping_violations(text: str) -> list[str]:
    """Return every defect in one payee id-mapping document's shape."""
    try:
        mappings = parse_yaml_raw_as(_IdentifierMappings, text).root
    except Exception as error:
        return _unparseable(error)
    violations: list[str] = []
    for payee, ordering in sorted(mappings.items()):
        if not all(ordering.orders):
            violations.append(f"`{payee}`: an `orders` row is empty")
        violations.extend(
            f"`{payee}`: `orders` names `{name}`, which `regex` does not define"
            for order in ordering.orders
            for name in order
            if name not in ordering.regex
        )
        for name, pattern in sorted(ordering.regex.items()):
            try:
                re.compile(pattern)
            except re.error as error:
                violations.append(f"`{payee}`: `regex.{name}`: {error}")
    return violations


def test_agents_command_table_matches_package_json() -> None:
    """Assert every documented command exists and no retired spelling survives.

    `AGENTS.md`'s table is the agent-facing command surface, so it is read cell
    by cell: a `bun run` cell must name a `package.json` script, an owner-run
    cell must name an invocation `scripts/clopen.py` accepts, and no cell may
    spell a retired command — the bare name included, which a contract phrased
    around the `bun run` form alone could not see.
    """
    agents_md = REPO_ROOT / "AGENTS.md"
    package_json = REPO_ROOT / "package.json"
    scripts = set(json.loads(_read(package_json))["scripts"])
    rows = _table_rows(_read(agents_md), COMMAND_TABLE_HEADER)
    violations: list[str] = []
    if not rows:
        violations.append(_report(agents_md, "declares no command table"))
    for row in rows:
        if len(row) != len(COMMAND_TABLE_HEADER):
            violations.append(
                _report(
                    agents_md,
                    f"the row `{row[0].strip('`')}` states {len(row)} cells",
                )
            )
            continue
        violations.extend(_command_violations(agents_md, row[0], scripts))
        violations.extend(
            _report(agents_md, f"the cell `{cell.strip('`')}` names `{token}`")
            for cell in row
            for token in _retired_tokens(cell)
        )
    violations.extend(
        _report(package_json, f"`{name}` must not be an agent command")
        for name in RETIRED_SCRIPTS
        if name in scripts
    )
    _check(
        "every documented command must exist, and no retired spelling may return",
        violations,
    )


def test_skill_frontmatter_and_budget() -> None:
    """Assert each skill names itself and its `SKILL.md` fits its budget.

    Rows are recognized by shape — a name and a line count — and compared with
    the tree in both directions, so a missing row and a stray row both fail.
    """
    budget, malformed = _skill_budget()
    skills = {skill.name: skill for skill in _skill_dirs()}
    violations = [_report(SKILL_AUTHORING, detail) for detail in malformed]
    for name, skill in sorted(skills.items()):
        document = skill / "SKILL.md"
        if not document.is_file():
            violations.append(_report(document, "missing"))
            continue
        fields, lines = _frontmatter(document), len(_read(document).splitlines())
        if fields.get("name") != name:
            violations.append(_report(document, f"`name` must be `{name}`"))
        if not 0 < len(fields.get("description", "")) <= 1024:
            violations.append(_report(document, "`description` is empty or too long"))
        if name not in budget:
            violations.append(_report(document, "has no row in the budget table"))
        elif lines > budget[name]:
            violations.append(
                _report(document, f"{lines} lines, budget {budget[name]}")
            )
    violations.extend(
        _report(SKILL_AUTHORING, f"`{name}` is no skill")
        for name in sorted(set(budget) - set(skills))
    )
    _check("every skill declares itself and keeps its line budget", violations)


def test_aspect_skills_run_the_five_sections_in_order() -> None:
    """Assert each aspect and `add-payee` runs its sections as the skeleton rule states.

    `skill-authoring` fixes the order for the twelve aspects and for `add-payee`,
    which puts its questions before its example, so thirteen skills are asserted;
    `ingest`, `fix-journals`, and `migrate` are task-shaped and take the sections
    their job needs, and a rule a test can assert must not live only in prose.
    """
    targets = [
        (skill.name, _ASPECT_SECTIONS)
        for skill in _skill_dirs()
        if skill.name.startswith("ingest-")
    ]
    targets.append(("add-payee", _PAYEE_SECTIONS))
    violations: list[str] = []
    for name, expected in targets:
        document = AGENTS_DIR / "skills" / name / "SKILL.md"
        sections = _sections(_read(document))
        missing = [section for section in expected if section not in sections]
        violations.extend(
            _report(document, f"has no `## {section}` section") for section in missing
        )
        present = [section for section in sections if section in expected]
        if not missing and present != list(expected):
            violations.append(
                _report(
                    document,
                    f"runs {', '.join(present)}; the rule states {', '.join(expected)}",
                )
            )
    _check(
        "each aspect and `add-payee` must run its five sections in order", violations
    )


def test_every_skill_asset_is_routed() -> None:
    """Assert every asset beside a `SKILL.md` is named in it.

    A name counts as routed when the `SKILL.md` links to the file or quotes it as
    inline code, so the contract reads the spans the document parses into and
    not its prose: a sentence that happens to contain an asset's name routes
    nothing.
    """
    violations: list[str] = []
    for skill in _skill_dirs():
        document = skill / "SKILL.md"
        if not document.is_file():
            violations.append(_report(document, "missing, so it routes no asset"))
            continue
        named = _named_files(_read(document))
        violations.extend(
            _report(asset, f"is not named in {_relative(document)}")
            for asset in sorted(skill.rglob("*"))
            if asset.is_file() and asset.name != "SKILL.md" and asset.name not in named
        )
    _check("every skill asset must be routed from its `SKILL.md`", violations)


def test_prompt_mirror_is_the_prompt_directory() -> None:
    """Assert `.opencode/commands` is the prompt directory, or a byte-identical copy.

    The mirror is a tracked symlink, so reading both paths compares one inode
    with itself and a byte comparison could never fail. The contract therefore
    checks where a symlink points, and asks for matching names and bytes only
    when the mirror is a real directory: replacing the link with a stale copy is
    the regression, and it fails here.
    """
    violations: list[str] = []
    sources = _file_names(PROMPTS_DIR)
    if not sources:
        violations.append(_report(PROMPTS_DIR, "holds no prompt"))
    if MIRROR_DIR.is_symlink():
        if MIRROR_DIR.resolve() != PROMPTS_DIR.resolve():
            violations.append(
                _report(
                    MIRROR_DIR,
                    f"links to `{os.readlink(MIRROR_DIR)}`, not the prompt directory",
                )
            )
    elif not MIRROR_DIR.is_dir():
        violations.append(
            _report(MIRROR_DIR, "is neither the prompt directory nor a copy of it")
        )
    else:
        mirrors = _file_names(MIRROR_DIR)
        if not mirrors:
            violations.append(_report(MIRROR_DIR, "holds no prompt"))
        violations.extend(
            _report(MIRROR_DIR / name, "has no source prompt")
            for name in sorted(mirrors - sources)
        )
        violations.extend(
            _report(PROMPTS_DIR / name, "has no mirror")
            for name in sorted(sources - mirrors)
        )
        violations.extend(
            _report(MIRROR_DIR / name, f"differs from its source `{name}`")
            for name in sorted(sources & mirrors)
            if (PROMPTS_DIR / name).read_bytes() != (MIRROR_DIR / name).read_bytes()
        )
    _check(
        "`.opencode/commands` must be the prompt directory or a byte-identical copy",
        violations,
    )


def test_no_agent_frontmatter_in_skill_dirs() -> None:
    """Assert no skill asset or reference file reads as an agent definition.

    An agent definition lives in `.agents/agents/` alone, must state its `name`
    and `description`, and must take `model: inherit`: the project allows no other
    model scope, and a literal model id would abort every dispatch.
    """
    assets = [
        path
        for skill in _skill_dirs()
        for path in sorted(skill.rglob("*"))
        if path.is_file() and path.name != "SKILL.md"
    ]
    assets.extend(p for p in (AGENTS_DIR / "reference").rglob("*") if p.is_file())
    violations = [
        _report(document, f"carries `{key}`, so it reads as an agent definition")
        for document in assets
        for key in _AGENT_KEYS
        if key in _frontmatter(document)
    ]
    for document in sorted((AGENTS_DIR / "agents").glob("*.md")):
        fields = _frontmatter(document)
        violations.extend(
            _report(document, f"frontmatter `{key}` is missing")
            for key in ("name", "description")
            if not fields.get(key)
        )
        model = fields.get("model", "absent")
        if model != "inherit":
            violations.append(_report(document, f"`model` is `{model}`, not `inherit`"))
    _check(
        "agent definitions live in `.agents/agents/` and take `model: inherit`",
        violations,
    )


def test_instructions_have_apply_to() -> None:
    """Assert every instruction file declares a name, a description, and a scope."""
    documents = sorted((AGENTS_DIR / "instructions").glob("*.md"))
    _check(
        "every instruction file must declare what it is and where it applies",
        [
            _report(document, f"frontmatter `{key}` is missing or empty")
            for document in documents
            for key in ("name", "description", "applyTo")
            if not _frontmatter(document).get(key)
        ],
    )


def test_mapping_targets_are_declared_payees() -> None:
    """Assert every payee mapping names a declared payee and none maps to itself."""
    document = AGENTS_DIR / "skills" / "ingest" / "payee_mappings.yml"
    _check(
        "every mapping target must be a declared payee, and no alias maps to itself",
        [_report(document, d) for d in _payee_mapping_violations(_read(document))],
    )


def test_id_mapping_shapes() -> None:
    """Assert the id mappings parse, keep unique keys, and name compilable regexes."""
    document = AGENTS_DIR / "skills" / "ingest" / "id_mappings.yml"
    _check(
        "each payee's identifier orders must name regexes it defines",
        [_report(document, d) for d in _id_mapping_violations(_read(document))],
    )


def test_payee_declarations_are_ordered_and_unique() -> None:
    """Assert each prelude's payee block is in strict byte order and free of repeats.

    The contract covers both properties because `.agents/skills/add-payee/SKILL.md`
    mandates them together, and the duplicate is the more dangerous of the two:
    two declarations of one merchant is how a payee silently splits in two.
    """
    _check(
        "every prelude's `payee` declarations must be in strict byte order and unique",
        _payee_declaration_violations(),
    )
