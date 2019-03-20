# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) kiko correoso
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
from qtpy.QtGui import QTextCursor
from qtpy.QtWidgets import QVBoxLayout, QGroupBox, QGridLayout, QLabel
from spyder.config.base import get_translation
from spyder.config.gui import fixed_shortcut
from spyder.utils.qthelpers import create_action
from spyder.py3compat import to_text_string
import qtawesome as qta

"""black formatter Plugin."""

# Standard library imports
import sys

# Third party imports
ERR_MSG = ""
try:
    from black import format_str, FileMode, TargetVersion
except ImportError:
    ERR_MSG = "Please, install black."


try:  # Spyder4
    from spyder.api.plugins import SpyderPluginWidget as BasePluginClass
    from spyder.api.preferences import PluginConfigPage
except ImportError:  # Spyder3
    from spyder.plugins import SpyderPluginMixin as BasePluginClass
    from spyder.plugins.configdialog import PluginConfigPage

# from spyder.utils.icon_manager import get_icon


_ = get_translation("black", dirname="spyder_black_formatter")


def get_python_version():
    major = sys.version_info.major
    minor = sys.version_info.minor
    return f"python {major}.{minor}"


target_version = (
    ("python 3.3", "PY33"),
    ("python 3.4", "PY34"),
    ("python 3.5", "PY35"),
    ("python 3.6", "PY36"),
    ("python 3.7", "PY37"),
    ("python 3.8", "PY38"),
)


class BlackConfigPage(PluginConfigPage):
    """
    Widget with configuration options for black formatter.
    """

    OPTIONS = {
        "line_length": 80,
        "target_version": target_version,
        "skip_string_normalization": (("False", False), ("True", True)),
    }

    def setup_page(self):
        if ERR_MSG:
            label = QLabel(_("Could not load plugin:\n{0}".format(ERR_MSG)))
            layout = QVBoxLayout()
            layout.addWidget(label)
            self.setLayout(layout)
            return

        # General options
        # Hack : the spinbox widget will be added to self.spinboxes
        spinboxes_before = set(self.spinboxes)
        # line length
        line_length_spin = self.create_spinbox(
            _("Line length: "),
            "",
            "line_length",
            default=self.OPTIONS["line_length"],
            min_=40,
            max_=200,
            step=1,
        )
        spinbox = set(self.spinboxes) - spinboxes_before
        spinbox = spinbox.pop()

        # target python version
        versions_group = QGroupBox(_("Target versions"))
        target_layout = QGridLayout()
        default = get_python_version()  # the python version being used
        for i, option in enumerate(self.OPTIONS["target_version"]):
            if default == option[0]:
                value = True
            else:
                value = False
            col = i - (i // 2) * 2
            row = i // 2
            cb = self.create_checkbox(option[0], option[1], default=value)
            target_layout.addWidget(cb, row, col)
        versions_group.setLayout(target_layout)

        # skip string normalization
        choices = self.OPTIONS["skip_string_normalization"]
        default = "False"
        skip_string_combobox = self.create_combobox(
            _("Skip string normalization: "),
            choices,
            "skip_string_normalization",
            default=default,
        )

        # General layout
        options_layout = QVBoxLayout()
        options_layout.addWidget(line_length_spin)
        options_layout.addWidget(versions_group)
        options_layout.addWidget(skip_string_combobox)
        options_group = QGroupBox(_("Options"))
        options_group.setLayout(options_layout)

        vlayout = QVBoxLayout()
        vlayout.addWidget(options_group)
        self.setLayout(vlayout)


class DummyDock:
    def close(self):
        pass


class BlackFormatterPlugin(BasePluginClass):
    """black formatter plugin."""

    CONF_SECTION = "spyder_black_formatter"
    CONFIGWIDGET_CLASS = BlackConfigPage

    def __init__(self, main):
        print("ENTRO")
        super(BlackFormatterPlugin, self).__init__(main)
        self.dockwidget = DummyDock()

    # --- SpyderPluginWidget API ----------------------------------------------
    def get_plugin_title(self):
        """Return widget title."""
        return _("Black formatter")

    def get_plugin_icon(self):
        """Return widget icon."""
        icon = qta.icon("fa5s.bold")
        return icon

    def register_plugin(self):
        """Register plugin in Spyder's main window."""
        black_act = create_action(
            self.main,
            _("Format code using Black"),
            icon=self.get_plugin_icon(),
            triggered=self.run_black,
        )
        fixed_shortcut("Shift+F5", self.main, self.run_black)
        self.main.source_menu_actions += [None, black_act]
        self.main.editor.pythonfile_dependent_actions += [black_act]

    def apply_plugin_settings(self, options):
        """Apply configuration file's plugin settings."""
        pass

    def closing_plugin(self, cancelable=False):
        """Perform actions before parent main window is closed."""
        return True

    # --- Public API ---------------------------------------------------------
    def run_black(self):
        """Format code with Black."""
        if ERR_MSG:
            self.main.statusBar().showMessage(
                _("Unable to run: {0}".format(ERR_MSG))
            )
            return

        # Retrieve text of current opened file
        editorstack = self.main.editor.get_current_editorstack()
        index = editorstack.get_stack_index()
        finfo = editorstack.data[index]
        editor = finfo.editor
        cursor = editor.textCursor()
        cursor.beginEditBlock()  # Start cancel block
        if not cursor.hasSelection():
            position_start = 0
            cursor.select(QTextCursor.Document)  # Select all
        else:
            # Select whole lines
            position_end = cursor.selectionEnd()
            cursor.setPosition(cursor.selectionStart())
            cursor.movePosition(QTextCursor.StartOfLine)
            position_start = cursor.position()
            cursor.setPosition(position_end, QTextCursor.KeepAnchor)
            cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
            position_lastline_start = cursor.position()
            if not position_end == position_lastline_start:
                cursor.movePosition(
                    QTextCursor.EndOfLine, QTextCursor.KeepAnchor
                )
                # Select EOL if not on a new line
                if not position_lastline_start == cursor.position():
                    cursor.movePosition(
                        QTextCursor.Right, QTextCursor.KeepAnchor
                    )

        # replace(): See qt doc for QTextCursor.selectedText()
        text_before = to_text_string(
            cursor.selectedText().replace("\u2029", "\n")
        )

        # Run Black
        line_length = self.get_option("line_length", 80)
        skip_string = self.get_option("skip_string_normalization", False)
        target = []
        for v in target_version:
            option = self.get_option(v[1], False)
            if option:
                target.append(TargetVersion[v[1]])
        mode = FileMode(
            target_versions=target,
            line_length=line_length,
            string_normalization=not skip_string,
            is_pyi=False,
        )

        text_after = format_str(text_before, mode=mode)

        # Apply new text if needed
        if text_before != text_after:
            cursor.insertText(text_after)  # Change text

        cursor.endEditBlock()  # End cancel block

        # Select changed text
        position_end = cursor.position()
        cursor.setPosition(position_start, QTextCursor.MoveAnchor)
        cursor.setPosition(position_end, QTextCursor.KeepAnchor)
        editor.setTextCursor(cursor)

        self.main.statusBar().showMessage(_("Black formatting finished !"))
