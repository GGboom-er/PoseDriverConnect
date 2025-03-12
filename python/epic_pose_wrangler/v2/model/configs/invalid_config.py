# Copyright Epic Games, Inc. All Rights Reserved.


# Internal
from epic_pose_wrangler.v2.model.configs.base_config import BaseConfig


class InvalidConfig(BaseConfig):
    """
    Class for handling skeleton settings i.e mirror mapping and import/export retargeting
    """

    @classmethod
    def validate(cls, file_path=None, data=None):
        return True

    @property
    def retargeter(self):
        return None

    @property
    def mirror_mapping(self):
        return None

    def upgrade(self):
        return self._data
