# Copyright Epic Games, Inc. All Rights Reserved.
class PoseWranglerContext(object):
    def __init__(self, current_solver, solvers):
        self._current_solver = current_solver
        self._solvers = solvers

    @property
    def current_solver(self):
        return self._current_solver

    @property
    def solvers(self):
        return self._solvers


class EditSolverContextManager(object):
    def __init__(self, api, current_solver):
        self._api = api
        self._current_solver = current_solver

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._api.edit_solver(edit=False, solver=self._current_solver)
