# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import typing

from PySide6.QtCore import Signal, Qt, QThreadPool
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListView,
)

from src.core.utils.missing_files import MissingRegistry
from src.qt.helpers.custom_runnable import CustomRunnable
from src.qt.helpers.function_iterator import FunctionIterator
from src.qt.widgets.progress import ProgressWidget

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class DeleteUnlinkedEntriesModal(QWidget):
    done = Signal()

    def __init__(self, driver: "QtDriver", tracker: MissingRegistry):
        super().__init__()
        self.driver = driver
        self.tracker = tracker
        self.setWindowTitle("Delete Unlinked Entries")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(500, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        self.desc_widget = QLabel()
        self.desc_widget.setObjectName("descriptionLabel")
        self.desc_widget.setWordWrap(True)
        self.desc_widget.setText(f"""
		Are you sure you want to delete the following {self.tracker.missing_files_count} entries?
		""")
        self.desc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.list_view = QListView()
        self.model = QStandardItemModel()
        self.list_view.setModel(self.model)

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.cancel_button = QPushButton()
        self.cancel_button.setText("&Cancel")
        self.cancel_button.setDefault(True)
        self.cancel_button.clicked.connect(self.hide)
        self.button_layout.addWidget(self.cancel_button)

        self.delete_button = QPushButton()
        self.delete_button.setText("&Delete")
        self.delete_button.clicked.connect(self.hide)
        self.delete_button.clicked.connect(lambda: self.delete_entries())
        self.button_layout.addWidget(self.delete_button)

        self.root_layout.addWidget(self.desc_widget)
        self.root_layout.addWidget(self.list_view)
        self.root_layout.addWidget(self.button_container)

    def refresh_list(self):
        self.desc_widget.setText(f"""
		Are you sure you want to delete the following {self.tracker.missing_files_count} entries?
		""")

        self.model.clear()
        for i in self.tracker.missing_files:
            self.model.appendRow(QStandardItem(str(i.path)))

    def delete_entries(self):
        pw = ProgressWidget(
            window_title="Deleting Entries",
            label_text="",
            cancel_button_text=None,
            minimum=0,
            maximum=self.tracker.missing_files_count,
        )
        pw.show()

        iterator = FunctionIterator(self.tracker.execute_deletion)
        files_count = self.tracker.missing_files_count
        iterator.value.connect(
            lambda idx: (
                pw.update_progress(idx),
                pw.update_label(f"Deleting {idx}/{files_count} Unlinked Entries"),
            )
        )

        r = CustomRunnable(iterator.run)
        QThreadPool.globalInstance().start(r)
        r.done.connect(
            lambda: (
                pw.hide(),
                pw.deleteLater(),
                self.done.emit(),
            )
        )
