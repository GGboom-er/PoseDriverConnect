# Copyright Epic Games, Inc. All Rights Reserved.

# External
try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore


class PoseExporterView(QtWidgets.QWidget):
    export = QtCore.Signal(str, list, str, str, bool)

    def __init__(self):
        super(PoseExporterView, self).__init__()
        self.setContentsMargins(0, 0, 0, 0)
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(main_layout)

        up_axis_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(up_axis_layout)

        up_axis_label = QtWidgets.QLabel("Up Axis:")
        up_axis_layout.addWidget(up_axis_label)

        self.x_axis_button = QtWidgets.QRadioButton("X Axis")
        self.y_axis_button = QtWidgets.QRadioButton("Y Axis")
        self.z_axis_button = QtWidgets.QRadioButton("Z Axis")
        self.z_axis_button.setChecked(True)

        up_axis_layout.addWidget(self.x_axis_button)
        up_axis_layout.addWidget(self.y_axis_button)
        up_axis_layout.addWidget(self.z_axis_button)

        export_dir_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(export_dir_layout)

        export_dir_label = QtWidgets.QLabel("Export Dir:")
        export_dir_layout.addWidget(export_dir_label)

        self.export_dir_line_edit = QtWidgets.QLineEdit()
        export_dir_layout.addWidget(self.export_dir_line_edit)

        browse_button = QtWidgets.QPushButton("Browse")
        browse_button.clicked.connect(self._set_export_dir)
        export_dir_layout.addWidget(browse_button)

        self.delta_checkbox = QtWidgets.QCheckBox("Export as delta")
        self.delta_checkbox.setChecked(True)
        main_layout.addWidget(self.delta_checkbox)

        export_button = QtWidgets.QPushButton("EXPORT")
        export_button.clicked.connect(self._export)
        main_layout.addWidget(export_button)
        main_layout.addSpacing(5)
        main_layout.addStretch()

    def _export(self):
        export_directory = self.export_dir_line_edit.text()
        if self.x_axis_button.isChecked():
            up_axis = "x"
        elif self.y_axis_button.isChecked():
            up_axis = "y"
        else:
            up_axis = "z"

        delta = self.delta_checkbox.isChecked()

        json_file = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "RBF Json File Name",
            dir=export_directory or ".",
            filter="RBF File (*.json)"
        )
        if json_file[0]:
            self.export.emit(
                json_file[0], [],
                export_directory,
                up_axis,
                delta
            )

    def _set_export_dir(self):
        dir_name = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_name:
            self.export_dir_line_edit.setText(dir_name)


if __name__ == '__main__':
    import ctypes
    import sys

    myappid = 'EpicGames.PoseWrangler'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = QtWidgets.QApplication(sys.argv)
    tool = PoseExporterView()
    tool.show()
    app.exec_()
