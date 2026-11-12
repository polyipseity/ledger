"""Invariant test for this repository's monthly close/open chain.

``hledger check`` passes on a ledger whose monthly chain is broken, because a
month that never received its ``closing balances`` transaction lets the
balances roll forward without violating any assertion. This test runs the
verifier that does notice, against the repository's own journals, so the defect
outlives the person who measured it.
"""

import pytest

from scripts.clopen_verify import resolve_now_month, verify_family
from scripts.utils.files import get_ledger_folder
from scripts.utils.journals import find_monthly_journals

"""Public symbols exported by this module (none)."""
__all__ = ()

"""Why this test is skipped, in the terms the owner needs to lift it."""
SKIP_REASON = (
    "monthly boundary chain unrepaired: `bun run verify:migration` still reports "
    "defects, and `.agents/skills/migrate/SKILL.md` holds the repair procedure. "
    "Remove this skip only after that command reports no defects."
)


@pytest.mark.skip(reason=SKIP_REASON)
@pytest.mark.anyio
async def test_repository_boundary_chain_is_complete() -> None:
    """Assert that every monthly journal of this repository is boundary-clean.

    The current month is derived the way ``scripts.clopen_verify`` derives it
    when ``--now`` is omitted, and the journals are the ones ``main`` discovers,
    so this test cannot disagree with ``bun run verify:migration``. Any defect
    fails the test with the same ``journal:month: kind: detail`` lines the
    command prints.
    """
    journals = await find_monthly_journals(get_ledger_folder(), None)
    defects = await verify_family(journals, resolve_now_month(None))
    report = "\n".join(
        f"{defect.journal}:{defect.month}: {defect.kind}: {defect.detail}"
        for defect in defects
    )
    assert not defects, f"{len(defects)} boundary defect(s):\n{report}"
