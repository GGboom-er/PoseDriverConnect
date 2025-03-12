# Copyright Epic Games, Inc. All Rights Reserved.

# Internal
from . import (
    invalid_config,
    mirror_mapping_config,
    skeleton_config
)


def get_config(file_path=None, data=None):
    """
    Get the correct config given a path or data
    :param file_path:
    :param data:
    :return: valid config
    """
    # List of configs in ascending version order
    configs = [mirror_mapping_config.MirrorMappingConfig, skeleton_config.SkeletonConfig]
    # Default config is invalid, so all config features will return disabled
    valid_config = invalid_config.InvalidConfig(file_path=file_path, data=data)
    # Iterate through the configs
    for config in configs:
        # If the config is valid
        if config.validate(file_path=file_path, data=data):
            # Create an instance of the config
            valid_config = config(file_path=file_path, data=data)
            # If the config is not the latest config, upgrade the data to the new format
            if valid_config != configs[-1]:
                data = valid_config.upgrade()

    return valid_config
