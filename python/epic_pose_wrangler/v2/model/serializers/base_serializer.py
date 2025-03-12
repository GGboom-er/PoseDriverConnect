# Copyright Epic Games, Inc. All Rights Reserved.

# Built-in
import abc


class Serializer(object):
    __version__ = "0.0.0"

    @classmethod
    @abc.abstractmethod
    def can_process(cls, data, **kwargs):
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def serialize(cls, solvers=None, **kwargs):
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def deserialize(cls, data, solver_names=None, **kwargs):
        raise NotImplementedError
