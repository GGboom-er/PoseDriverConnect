# Copyright Epic Games, Inc. All Rights Reserved.

# Built-in
import json

# Internal
from epic_pose_wrangler.v2.model import mirror_mapping, retargeting
from epic_pose_wrangler.v2.model.configs.base_config import BaseConfig


class SkeletonConfig(BaseConfig):
    """
    Class for handling skeleton settings i.e mirror mapping and import/export retargeting
    """

    @classmethod
    def validate(cls, file_path=None, data=None):
        if file_path:
            with open(file_path, 'r') as f:
                data = json.loads(f.read())

        if data:
            return bool(data.get('mirror_mapping', None))

        return False

    def __init__(self, file_path=None, data=None):
        if file_path and not data:
            with open(file_path, 'r') as f:
                data = json.loads(f.read())

        super(SkeletonConfig, self).__init__(file_path=file_path, data=data)
        self._retargeter = retargeting.Retargeter(retargeting_data=data.get('retargeting', {}))
        self._mirror_mapping = mirror_mapping.MirrorMapping(mapping_data=data.get('mirror_mapping', {}))

    @property
    def retargeter(self):
        return self._retargeter

    @property
    def mirror_mapping(self):
        return self._mirror_mapping

    def upgrade(self):
        return self._data
