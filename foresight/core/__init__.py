"""``foresight.core`` — shared data models, storage abstractions, settings.

Owns the cross-cutting Python concerns consumed by every other subpackage:

- SQLAlchemy models (E2.S1)
- Database session factory + storage abstractions (E2.S3)
- Settings / config loading (E2 onward)
- Domain primitives and exceptions

This subpackage MUST be import-side-effect free: module loading must not
perform network calls, file system writes, or environment-dependent init.
"""

from __future__ import annotations
