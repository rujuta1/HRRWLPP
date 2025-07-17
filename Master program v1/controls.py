from __future__ import annotations

from functools import partial
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

DEGREE_SYMBOL = "\N{DEGREE SIGN}"
DEFAULT_FEEDRATE = 720  # ° min⁻¹ – tweak to taste


class RotationMountTab(QWidget):
    """PyQt tab controlling three rotation mounts via a *single* ``BTT`` object."""

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    def __init__(self, btt: "BTT", parent: QWidget | None = None):  # type: ignore[name-defined]
        super().__init__(parent)
        self.btt = btt

        self.setWindowTitle("Rotation Mount Control")

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # build three identical panels
        for idx in (1, 2, 3):
            main_layout.addWidget(self._build_panel(idx))

        main_layout.addStretch()

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def _build_panel(self, idx: int) -> QGroupBox:
        box = QGroupBox(f"Rotation Mount {idx}")
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        form = QFormLayout(box)

        angle_edit = QLineEdit()
        angle_edit.setPlaceholderText(f"Target angle (0–360{DEGREE_SYMBOL})")

        # buttons
        move_btn = QPushButton("Move")
        home_btn = QPushButton("Home")

        # wiring
        move_btn.clicked.connect(partial(self._move_clicked, idx, angle_edit))
        home_btn.clicked.connect(partial(self._home_clicked, idx))

        # layout
        btn_row = QHBoxLayout()
        btn_row.addWidget(move_btn)
        btn_row.addWidget(home_btn)

        form.addRow(QLabel("Target Angle"), angle_edit)
        form.addRow(btn_row)

        return box

    # ------------------------------------------------------------------
    # slot implementations
    # ------------------------------------------------------------------

    # mapping of index → BTT method names
    _MOVE_METHODS: dict[int, str] = {1: "rot_1", 2: "rot_2", 3: "rot_3"}
    _HOME_METHODS: dict[int, str] = {1: "home_rot1", 2: "home_rot2", 3: "home_rot3"}

    def _move_clicked(self, idx: int, angle_edit: QLineEdit) -> None:
        text = angle_edit.text().strip()
        try:
            angle = float(text)
        except ValueError:
            self._error(idx, "Enter a valid number for the angle.")
            return

        if not 0 <= angle <= 360:
            self._error(idx, f"Angle must be between 0 and 360{DEGREE_SYMBOL}.")
            return

        method_name = self._MOVE_METHODS[idx]
        self._invoke_btt(idx, method_name, angle, DEFAULT_FEEDRATE)

    def _home_clicked(self, idx: int) -> None:
        method_name = self._HOME_METHODS[idx]
        self._invoke_btt(idx, method_name)

    # ------------------------------------------------------------------
    # low‑level helper
    # ------------------------------------------------------------------

    def _invoke_btt(self, idx: int, method_name: str, *args):
        try:
            method: Callable = getattr(self.btt, method_name)
        except AttributeError:
            self._error(idx, f"BTT driver lacks method '{method_name}()'.")
            return

        try:
            method(*args)
        except Exception as exc:  # noqa: BLE001
            self._error(idx, f"Driver error: {exc}")

    # ------------------------------------------------------------------
    # message box helper
    # ------------------------------------------------------------------

    def _error(self, idx: int, msg: str) -> None:
        QMessageBox.critical(self, "Rotation Mount Error", f"Mount {idx}: {msg}")
