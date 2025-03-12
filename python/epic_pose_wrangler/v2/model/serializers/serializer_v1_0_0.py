# Copyright Epic Games, Inc. All Rights Reserved.

# Internal
from epic_pose_wrangler.v2.model import api
from epic_pose_wrangler.v2.model.serializers import base_serializer


class Serializer(base_serializer.Serializer):
    __version__ = "1.0.0"

    @classmethod
    def can_process(cls, data, **kwargs):
        return 'metadata' not in data.keys()

    @classmethod
    def serialize(cls, solvers=None, **kwargs):
        return {str(solver): solver.data() for solver in solvers}

    @classmethod
    def deserialize(cls, data, solver_names=None, **kwargs):
        rbf_data = data.get('solvers', {}) or data
        if solver_names:
            rbf_data = {n: d for n, d in rbf_data.items() if n in solver_names}

        for solver_name, solver_data in rbf_data.items():
            api.RBFNode.create_from_data(solver_data)
