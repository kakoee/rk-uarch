"""Repository maintenance commands, never production dependencies."""

from .u2_import_guard import check_import_roots

check_import_roots()
