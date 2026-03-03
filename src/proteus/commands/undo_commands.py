"""QUndoCommand subclasses for all undoable operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from PySide6.QtGui import QUndoCommand

from proteus.core.state import ImageState

if TYPE_CHECKING:
    from proteus.ui.main_window import ProteusMainWindow


class ImageOperationCommand(QUndoCommand):
    """Generic undo command that captures before/after ImageState snapshots."""

    def __init__(self, window: ProteusMainWindow, before: ImageState, after: ImageState, description: str):
        super().__init__(description)
        self._window = window
        self._before = before
        self._after = after

    def undo(self) -> None:
        self._window.restore_state(self._before)

    def redo(self) -> None:
        self._window.restore_state(self._after)


class DrawStrokeCommand(QUndoCommand):
    """Captures a complete brush stroke as one undoable action."""

    def __init__(self, window: ProteusMainWindow, mask_before: np.ndarray | None, mask_after: np.ndarray):
        super().__init__("Brush Stroke")
        self._window = window
        self._mask_before = mask_before.copy() if mask_before is not None else None
        self._mask_after = mask_after.copy()

    def undo(self) -> None:
        self._window.set_draw_mask(self._mask_before)

    def redo(self) -> None:
        self._window.set_draw_mask(self._mask_after)


class RoiChangeCommand(QUndoCommand):
    """Captures an ROI selection as one undoable action."""

    def __init__(self, window: ProteusMainWindow, roi_before: tuple | None, roi_after: tuple | None):
        super().__init__("ROI Selection")
        self._window = window
        self._roi_before = roi_before
        self._roi_after = roi_after

    def undo(self) -> None:
        self._window.set_roi(self._roi_before)

    def redo(self) -> None:
        self._window.set_roi(self._roi_after)
