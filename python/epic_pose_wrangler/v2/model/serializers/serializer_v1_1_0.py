# Copyright Epic Games, Inc. All Rights Reserved.

# Built-in
import collections
import copy
import json
from collections import OrderedDict

# External
from maya import cmds
from maya.api import OpenMaya as om

# Internal
from epic_pose_wrangler.v2.model import api
from epic_pose_wrangler.v2.model.serializers import base_serializer


class Serializer(base_serializer.Serializer):
    __version__ = "1.1.0"

    @classmethod
    def can_process(cls, data, **kwargs):
        correct_version = 'metadata' in data.keys() and data['metadata']['version'] == cls.__version__
        return correct_version and kwargs.get('config')

    @classmethod
    def serialize(cls, solvers=None, **kwargs):
        config = kwargs.get('config')
        # Check if we want to serialize the drivers matrices as a delta, instead of absolute. Use delta by default
        serialize_delta = kwargs.get('delta', True)

        initial_solver_data = OrderedDict({str(solver): solver.data() for solver in solvers})

        final_solver_data = OrderedDict()
        # If delta is enabled
        if serialize_delta:
            # Iterate over the solver data and generate deltas between:
            # drivers in default pose ---> drivers in each custom pose
            for solver_name, solver_data in initial_solver_data.items():
                # Get the poses
                poses = solver_data['poses']
                # The first pose is always treated as the rest pose and this is what will be used to generate the delta
                pose_index = 0
                # List to store the default position of the driver matrices
                default_pose_driver_matrices = []

                solver_pose_data = OrderedDict()

                # Generate a delta for each pose
                for pose_name, pose_data in poses.items():
                    drivers = copy.deepcopy(pose_data['drivers'])

                    # If this is the first pose, we can assume it is the default and should use this to calculate
                    # the delta
                    if pose_index == 0:
                        default_pose_driver_matrices = drivers
                    else:
                        # This isn't the default pose, so we want to calculate the delta between this pose and the
                        # default for each driver specified
                        new_drivers = []
                        for index, driver in enumerate(drivers):
                            default_driver = om.MMatrix(default_pose_driver_matrices[index])
                            driver = om.MMatrix(driver)
                            new_drivers.append(list(driver * default_driver.inverse()))
                        # Update the pose data
                        pose_data['drivers'] = new_drivers
                    # Update the solver pose data
                    solver_pose_data[pose_name] = pose_data
                    # Increment to ensure that the first pose is used as the rest pose
                    pose_index += 1

                # Update the pose data for the solver
                solver_data['poses'] = solver_pose_data
                # Generate new dictionary with the new solver data
                final_solver_data[solver_name] = solver_data

        else:
            final_solver_data = initial_solver_data

        data = {
            "solvers": final_solver_data,
            "metadata": {
                "version": cls.__version__,
                "copyright": "Copyright Epic Games, Inc. All Rights Reserved",
                # Embed any serialization parameters into the file so that the user doesn't need to specify them
                # in order to correctly deserialize
                "serializer_params": {"delta": serialize_delta}
            }
        }

        if config.is_feature_available(config.retargeter):
            str_data = json.dumps(data)
            for source, target in config.retargeter.transform_export_mapping.items():
                str_data = str_data.replace('"{source}"'.format(source=source), '"{target}"'.format(target=target))

            data = json.loads(str_data, object_pairs_hook=collections.OrderedDict)

        return data

    @classmethod
    def deserialize(cls, data, solver_names=None, **kwargs):
        config = kwargs.get('config')
        serializer_params = data['metadata'].get('serializer_params', {})
        load_delta = serializer_params.get('delta', False) or kwargs.get('delta', False)

        rbf_data = data.get('solvers', {}) or data
        if solver_names:
            rbf_data = {n: d for n, d in rbf_data.items() if n in solver_names}

        if config.is_feature_available(config.retargeter):
            str_data = json.dumps(rbf_data)
            for source, target in config.retargeter.transform_import_mapping.items():
                str_data = str_data.replace('"{source}"'.format(source=source), '"{target}"'.format(target=target))

            rbf_data = json.loads(str_data, object_pairs_hook=collections.OrderedDict)

        # If loading by delta is specified, the correct delta needs to be calculated before the deserialization process
        # can be triggered
        if load_delta:
            new_rbf_data = OrderedDict()

            for solver_name, solver_data in rbf_data.items():
                # Get the current drivers matrices from its current object space position as an MMatrix for ease of use
                current_drivers = [om.MMatrix(cmds.xform(d, query=True, matrix=True, objectSpace=True)) for d in
                                   solver_data['drivers']]

                poses = solver_data['poses']
                new_pose_data = OrderedDict()
                # Each pose needs to be updated, but the first pose requires different treatment so the pose index
                # must be tracked
                pose_index = 0

                for pose_name, pose_data in poses.items():
                    # If this is the first pose, it is treated as the rest pose and the driver matrices should be set
                    # to their current value from the scene
                    if pose_index == 0:
                        pose_data['drivers'] = [list(d) for d in current_drivers]
                    else:
                        # If it isn't the first pose, the new matrix must be calculated by taking the delta stored in
                        # the file and adding it to the rest pose value. This needs to be done for each driver
                        new_drivers = []
                        drivers = copy.deepcopy(pose_data['drivers'])
                        for index, driver in enumerate(drivers):
                            default_driver = current_drivers[index]
                            driver = om.MMatrix(driver)
                            new_drivers.append(list(driver * default_driver))
                        # Update the driver data
                        pose_data['drivers'] = new_drivers
                    # Update the solver pose data
                    new_pose_data[pose_name] = pose_data
                    # Increment the pose index to ensure that the rest pose is the only pose to be calculated
                    # differently
                    pose_index += 1
                # Set the pose data for the solver
                solver_data['poses'] = new_pose_data
                # Set the new solver data
                new_rbf_data[solver_name] = solver_data

            rbf_data = new_rbf_data

        # Generate the solvers from the solver data
        for solver_name, solver_data in rbf_data.items():
            api.RBFNode.create_from_data(solver_data)
