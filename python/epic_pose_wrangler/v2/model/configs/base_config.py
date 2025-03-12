# Copyright Epic Games, Inc. All Rights Reserved.

# Built-in
import abc


class BaseConfig(object):

    @classmethod
    @abc.abstractmethod
    def validate(cls, file_path=None, data=None):
        raise NotImplementedError

    def __init__(self, file_path="", data=None):
        self._file_path = file_path
        self._data = data or {}

    @property
    def file_path(self):
        return self._file_path

    @property
    def retargeter(self):
        return None

    @property
    def mirror_mapping(self):
        return None

    @abc.abstractmethod
    def upgrade(self):
        raise NotImplementedError

    def is_feature_available(self, feature=None):
        return bool(feature)
