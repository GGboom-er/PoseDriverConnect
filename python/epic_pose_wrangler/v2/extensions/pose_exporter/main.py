# Copyright Epic Games, Inc. All Rights Reserved.

# Built-in
import os
import subprocess
import sys
import shutil
import uuid
from multiprocessing.pool import ThreadPool

# External
from maya import cmds

# Internal
from epic_pose_wrangler.log import LOG
from epic_pose_wrangler.v2.model import base_extension, api


class PoseExporter(base_extension.PoseWranglerExtension):
    __category__ = "Pose Exporter"

    @property
    def view(self):
        if self._view is not None:
            return self._view
        from epic_pose_wrangler.v2.extensions.pose_exporter import view
        self._view = view.PoseExporterView()
        self._view.export.connect(self.export)
        return self._view

    def export(self, json_file, solvers=None, export_directory="", up_axis="z", delta=False):
        if self._view and not solvers:
            LOG.debug("Grabbing solvers from current UI selection")
            ui_context = self.api.get_ui_context()
            solvers = [api.RBFNode(s) for s in ui_context.current_solvers]

        self.execute(
            json_file=json_file, solvers=solvers, export_directory=export_directory, up_axis=up_axis, delta=delta
        )

    def execute(self, context=None, **kwargs):
        json_file = kwargs.get('json_file')
        export_directory = kwargs.get('export_directory')
        up_axis = kwargs.get('up_axis', 'z')
        solvers = kwargs.get('solvers') or self.api.rbf_solvers
        delta = kwargs.get('delta', False)
        export_instances = kwargs.get('export_instances', 5)
        if not json_file:
            LOG.warning('Unable to export, `json_file` not specified')
        if not solvers:
            LOG.warning("Unable to export, no solvers specified")
            return

        # Create a temporary directory to store the current scene
        temp_export_directory = "{export_dir}/_temp_posewrangler_export".format(
            export_dir=export_directory)

        if not os.path.exists(temp_export_directory):
            os.makedirs(temp_export_directory)

        maya_file = os.path.join(temp_export_directory, '{}.ma'.format(uuid.uuid4()))

        cmds.file(
            maya_file, force=True, type='mayaAscii', exportAll=True
        )

        self.api.serialize_to_file(file_path=json_file, solvers=solvers, delta=delta)

        process_file = os.path.join(os.path.dirname(__file__), 'batch.py')
        env = dict(os.environ)
        env['PYTHONPATH'] += ";{}".format(';'.join(sys.path))

        thread_pool = ThreadPool(export_instances)

        for solver in solvers:
            if not isinstance(solver, api.RBFNode):
                solver_name = solver
                solver = self.api.get_rbf_solver_by_name(solver)
                if not solver:
                    LOG.warning(
                        "Unable to find solver with name: {solver_name}, skipping".format(solver_name=solver_name)
                    )
                    continue

            solver_name = str(solver)
            thread_pool.apply_async(
                _execute_process,
                (process_file, solver_name, maya_file, export_directory, up_axis, env)
            )

        thread_pool.close()
        thread_pool.join()

        if os.path.exists(temp_export_directory):
            shutil.rmtree(temp_export_directory)


def _execute_process(script_path, solver_name, maya_file, export_directory, up_axis, environment):
    process = subprocess.Popen(
        [
            'mayapy',
            script_path,
            '--solverName',
            solver_name,
            '--path',
            maya_file,
            '--exportDirectory',
            export_directory,
            '--upAxis',
            up_axis
        ],
        shell=False,
        stdout=None,
        stderr=None,
        env=environment
    )
    process.wait()
