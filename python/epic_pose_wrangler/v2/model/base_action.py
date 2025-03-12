# Copyright Epic Games, Inc. All Rights Reserved.

# Built-in
import abc


class BaseAction(object):
    """
    The base class for creating custom PoseWrangler actions that are displayed to the user when they right-click
    a solver in the RBF Solvers section of the main window.
    """
    __display_name__ = "BaseAction"
    __tooltip__ = ""
    __category__ = ""

    @classmethod
    @abc.abstractmethod
    def validate(cls, ui_context):
        """
        Return True/False if the current UI context contains the correct information in order for this action to be
        successfully executed. Must be implemented.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def execute(self, ui_context=None, **kwargs):
        raise NotImplementedError

    def __init__(self, api=None):
        self._api = api

    @property
    def api(self):
        return self._api
