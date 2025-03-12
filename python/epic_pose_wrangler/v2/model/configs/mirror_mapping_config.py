# Copyright Epic Games, Inc. All Rights Reserved.

# Built-in
import json

# Internal
from epic_pose_wrangler.v2.model.configs.base_config import BaseConfig
from epic_pose_wrangler.v2.model import mirror_mapping


class MirrorMappingConfig(BaseConfig):
    @classmethod
    def validate(cls, file_path=None, data=None):
        if file_path:
            with open(file_path, 'r') as f:
                data = json.loads(f.read())

        if data:
            matches = [data.get('solver_expression', None), data.get('transform_expression', None)]
            return all(matches)

        return False

    def __init__(self, file_path=None, data=None):
        super(MirrorMappingConfig, self).__init__(file_path=file_path, data=data)
        self._mirror_mapping = mirror_mapping.MirrorMapping(file_path=file_path, mapping_data=data)

    @property
    def mirror_mapping(self):
        return self._mirror_mapping

    def upgrade(self):
        data = {
            'retargeting': {
                'transform_mapping': {},
                'import': {},
                'export': {}
            },
            'mirror_mapping': self._mirror_mapping.mapping_data
        }
        if self._file_path:
            with open(self._file_path, 'w') as f:
                f.write(json.dumps(data))

        return data
