# Copyright Epic Games, Inc. All Rights Reserved.

# Built-in
import argparse
import os
import sys

# External
import maya.standalone

maya.standalone.initialize()

from maya import cmds

# Internal
from epic_pose_wrangler.log import LOG
from epic_pose_wrangler.v2.main import UERBFAPI
from epic_pose_wrangler.v2.extensions import bake_poses


def export(solver_name, maya_path, export_directory, up_axis='z'):
    """
    Opens up the specified Maya file and attempts to export a specific solver to the export directory.

    """
    # Set the up axis for the scene
    cmds.upAxis(axis=up_axis, rv=True)

    # Open the file
    cmds.file(maya_path, o=True, force=True, prompt=False)

    # Load the PoseWrangler API
    api = UERBFAPI(view=False)
    # Get the solver object that matches the given solver name
    solver = api.get_rbf_solver_by_name(solver_name=solver_name)

    # Bake each pose onto the timeline one frame after another, with the default pose being on frame 0.
    bake_poses.bake_poses_to_timeline(start_frame=0, anim_layer=None, solver=solver)

    # Get the skeleton config currently used by Pose Wrangler
    config = api.config

    export_joints = []
    # If the config has a retargeter attached
    if config.retargeter:
        # Get a list of the names of the joints to export. Using the MetaHuman setup as an example, the RBF solvers are
        # set to work on a driver skeleton but on export we want the solver data to use the bind skeleton. In the
        # MetaHuman skeleton config the `transform_export_mapping` is set to retarget from _drv to the bind joint.
        # I.e `thigh_l_drv` to `thigh_l`. By getting the `transform_export_mapping` values, we can find the bind joints
        # and thus export the correct hierarchy.
        # If you are using a custom skeleton or not using a driver skeleton, ensuring you have a single entry under your
        # `transform_mapping` in your skeleton config with a mapping from your root joint to your root joint
        # I.e
        #  "transform_mapping": {
        #   "root": "root"
        # }
        target_joints = list(config.retargeter.transform_export_mapping.values())

        if target_joints:
            # We need to check if the joints listed in the targets exist in the scene to find the correct root joint.
            # Iterate over each target joint until we find one that exists. If no
            target_joint = None
            for joint in target_joints:
                if cmds.ls(joint):
                    target_joint = joint
                    break
            # If a one of the target joints exists, use that hierarchy. Otherwise, export all the joints in the scene.
            # A simple way to ensure this always works is to add the "root": "root" mapping at the top of the transform
            # mapping.
            if target_joint:
                # Get all the parents of the first joint in the list in an attempt to find the root joint
                relatives = cmds.listRelatives(target_joint, allParents=True, fullPath=True) or [target_joint]
                if relatives:
                    parents = [n for n in relatives[0].split('|') if n and cmds.nodeType(n) == 'joint']
                    if parents:
                        # Add the parent and entire hierarchy to the list of export joints
                        export_joints.append(parents[0])
                        export_joints.extend(cmds.listRelatives(parents[0], allDescendents=True, type='joint'))

    # If no export joints were set, use every joint in the scene
    if not export_joints:
        export_joints = cmds.ls(type='joint')

    # If no export joints were set, exit early
    if not export_joints:
        return

    # Select the joints so that fbx export selected can be performed
    cmds.select(export_joints, replace=True)
    LOG.debug("Exporting {joint_count} Joints".format(joint_count=len(export_joints)))

    # Generate an export path
    fbx_path = os.path.join(export_directory, '{solver_name}.fbx'.format(solver_name=solver_name))
    # Run the export
    fbx_export(
        fbx_path,
        animation=True,
        animation_only=False,
        bake_complex_animation=True,
        bake_complex_start=cmds.playbackOptions(q=1, animationStartTime=1),
        bake_complex_end=cmds.playbackOptions(q=1, animationEndTime=1),
        bake_complex_step=1,
        up_axis=up_axis
    )


def fbx_export(
        filepath,
        animation=True,
        # Mesh
        triangulate=False, smoothing_groups=True, hard_edges=False, tangents=True, smooth_mesh=False,
        # Animation
        bake_resample_animation=True, animation_only=False, quaternion='quaternion',
        apply_constant_key_reducer=False,
        bake_complex_animation=True, bake_complex_start=None, bake_complex_end=None, bake_complex_step=1,
        # Objects
        skins=True, shapes=False, input_connections=False, constraints=False, cameras=False, lights=False,
        # Scene
        referenced_assets_content=True, instances=False, cache_file=False, axis_conversion_method='none',
        embedded_textures=False, generate_log=False, use_scene_name=False, in_ascii=False,
        file_version='FBX202000', up_axis='y'
):
    '''
    Exports selected objects
    '''

    if not cmds.pluginInfo('fbxmaya', q=True, loaded=True):
        cmds.loadPlugin('fbxmaya')

    cmds.FBXResetExport()

    # Mesh
    cmds.FBXExportTriangulate('-v', triangulate)  # ?
    cmds.FBXExportSmoothingGroups('-v', smoothing_groups)
    cmds.FBXExportHardEdges('-v', hard_edges)
    cmds.FBXExportTangents('-v', tangents)
    cmds.FBXExportSmoothMesh('-v', smooth_mesh)

    # Animation
    cmds.FBXExportBakeResampleAnimation('-v', bake_resample_animation)
    cmds.FBXExportAnimationOnly('-v', animation_only)
    cmds.FBXExportBakeComplexAnimation('-v', bake_complex_animation)
    cmds.FBXExportBakeComplexStart('-v', bake_complex_start)
    cmds.FBXExportBakeComplexEnd('-v', bake_complex_end)
    cmds.FBXExportBakeComplexStep('-v', bake_complex_step)
    cmds.FBXExportQuaternion('-v', quaternion)  # quaternion|euler|resample
    cmds.FBXExportApplyConstantKeyReducer('-v', apply_constant_key_reducer)

    # make sure we are not exporting any animation.
    # @ref: http://discourse.techart.online/t/solved-problem-exporting-fbx-from-maya-without-animation/8796/3
    if not animation:
        cmds.FBXProperty('Export|IncludeGrp|Animation', '-v', 0)

    # Objects
    cmds.FBXExportSkins('-v', skins)
    cmds.FBXExportShapes('-v', shapes)
    cmds.FBXExportInputConnections('-v', input_connections)
    cmds.FBXExportConstraints('-v', constraints)
    cmds.FBXExportCameras('-v', cameras)
    cmds.FBXExportLights('-v', lights)
    cmds.FBXExportEmbeddedTextures('-v', embedded_textures)

    # Scene
    cmds.FBXExportReferencedAssetsContent('-v', referenced_assets_content)
    cmds.FBXExportInstances('-v', instances)
    cmds.FBXExportCacheFile('-v', cache_file)
    cmds.FBXExportAxisConversionMethod(axis_conversion_method)
    cmds.FBXExportGenerateLog('-v', generate_log)
    cmds.FBXExportUseSceneName('-v', use_scene_name)
    cmds.FBXExportInAscii('-v', in_ascii)
    cmds.FBXExportFileVersion('-v', file_version)
    cmds.FBXExportUpAxis(up_axis)

    cmds.FBXExport('-s', '-f', filepath)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description="PoseWrangler Command Line Pose Exporter")
    arg_parser.add_argument('-sn', '--solverName', help='Name of the solver to export the poses for', required=True)
    arg_parser.add_argument('-p', '--path', help='Local path to the scene containing the RBF setup', required=True)
    arg_parser.add_argument('-ed', '--exportDirectory', help='Local path to the export folder', required=True)
    arg_parser.add_argument('-ua', '--upAxis', help='y or z', default='z', required=False)

    known_args, unknown_args = arg_parser.parse_known_args(sys.argv)
    export(solver_name=known_args.solverName, maya_path=known_args.path, export_directory=known_args.exportDirectory,
           up_axis=known_args.upAxis)

    # exit
    os._exit(0)
