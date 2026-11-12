"""Documentation-contract tests for this repository's agent customization tree.

The restructure produced sixteen skills, nine instruction files, three agent
definitions, one reference file, and two mirrored prompts. The properties that
keep that tree coherent — every documented command exists, no retired spelling
returns, each skill stays inside its budget, every asset is routed from its
``SKILL.md``, the prompt mirror is the prompt directory itself — hold only
because every author was careful. Each test below turns one property into a
contract, reports every violation at once, and names the file and the rule that
broke.

``test_payee_declarations_are_ordered_and_unique`` is skipped because
``preludes/self.journal`` breaks the rule it enforces; its docstring holds the
decision and ``PAYEE_DEFECTS`` names the lines to repair.

A documented path resolves from the document carrying it or from the repository
root, because the docs use both anchors; one whose leading ``../`` run leaves
the repository is checked by its tail, the spelling a monthly journal's
``include`` uses. Placeholders (``*``, ``<``, ``>``, an all-uppercase segment
naming a month or a year) and backticked commands holding whitespace are not
paths.
"""

import os
import re
from collections import Counter
from pathlib import Path

import pytest
from pydantic import BaseModel, RootModel
from pydantic_yaml import parse_yaml_raw_as

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

"""The spellings the restructure retired, none of which names a command today."""
RETIRED_SPELLINGS = (
    "hledger:check|hledger:format|hledger:format:check|format:hledger|"
    "bun run markdownlint|markdownlint:fix|cwd=scripts"
).split("|")

"""The file extensions a documented relative path may carry."""
_PATH_SUFFIXES = (".journal", ".md", ".py", ".yml")

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

"""Why the payee-declaration contract is skipped, naming the lines to repair."""
PAYEE_DEFECTS = (
    "`preludes/self.journal` declares `payee Oliver's Super Sandwiches` twice "
    "(lines 438-439) and breaks byte order at lines 518-519, where "
    "`payee 日本城 (Japan Home Center)` precedes `payee 丸龜製麵`. Both are "
    "owner-visible defects no hledger check reports, and `.agents/skills/add-payee/"
    "SKILL.md` holds the rule. Remove this skip only once the prelude is repaired."
)


class _PackageJson(BaseModel):
    """The `package.json` slice these contracts read."""

    scripts: dict[str, str]


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


def _documented_files() -> list[Path]:
    """Return every document that states the repository's agent-facing rules."""
    roots = [REPO_ROOT / "AGENTS.md", REPO_ROOT / "README.md"]
    return [*roots, *sorted(AGENTS_DIR.rglob("*.md"))]


def _unfenced(document: Path) -> str:
    """Return ``document``'s text without its fenced code blocks."""
    kept: list[str] = []
    fenced = False
    for line in _read(document).splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced:
            kept.append(line)
    return "\n".join(kept)


def _frontmatter(document: Path) -> dict[str, str]:
    """Return the flat ``key: value`` frontmatter of ``document``, if it has one."""
    lines = _read(document).splitlines()
    fields: dict[str, str] = {}
    if not lines or lines[0].strip() != "---":
        return fields
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip().strip('"')
    return fields


def _skill_dirs() -> list[Path]:
    """Return every skill directory, sorted by name."""
    skills = (AGENTS_DIR / "skills").iterdir()
    return sorted(entry for entry in skills if entry.is_dir())


def _sections(document: Path) -> list[str]:
    """Return ``document``'s second-level headings, in file order."""
    return [
        line.removeprefix("## ").strip()
        for line in _read(document).splitlines()
        if line.startswith("## ")
    ]


def _file_names(directory: Path) -> set[str]:
    """Return the names of the files one prompt directory holds."""
    return {path.name for path in directory.iterdir() if path.is_file()}


def _skill_budget() -> dict[str, int]:
    """Return each skill's line budget, from the table `skill-authoring` owns."""
    document = AGENTS_DIR / "instructions" / "skill-authoring.instructions.md"
    rows = (line.split() for line in _read(document).splitlines())
    return {row[0]: int(row[1]) for row in rows if len(row) == 2 and row[1].isdigit()}


def _payee_declaration_violations() -> list[str]:
    """Return every prelude payee block out of byte order or repeating a name."""
    violations: list[str] = []
    for prelude in sorted((REPO_ROOT / "preludes").glob("*.journal")):
        where = _relative(prelude)
        pairs = [
            (number, line.removeprefix("payee "))
            for number, line in enumerate(_read(prelude).splitlines(), 1)
            if line.startswith("payee ")
        ]
        for (number, name), (earlier, previous) in zip(pairs[1:], pairs):
            if name == previous:
                violations.append(f"{where}:{number}: `{name}` repeats line {earlier}")
            elif name < previous:
                violations.append(
                    f"{where}:{number}: `{name}` sorts before `{previous}`"
                )
    return violations


def _is_document_path(token: str) -> bool:
    """Report whether ``token`` is a relative path a document must resolve."""
    if any(marker in token for marker in ("://", "*", "<", ">", "~")):
        return False
    if token.startswith(("/", "#", "mailto:")) or "/" not in token:
        return False
    if not token.endswith(_PATH_SUFFIXES) or any(c.isspace() for c in token):
        return False
    # An all-uppercase segment such as `YYYY` or `MM` names a shape, not a path.
    return not any(re.fullmatch(r"[A-Z]{2,}", part) for part in token.split("/"))


def _resolves(document: Path, token: str) -> bool:
    """Report whether ``token`` exists from ``document``, or from the repository root."""
    if (document.parent / token).exists() or (REPO_ROOT / token).exists():
        return True
    tail = token
    while tail.startswith("../"):
        tail = tail.removeprefix("../")
    return tail != token and (REPO_ROOT / tail).exists()


def _unparseable(error: Exception) -> list[str]:
    """Report a document the YAML reader refused, by the error it raised.

    ``pydantic_yaml`` declares no error type of its own: a shape violation
    arrives as pydantic's ``ValidationError`` and a syntax error from the reader
    ``pydantic_yaml`` wraps, which no manifest here declares. Both are reported
    as one violation rather than escaping the contract as a traceback.
    """
    return [f"does not parse: {error}"]


def _payee_mapping_violations(text: str) -> list[str]:
    """Return every mapping whose target no prelude declares or that maps to itself."""
    try:
        mappings = parse_yaml_raw_as(RootModel[dict[str, list[str]]], text).root
    except Exception as error:
        return _unparseable(error)
    declared = {
        line.removeprefix("payee ")
        for prelude in (REPO_ROOT / "preludes").glob("*.journal")
        for line in _read(prelude).splitlines()
        if line.startswith("payee ")
    }
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
    key = re.compile(r'^(?:"([^"]+)"|([A-Za-z_][\w.-]*)):', re.MULTILINE)
    counts = Counter(quoted or bare for quoted, bare in key.findall(text))
    violations = [
        f"top-level key `{name}` is declared {count} times"
        for name, count in sorted(counts.items())
        if count > 1
    ]
    if violations:
        # The YAML reader refuses a document whose keys repeat.
        return violations
    try:
        mappings = parse_yaml_raw_as(_IdentifierMappings, text).root
    except Exception as error:
        return _unparseable(error)
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


def test_documented_bun_scripts_exist() -> None:
    """Assert every `bun run <name>` a document shows names a real script."""
    package = _PackageJson.model_validate_json(_read(REPO_ROOT / "package.json"))
    names = re.compile(r"\bbun run ([^\s`)\],.;]+)")
    _check(
        "every documented `bun run` name must be a `package.json` script",
        [
            _report(document, f"`bun run {name}` names no script")
            for document in _documented_files()
            for name in names.findall(_read(document))
            if name not in package.scripts
            and "<" not in name
            and not name.startswith("-")
        ],
    )


def test_no_retired_script_spellings() -> None:
    """Assert no document revives a command spelling the restructure retired."""
    violations = [
        _report(document, f"carries the retired spelling `{spelling}`")
        for document in _documented_files()
        for spelling in RETIRED_SPELLINGS
        if spelling in _read(document)
    ]
    violations.extend(
        _report(document, f"`{match.group(0)}` must name a `scripts.` module")
        for document in _documented_files()
        for match in re.finditer(r"python -m (?!scripts\.)", _read(document))
    )
    _check("no retired spelling may return", violations)


def test_no_husky_references() -> None:
    """Assert `prek.toml` declares the hooks and no document names another manager."""
    violations = [
        _report(document, f"names {tool}, but `prek.toml` declares the hooks")
        for document in _documented_files()
        for tool in ("husky", "lint-staged")
        if tool in _read(document).lower()
    ]
    if not (REPO_ROOT / "prek.toml").is_file():
        violations.append("prek.toml: the hook declaration is missing")
    _check("`prek.toml` must be the hook manager", violations)


def test_skill_frontmatter_and_budget() -> None:
    """Assert each skill names itself and its `SKILL.md` fits its budget.

    Rows are recognized by shape — a name and a line count — and compared with
    the tree in both directions, so a missing row and a stray row both fail.
    """
    budget = _skill_budget()
    skills = {skill.name: skill for skill in _skill_dirs()}
    violations: list[str] = []
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
        f".agents/instructions/skill-authoring.instructions.md: `{name}` is no skill"
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
        sections = _sections(document)
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
    """Assert every asset beside a `SKILL.md` is named in it."""
    violations: list[str] = []
    for skill in _skill_dirs():
        text = _read(skill / "SKILL.md") if (skill / "SKILL.md").is_file() else ""
        violations.extend(
            _report(asset, f"is not named in {_relative(skill / 'SKILL.md')}")
            for asset in sorted(skill.rglob("*"))
            if asset.is_file() and asset.name != "SKILL.md" and asset.name not in text
        )
    _check("every skill asset must be routed from its `SKILL.md`", violations)


def test_every_referenced_skill_exists() -> None:
    """Assert every skill a document names is a directory, and no asset fakes one."""
    skills = {skill.name for skill in _skill_dirs()}
    violations = [
        _report(document, f"names the skill `{name}`, which has no directory")
        for document in _documented_files()
        for name in re.findall(
            r"\b(ingest-[a-z]+|add-payee|migrate|fix-journals)\b", _read(document)
        )
        if name not in skills
    ]
    violations.extend(
        _report(entry, "carries the prefix of an `ingest-` aspect directory")
        for entry in sorted((AGENTS_DIR / "skills" / "ingest").iterdir())
        if entry.name.startswith("ingest-")
    )
    _check(
        "every referenced skill must exist, and no asset may read as one", violations
    )


def test_markdown_relative_links_resolve() -> None:
    """Assert every relative link and documented path resolves to a real file."""
    links = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
    spans = re.compile(r"`([^`\n]+)`")
    violations: list[str] = []
    for document in _documented_files():
        text = _unfenced(document)
        tokens = [match.group(1) for match in links.finditer(text)]
        tokens.extend(match.group(1).strip() for match in spans.finditer(text))
        violations.extend(
            _report(document, f"`{token}` names no file a reader can open")
            for token in tokens
            if _is_document_path(token) and not _resolves(document, token)
        )
    _check("every relative path a document shows must exist", violations)


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


def test_prompt_arguments_are_harness_neutral() -> None:
    """Assert no prompt carries an argument placeholder one harness alone expands."""
    documents = {path for dir in (PROMPTS_DIR, MIRROR_DIR) for path in dir.glob("*.md")}
    _check(
        "prompts must name arguments every harness reads the same way",
        [
            _report(document, "contains a `${input:` placeholder, one harness's own")
            for document in sorted(documents)
            if "${input:" in _read(document)
        ],
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


@pytest.mark.skip(reason=PAYEE_DEFECTS)
def test_payee_declarations_are_ordered_and_unique() -> None:
    """Assert each prelude's payee block is in strict byte order and free of repeats.

    The contract covers both properties because `.agents/skills/add-payee/SKILL.md`
    mandates them together, and the duplicate is the more dangerous of the two:
    two declarations of one merchant is how a payee silently splits in two.

    The decision recorded here is to keep the whole contract and skip it rather
    than scope it to order alone, because `preludes/self.journal` breaks both
    today — ``Oliver's Super Sandwiches`` twice at lines 438-439, and
    ``日本城 (Japan Home Center)`` sorted before ``丸龜製麵`` at lines 518-519 —
    and neither defect is a test defect. Both are owner-visible prelude defects
    that no hledger check reports; ``PAYEE_DEFECTS`` repeats the lines in the
    skip reason, and lifting the skip without repairing the prelude fails with
    every offending line.
    """
    _check(
        "every prelude's `payee` declarations must be in strict byte order and unique",
        _payee_declaration_violations(),
    )
