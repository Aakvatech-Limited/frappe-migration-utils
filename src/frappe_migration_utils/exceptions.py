class MigrationError(RuntimeError):
    """A migration cannot safely finish; do not mark its patch complete."""
