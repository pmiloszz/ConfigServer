class FlagNotFound(Exception):
    def __init__(self, flag_id: int) -> None:
        super().__init__(f"Flag not found (id={flag_id})")
        self.flag_id = flag_id


class FlagAlreadyExists(Exception):
    pass


class VersionConflict(Exception):
    def __init__(self, flag_id: int) -> None:
        super().__init__(f"Version mismatch (id={flag_id})")
        self.flag_id = flag_id
