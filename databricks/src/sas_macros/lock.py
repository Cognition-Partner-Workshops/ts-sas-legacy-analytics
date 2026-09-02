"""Delta locking compatibility shim."""


def lock(table: str, action: str = "LOCK") -> bool:
    """No-op because Delta ACID transactions provide table consistency (D2-001)."""

    del table, action
    return True
