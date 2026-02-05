"""Utilities package that mirrors the old ``scripts.util`` module.

Historically this package re-exported public symbols for convenience.
We intentionally avoid re-exporting names now - submodules define their
public APIs via their own ``__all__`` and callers should import from the
specific submodule (for example ``from .util.journals import ...``).
"""

__all__ = ()
