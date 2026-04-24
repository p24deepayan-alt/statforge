"""Command-pattern undo/redo stack for preprocessing and report editing."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Command(Protocol):
    """A reversible operation."""

    def execute(self) -> None: ...
    def undo(self) -> None: ...
    def describe(self) -> str: ...


class UndoStack:
    """Manages an ordered history of commands with undo/redo."""

    def __init__(self, max_depth: int = 200) -> None:
        self._done: list[Command] = []
        self._undone: list[Command] = []
        self._max_depth = max_depth

    def push(self, command: Command) -> None:
        """Execute a command and push it onto the done stack."""
        command.execute()
        self._done.append(command)
        if len(self._done) > self._max_depth:
            self._done.pop(0)
        # New action invalidates the redo branch.
        self._undone.clear()

    def undo(self) -> Command | None:
        """Undo the most recent command. Returns it, or None if nothing to undo."""
        if not self._done:
            return None
        command = self._done.pop()
        command.undo()
        self._undone.append(command)
        return command

    def redo(self) -> Command | None:
        """Redo the most recently undone command. Returns it, or None."""
        if not self._undone:
            return None
        command = self._undone.pop()
        command.execute()
        self._done.append(command)
        return command

    def can_undo(self) -> bool:
        return len(self._done) > 0

    def can_redo(self) -> bool:
        return len(self._undone) > 0

    def clear(self) -> None:
        self._done.clear()
        self._undone.clear()

    @property
    def history(self) -> list[str]:
        """Return human-readable descriptions of all executed commands."""
        return [c.describe() for c in self._done]
