from __future__ import annotations

import copy
from dataclasses import dataclass, asdict
import logging
import os
from typing import cast, Dict, Iterable, List, Optional, Type, Union, Tuple

import appdirs
import yaml

from . import exceptions


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
        return self._data.get("depth_per_pass")


class MillHolesJobSpec(JobSpec):
    pass


class MillSlotsJobSpec(MillHolesJobSpec):
    pass


class IsolationRoutingJobSpec(JobSpec):
    @property
    def passes(self) -> float:
        return self._data["passes"]

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


class ToolProfileSpec(JobSpec):
    @property
    def min_size(self) -> float:
        # Exclusive
        return self._data.get("min_size", 0)

    @property
    def max_size(self) -> float:
        # Inclusive
        return self._data.get("max_size", 999)

    @property
    def range(self) -> Tuple[float, float]:
        return self.min_size, self.max_size

    @property
    def range_center(self) -> float:
        return self.min_size + ((self.max_size - self.min_size) / 2)

    def allowed_for_tool_size(self, diameter: float) -> bool:
        range_allowed = "min_size" in self._data or "max_size" in self._data

        if (
            range_allowed and (self.min_size <= diameter <= self.max_size)
        ) or diameter in self.sizes:
            return True

        return False

    def is_better_match_than(
        self, diameter: float, other: Optional[ToolProfileSpec]
    ) -> bool:
        if not other:
            return True
        if diameter in self.sizes and diameter not in other.sizes:
            return True
        if abs(diameter - self.range_center) < abs(diameter - other.range_center):
            return True

        return False

    @property
    def sizes(self) -> List[float]:
        return self._data.get("sizes", [])

    @property
    def specs(self) -> Iterable[Union[MillHolesJobSpec, DrillHolesJobSpec]]:
        specs = []

        for spec_data in self._data["specs"]:
            data = spec_data["params"]
            spec_type = spec_data["type"]
            spec_class: Union[Type[MillHolesJobSpec], Type[DrillHolesJobSpec]]

            if spec_type == "cnc_drill":
                spec_class = DrillHolesJobSpec
            elif spec_type == "mill_holes":
                spec_class = MillHolesJobSpec
            elif spec_type == "mill_slots":
                spec_class = MillSlotsJobSpec
            else:
                raise exceptions.InvalidConfiguration(
                    "Unexpected spec type: %s" % spec_type
                )

            specs.append(spec_class(data))

        return specs


class DrillProfileSpec(ToolProfileSpec):
    @property
    def specs(self) -> Iterable[Union[MillHolesJobSpec, DrillHolesJobSpec]]:
        specs = super().specs

        for spec in specs:
            if not isinstance(spec, (DrillHolesJobSpec, MillHolesJobSpec)):
                raise exceptions.InvalidConfiguration(
                    "Drills support only 'cnc_drill' and 'mill_holes' specifications."
                )

        return specs


class SlotProfileSpec(ToolProfileSpec):
    @property
    def specs(self) -> Iterable[MillSlotsJobSpec]:
        specs = super().specs

        for spec in specs:
            if not isinstance(spec, MillSlotsJobSpec):
                raise exceptions.InvalidConfiguration(
                    "Slots support only 'mill_slots' specifications."
                )

        yield from cast(Iterable[MillSlotsJobSpec], specs)


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

    @classmethod
    def from_file(self, path) -> Config:
        configs: List[Config] = []

        with open(path, "r") as inf:
            loaded = yaml.safe_load(inf)

        includes = loaded.pop("include", [])

        configs.append(Config(loaded))

        config_dir = os.path.dirname(path)
        for include in includes:
            if os.path.splitext(include)[1] in (".yaml", ".yml"):
                include_path = os.path.join(config_dir, include)

                configs.append(Config.from_file(include_path))
            else:
                configs.append(get_config_by_name(include))

        merged = sum(configs, Config({}))

        # By default, we strip descriptions when merging multiple configs;
        # but that's just because we can't make that sane when a user is
        # merging configs at the command-line on an ad-hoc basis; in this
        # particular case, the loaded config *does* know what files are
        # being overlayed, so we should assume its description is OK.
        if "description" in loaded:
            merged._data["description"] = loaded["description"]

        return merged

    @property
    def description(self) -> Optional[str]:
        if "description" in self._data:
            return self._data["description"]

        return None

    @property
    def alignment_holes(self) -> Optional[AlignmentHolesJobSpec]:
        if "alignment_holes" not in self._data:
            return None
        return AlignmentHolesJobSpec(self._data["alignment_holes"])

    @property
    def isolation_routing(self) -> Optional[IsolationRoutingJobSpec]:
        if "isolation_routing" not in self._data:
            return None
        return IsolationRoutingJobSpec(self._data["isolation_routing"])

    @property
    def edge_cuts(self) -> Optional[BoardCutoutJobSpec]:
        if "edge_cuts" not in self._data:
            return None
        return BoardCutoutJobSpec(self._data["edge_cuts"])

    @property
    def drill(self) -> Dict[str, DrillProfileSpec]:
        drill_range_specs = {}

        for name, data in self._data.get("drill", {}).items():
            drill_range_specs[name] = DrillProfileSpec(data)

        return drill_range_specs

    @property
    def slot(self) -> Dict[str, SlotProfileSpec]:
        drill_range_specs = {}

        for name, data in self._data.get("slot", {}).items():
            drill_range_specs[name] = SlotProfileSpec(data)

        return drill_range_specs

    def __add__(self, other: Config) -> Config:
        left = copy.deepcopy(self._data)
        right = other._data

        overwrite = ["alignment_holes", "isolation_routing", "edge_cuts"]
        merge = ["drill", "slot"]

        for key in overwrite:
            if key in right:
                left[key] = right[key]

        for key in merge:
            if key in right:
                left.setdefault(key, {}).update(right[key])

        if "description" in left:
            del left["description"]

        return Config(left)


def get_user_config_dir() -> str:
    return os.path.join(appdirs.user_config_dir("barbari", "coddingtonbear"), "configs")


def get_environment_config_file_path() -> str:
    return os.path.join(
        appdirs.user_config_dir("barbari", "coddingtonbear"), "config.yaml"
    )


@dataclass
class EnvironmentConfig:
    flatcam_path: Optional[str] = None
    python_bin: Optional[str] = None


def get_environment_config() -> EnvironmentConfig:
    try:
        with open(get_environment_config_file_path(), "r") as inf:
            loaded = yaml.safe_load(inf)

            return EnvironmentConfig(**loaded)
    except FileNotFoundError:
        return EnvironmentConfig()


def save_environment_config(cfg: EnvironmentConfig) -> None:
    with open(get_environment_config_file_path(), "w") as outf:
        yaml.safe_dump(asdict(cfg), outf)


def get_default_config_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "configs")


def _get_config_path_map() -> Dict[str, str]:
    configs: Dict[str, str] = {}

    directories = [get_default_config_dir(), get_user_config_dir()]

    for directory in directories:
        if not os.path.exists(directory):
            continue

        for filename in os.listdir(directory):
            name, ext = os.path.splitext(filename)

            if ext in (".yaml", ".yml"):
                configs[name] = os.path.join(directory, filename)

    return configs


def get_available_configs() -> List[str]:
    return list(_get_config_path_map().keys())


def get_config_by_name(name: str) -> Config:
    try:
        config_path = _get_config_path_map()[name]
    except KeyError:
        raise exceptions.ConfigNotFound(f"Config '{name}' not found")

    return Config.from_file(config_path)


def get_merged_config(names: List[str]) -> Config:
    configs: List[Config] = []

    for config_name in names:
        configs.append(get_config_by_name(config_name))

    return sum(configs, Config({}))
