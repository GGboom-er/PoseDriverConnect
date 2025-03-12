# Copyright Epic Games, Inc. All Rights Reserved.

# Built-in
import copy

# Internal
from epic_pose_wrangler.log import LOG


class Retargeter(object):
    def __init__(self, retargeting_data=None):
        self._retargeting_data = retargeting_data or {}
        self._transform_import_mapping = self._generate_mapping(io='import')
        self._transform_export_mapping = self._generate_mapping(io='export')

    def _generate_mapping(self, io='import'):
        mapping_settings = self._retargeting_data.get(io)
        if not mapping_settings:
            return {}

        transform_in_index = mapping_settings.get('source')
        transform_out_index = mapping_settings.get('target')
        if transform_in_index is None or transform_out_index is None:
            LOG.warning(
                "Unable to generate retargeting map, no `source` or `target` index specified under `{io}`".format(
                    io=io)
            )
            return {}

        mapping_data = {}
        for in_transform, out_transform in self._retargeting_data.get('transform_mapping', {}).items():
            data = (in_transform, out_transform)
            mapping_data[data[transform_in_index]] = data[transform_out_index]

        return mapping_data

    @property
    def retargeting_data(self):
        return copy.deepcopy(self._retargeting_data)

    @property
    def transform_import_mapping(self):
        return copy.deepcopy(self._transform_import_mapping)

    @property
    def transform_export_mapping(self):
        return copy.deepcopy(self._transform_export_mapping)
