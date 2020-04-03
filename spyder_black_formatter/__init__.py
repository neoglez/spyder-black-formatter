# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) neoglez
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Spyder black formatter Plugin."""


from ._version import __version__

# The following statements are required to register this 3rd party plugin:

from .blackformatterplugin import BlackFormatterPlugin

PLUGIN_CLASS = BlackFormatterPlugin
