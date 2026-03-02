"""Application state and operation logging. No UI dependencies."""

import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any

import numpy as np


@dataclass
class ImageState:
    """Snapshot of the application state for undo/redo."""
    img: Optional[np.ndarray]
    draw_mask: Optional[np.ndarray]
    roi: Optional[Tuple[int, int, int, int]]
    zoom: float
    pan_x: float
    pan_y: float
    meta: Dict[str, Any] = field(default_factory=dict)

    def copy(self) -> "ImageState":
        return ImageState(
            img=None if self.img is None else self.img.copy(),
            draw_mask=None if self.draw_mask is None else self.draw_mask.copy(),
            roi=None if self.roi is None else tuple(self.roi),
            zoom=self.zoom,
            pan_x=self.pan_x,
            pan_y=self.pan_y,
            meta=dict(self.meta),
        )


class OperationLog:
    """Records processing operations and exports metadata files."""

    # Operations that should not be recorded in the log
    _SKIP_OPS = {"open", "draw", "roi", "clear_draw", "clear_roi"}

    def __init__(self):
        self.entries: List[Dict[str, Any]] = []

    def record(self, meta: Dict[str, Any]) -> None:
        op = meta.get("op")
        if op not in self._SKIP_OPS:
            self.entries.append(dict(meta))

    def clear(self) -> None:
        self.entries.clear()

    @staticmethod
    def friendly_name(meta: Dict[str, Any]) -> str:
        """Convert an operation meta dict into a human-readable name."""
        op = meta.get("op", "")
        if op in ("pseudocolor_current", "pseudocolor_two", "pseudocolor_channel"):
            ch = meta.get("channel")
            if ch in ("r", "g", "b", "all"):
                return f"Pseudocolor-{ch.upper()}"
            return "Pseudocolor"
        if op in ("sharpen_otsu", "sharpie_binarize"):
            return "Sharpen(Otsu)"
        if op == "sharpen_fixed":
            return "Sharpen(128)"
        if op == "power":
            return "Power"
        if op == "invert":
            return "Invert"
        if op == "blur_divide":
            return "Blur&Divide"
        if op == "denoise_gaussian":
            return "Denoise(Gaussian)"
        if op == "pca":
            return "PCA"
        if op == "pca_svd":
            return "PCA-SVD"
        if op == "rotate_90":
            direction = meta.get("direction", "")
            return f"Rotate90({direction})"
        return op or "Unknown"

    def export_txt(self, path: str) -> None:
        """Write the operation log as a text file alongside the saved image."""
        lines: List[str] = []
        # Header
        lines.append("Technical")
        lines.append("System Manufacturer: ")
        lines.append("Lights used: ")
        lines.append("Name of photographer: ")
        lines.append("Name of processor: ")
        lines.append("")
        lines.append("Object")
        lines.append("Name (if any): ")
        lines.append("Shelfmark: ")
        lines.append("Material: ")
        lines.append("Institution/owner: ")
        lines.append("")

        # Summary
        friendly_ops = [self.friendly_name(m) for m in self.entries]
        if friendly_ops:
            cnt = Counter(friendly_ops)
            summary_parts = [f"{name} x{c}" for name, c in cnt.items()]
            summary = ", ".join(summary_parts)
        else:
            summary = "None"

        lines.append(f"Processes used: {summary}")
        lines.append("")
        lines.append("Process details:")

        for i, meta in enumerate(self.entries, start=1):
            name = self.friendly_name(meta)
            params = {k: v for k, v in meta.items() if k != "op"}
            if params:
                lines.append(f"{i}. {name} | params: {json.dumps(params, ensure_ascii=False)}")
            else:
                lines.append(f"{i}. {name}")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
