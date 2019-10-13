import json
import logging
import os
from typing import Dict, List, Union

import appdirs


logger = logging.getLogger(__name__)


class JobSpec(object):
    def __init__(self, data):
        self._data = data

        super().__init__()

    @property
    def tool_size(self) -> float:
        return self._data["tool_size"]

    @property
    def cut_z(self) -> float:
        return self._data["cut_z"]

    @property
    def travel_z(self) -> float:
        return self._data["travel_z"]

    @property
    def feed_rate(self) -> float:
        return self._data["feed_rate"]

    @property
    def spindle_speed(self) -> int:
        return self._data["spindle_speed"]

    @property
    def multi_depth(self) -> bool:
        return self._data.get("multi_depth", False)

    @property
    def depth_per_pass(self) -> float:
        return self._data["depth_per_pass"]


class MillHolesJobSpec(JobSpec):
    pass


class IsolationRoutingJobSpec(JobSpec):
    @property
    def width(self) -> float:
        return self._data["width"]

    @property
    def pass_overlap(self) -> float:
        return self._data.get("pass_overlap", 1.0)


class BoardCutoutJobSpec(JobSpec):
    @property
    def margin(self) -> float:
        return self._data["margin"]

    @property
    def gap_size(self) -> float:
        return self._data["gap_size"]

    @property
    def gaps(self) -> str:
        return self._data["gaps"]


class DrillHolesJobSpec(JobSpec):
    @property
    def drill_z(self) -> float:
        return self._data.get("drill_z")


class DrillProfileSpec(JobSpec):
    @property
    def min_size(self) -> float:
        return self._data.get("min_size", 0)

    @property
    def max_size(self) -> float:
        return self._data.get("max_size", float('inf'))

    @property
    def specs(self) -> List[Union[MillHolesJobSpec, DrillHolesJobSpec]]:
        specs = []

        for spec_data in self._data["specs"]:
            data = spec_data["params"]
            spec_type = spec_data["type"]
            spec_class = None

            if spec_type == "cnc_drill":
                spec_class = DrillHolesJobSpec
            elif spec_type == "mill_holes":
                spec_class = MillHolesJobSpec
            else:
                raise ValueError(
                    "Unexpected spec type: %s" % spec_type
                )

            specs.append(spec_class(data))

        return specs


class AlignmentHolesJobSpec(MillHolesJobSpec):
    @property
    def mirror_axis(self) -> str:
        return self._data.get("mirror_axis", "X")

    @property
    def hole_size(self) -> float:
        return self._data["hole_size"]

    @property
    def hole_offset(self) -> float:
        return self._data["hole_offset"]


class Config(object):
    def __init__(self, data):
        self._data = data

    @property
    def alignment_holes(self) -> MillHolesJobSpec:
        return AlignmentHolesJobSpec(self._data["alignment_holes"])

    @property
    def isolation_routing(self) -> IsolationRoutingJobSpec:
        return IsolationRoutingJobSpec(self._data["isolation_routing"])

    @property
    def edge_cuts(self) -> BoardCutoutJobSpec:
        return BoardCutoutJobSpec(self._data["edge_cuts"])

    @property
    def drill(self) -> Dict[str, DrillProfileSpec]:
        drill_range_specs = {}

        for name, data in self._data["drill_profiles"].items():
            drill_range_specs[name] = DrillProfileSpec(data)

        return drill_range_specs


def get_user_config_path() -> str:
    return os.path.join(
        appdirs.user_config_dir(
            "barbari",
            "coddingtonbear"
        ),
        "config.json"
    )


def get_user_config_dict() -> dict:
    path = get_user_config_path()

    with open(path, "r") as inf:
        return json.load(inf)


def get_default_config_path() -> str:
    return os.path.join(
        os.path.dirname(__file__),
        "config.json"
    )


def get_default_config_dict() -> dict:
    with open(get_default_config_path(), "r") as inf:
        return json.load(inf)


def get_config() -> Config:
    try:
        logger.info(
            "Looking for user configuration at %s...",
            get_user_config_path()
        )
        config_data = get_user_config_dict()
        logger.info(
            "Loaded user-specified configuration from %s",
            get_user_config_path()
        )
    except OSError:
        logger.info("User configuration not found.")
        config_data = get_default_config_dict()
        logger.info(
            "Loaded default configuration from %s",
            get_default_config_path()
        )

    return Config(config_data)
