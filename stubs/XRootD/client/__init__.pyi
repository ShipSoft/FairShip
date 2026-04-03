"""Partial type stubs for XRootD.client as used in FairShip."""

class XRootDStatus:
    ok: bool
    errno: int
    code: int
    message: str

class StatInfo:
    size: int
    flags: int
    modtime: int
    modtimestr: str
    id: str

class FileSystem:
    def __init__(self, url: str) -> None: ...
    def stat(self, path: str) -> tuple[XRootDStatus, StatInfo | None]: ...
