import logging
import os
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Union

from gerber import excellon

from .gerbers import GerberProject
from .config import (
    Config,
    DrillHolesJobSpec,
    IsolationRoutingJobSpec,
    JobSpec,
    MillHolesJobSpec,
    MillSlotsJobSpec,
    ToolProfileSpec,
)
from .constants import LayerType, FlatcamLayer


logger = logging.getLogger(__name__)


class FlatcamProcess(object):
    def __init__(self, cmd, *args, **params):
        self._cmd = cmd
        self._args = args
        self._params = params

    def __str__(self):
        cmd_parts = [
            self._cmd,
            *self._args,
            *[
                "-{key} {value}".format(
                    key=key,
                    value=value,
                )
                for key, value in self._params.items()
            ],
        ]

        return " ".join(cmd_parts)

    def get_layer_name(self, layer: Union[FlatcamLayer, str]):
        if isinstance(layer, FlatcamLayer):
            return layer.value

        return layer


class FlatcamCNCJob(FlatcamProcess):
    def __init__(
        self,
        config: JobSpec,
        input_layer: Union[FlatcamLayer, str],
        output_layer: Union[FlatcamLayer, str],
    ):
        extra_kwargs = {}
        if config.multi_depth or config.depth_per_pass:
            extra_kwargs["dpp"] = config.depth_per_pass

        return super().__init__(
            "cncjob",
            self.get_layer_name(input_layer),
            z_cut=config.cut_z,
            z_move=config.travel_z,
            feedrate=config.feed_rate,
            dia=config.tool_size,
            spindlespeed=config.spindle_speed,
            **extra_kwargs,
            outname=self.get_layer_name(output_layer)
        )


class FlatcamDrillCNCJob(FlatcamProcess):
    def __init__(
        self,
        config: DrillHolesJobSpec,
        input_layer: Union[FlatcamLayer, str],
        output_layer: Union[FlatcamLayer, str],
        drilled_dias: List[float],
    ):
        return super().__init__(
            "drillcncjob",
            self.get_layer_name(input_layer),
            drilled_dias=",".join(str(dia) for dia in drilled_dias),
            drillz=config.drill_z,
            travelz=config.travel_z,
            feedrate_z=config.feed_rate,
            spindlespeed=config.spindle_speed,
            outname=self.get_layer_name(output_layer),
        )


class FlatcamMillHoles(FlatcamProcess):
    def __init__(
        self,
        config: MillHolesJobSpec,
        input_layer: Union[FlatcamLayer, str],
        output_layer: Union[FlatcamLayer, str],
        milled_dias: List[float],
    ):
        return super().__init__(
            "milldrills",
            self.get_layer_name(input_layer),
            tooldia=config.tool_size,
            milled_dias=",".join(str(dia) for dia in milled_dias),
            outname=self.get_layer_name(output_layer),
        )


class FlatcamMillSlots(FlatcamProcess):
    def __init__(
        self,
        config: MillSlotsJobSpec,
        input_layer: Union[FlatcamLayer, str],
        output_layer: Union[FlatcamLayer, str],
        milled_dias: List[float],
    ):
        return super().__init__(
            "millslots",
            self.get_layer_name(input_layer),
            tooldia=config.tool_size,
            milled_dias=",".join(str(dia) for dia in milled_dias),
            outname=self.get_layer_name(output_layer),
        )


class FlatcamIsolate(FlatcamProcess):
    def __init__(
        self,
        config: IsolationRoutingJobSpec,
        input_layer: Union[FlatcamLayer, str],
        output_layer: Union[FlatcamLayer, str],
    ):
        return super().__init__(
            "isolate",
            self.get_layer_name(input_layer),
            dia=config.tool_size,
            passes=int(config.passes),
            overlap=config.pass_overlap,
            combine=1,
            outname=self.get_layer_name(output_layer),
        )


class FlatcamWriteGcode(FlatcamProcess):
    def __init__(
        self,
        layer: Union[FlatcamLayer, str],
        path: str,
        counter: int,
        name: str,
        tool_name: str,
        tool_size: float,
    ):
        return super().__init__(
            "write_gcode",
            self.get_layer_name(layer),
            os.path.join(
                path,
                "{counter}.{name}.{tool_size}.{tool_name}.gcode".format(
                    counter=str(counter).zfill(2),
                    name=name,
                    tool_name=tool_name,
                    tool_size=tool_size,
                ),
            ),
        )


class FlatcamProjectGenerator(object):
    def __init__(self, gerbers: GerberProject, config: Config):
        self._gerbers = gerbers
        self._config = config
        self._gcode_counter = 0

        super().__init__()

    @property
    def counter(self) -> int:
        self._gcode_counter += 1
        return self._gcode_counter

    @property
    def counter_str(self) -> str:
        return str(self.counter).zfill(2)

    @property
    def config(self) -> Config:
        return self._config

    @property
    def gerbers(self) -> GerberProject:
        return self._gerbers

    def _load_layers(self) -> Iterable[FlatcamProcess]:
        for layer_type, layer in self.gerbers.get_layers().items():
            if layer_type == LayerType.DRILL:
                yield FlatcamProcess(
                    "open_excellon",
                    layer.filename,
                    outname=layer_type.value,
                )
            else:
                yield FlatcamProcess(
                    "open_gerber",
                    layer.filename,
                    outname=layer_type.value,
                )

    def _alignment_holes(self) -> Iterable[FlatcamProcess]:
        if not self.config.alignment_holes:
            return

        logger.debug("Processing alignment holes...")

        layers = self.gerbers.get_layers()

        edge_cuts = layers[LayerType.EDGE_CUTS]

        min_x = edge_cuts.bounds[0][0]
        max_x = edge_cuts.bounds[0][1]
        min_y = edge_cuts.bounds[1][0]
        max_y = edge_cuts.bounds[1][1]

        hole_offset = (
            self.config.alignment_holes.hole_size / 2
        ) + self.config.alignment_holes.hole_offset
        holes = [
            (
                min_x + hole_offset,
                min_y - hole_offset,
            ),
            (
                max_x - hole_offset,
                min_y - hole_offset,
            ),
        ]

        # This command took some trial and error to figure out --
        # the "holes" parameter is undocumented, and I was only
        # able to figure out how to set the rotation point by
        # reading the source :shrug:
        yield FlatcamProcess(
            "aligndrill",
            FlatcamLayer.EDGE_CUTS.value,
            axis=self.config.alignment_holes.mirror_axis,
            dia=self.config.alignment_holes.hole_size,
            holes='"' + ",".join(str(hole) for hole in holes) + '"',
            dist=max_y / 2,
        )
        yield FlatcamProcess(
            "mirror",
            FlatcamLayer.B_CU.value,
            axis=self.config.alignment_holes.mirror_axis,
            box="edge_cuts",
        )
        yield FlatcamMillHoles(
            self.config.alignment_holes,
            FlatcamLayer.ALIGNMENT,
            FlatcamLayer.ALIGNMENT_PATH,
            milled_dias=[self.config.alignment_holes.hole_size],
        )
        yield FlatcamCNCJob(
            self.config.alignment_holes,
            FlatcamLayer.ALIGNMENT_PATH,
            FlatcamLayer.ALIGNMENT_CNC,
        )
        yield FlatcamWriteGcode(
            FlatcamLayer.ALIGNMENT_CNC,
            self.gerbers.path,
            self.counter,
            "alignment_holes",
            "end_mill",
            self.config.alignment_holes.tool_size,
        )

    def _copper(self) -> Iterable[FlatcamProcess]:
        if not self.config.isolation_routing:
            return

        logger.debug("Processing isolation routing...")

        yield FlatcamIsolate(
            self.config.isolation_routing,
            FlatcamLayer.B_CU,
            FlatcamLayer.B_CU_PATH,
        )
        yield FlatcamCNCJob(
            self.config.isolation_routing,
            FlatcamLayer.B_CU_PATH,
            FlatcamLayer.B_CU_CNC,
        )
        yield FlatcamWriteGcode(
            FlatcamLayer.B_CU_CNC,
            self.gerbers.path,
            self.counter,
            "b_cu",
            "engraving_bit",
            self.config.isolation_routing.tool_size,
        )
        yield FlatcamIsolate(
            self.config.isolation_routing,
            FlatcamLayer.F_CU,
            FlatcamLayer.F_CU_PATH,
        )
        yield FlatcamCNCJob(
            self.config.isolation_routing,
            FlatcamLayer.F_CU_PATH,
            FlatcamLayer.F_CU_CNC,
        )
        yield FlatcamWriteGcode(
            FlatcamLayer.F_CU_CNC,
            self.gerbers.path,
            self.counter,
            "f_cu",
            "engraving_bit",
            self.config.isolation_routing.tool_size,
        )

    def _get_spec_for_tool(
        self, tool, specs: Mapping[str, ToolProfileSpec]
    ) -> Optional[str]:
        selected: Optional[str] = None

        for spec_name, spec in specs.items():
            if spec.allowed_for_tool_size(tool.diameter) and spec.is_better_match_than(
                tool.diameter, specs[selected] if selected else None
            ):
                selected = spec_name

        return selected

    def _get_tool_hit_count(
        self,
        layer: excellon.ExcellonFile,
        tool: excellon.ExcellonTool,
        slot: bool = False,
    ):
        counter = 0

        expected_class = excellon.DrillSlot if slot else excellon.DrillHit

        for hit in layer.hits:
            if isinstance(hit, expected_class) and hit.tool == tool:
                counter += 1

        return counter

    def _drill(self) -> Iterable[FlatcamProcess]:
        if not self.config.drill:
            return

        logger.debug("Processing drills...")

        layer: excellon.ExcellonFile = self.gerbers.get_layers()[LayerType.DRILL]

        process_map: Dict[str, List[int]] = {}
        for tool_number, tool in layer.tools.items():
            if not self._get_tool_hit_count(layer, tool):
                logger.debug(
                    "Tool %s (%s dia) has no drill hits.",
                    tool_number,
                    tool.diameter,
                )
                continue

            selected_spec = self._get_spec_for_tool(tool, self.config.drill)
            if selected_spec:
                logger.debug(
                    "Assigning tool %s (%s dia) to drill process %s.",
                    tool_number,
                    tool.diameter,
                    selected_spec,
                )
                process_map.setdefault(selected_spec, []).append(tool_number)
            else:
                logger.error(
                    "Unable to find compatible drill profile for tool "
                    "#%s having diameter %s; omitting from output.",
                    tool_number,
                    tool.diameter,
                )

        for process_name, tool_numbers in process_map.items():
            specs = self.config.drill[process_name].specs
            for idx, spec in enumerate(specs):
                layer_name = "drill_{name}_{idx}".format(
                    name=process_name,
                    idx=idx,
                )
                if isinstance(spec, DrillHolesJobSpec):
                    yield FlatcamDrillCNCJob(
                        spec,
                        FlatcamLayer.DRILL,
                        layer_name,
                        [layer.tools[n].diameter for n in tool_numbers],
                    )
                    yield FlatcamWriteGcode(
                        layer_name,
                        self.gerbers.path,
                        self.counter,
                        "drill_{name}".format(name=process_name),
                        "drill",
                        spec.tool_size,
                    )
                elif isinstance(spec, MillHolesJobSpec):
                    yield FlatcamMillHoles(
                        spec,
                        FlatcamLayer.DRILL,
                        layer_name,
                        [layer.tools[n].diameter for n in tool_numbers],
                    )
                    yield FlatcamCNCJob(spec, layer_name, layer_name + "_cnc")
                    yield FlatcamWriteGcode(
                        layer_name + "_cnc",
                        self.gerbers.path,
                        self.counter,
                        "drill_{name}".format(name=process_name),
                        "end_mill",
                        spec.tool_size,
                    )
                else:
                    raise ValueError("Unhandled spec!")

    def _slot(self) -> Iterable[FlatcamProcess]:
        if not self.config.slot:
            return

        logger.debug("Processing slots...")

        layer: excellon.ExcellonFile = self.gerbers.get_layers()[LayerType.DRILL]

        process_map: Dict[str, List[int]] = {}
        for tool_number, tool in layer.tools.items():
            if not self._get_tool_hit_count(layer, tool, slot=True):
                logger.debug(
                    "Tool %s (%s dia) has no slot hits.",
                    tool_number,
                    tool.diameter,
                )
                continue

            selected_spec = self._get_spec_for_tool(tool, self.config.slot)
            if selected_spec:
                logger.debug(
                    "Assigning tool %s (%s dia) to slot process %s.",
                    tool_number,
                    tool.diameter,
                    selected_spec,
                )
                process_map.setdefault(selected_spec, []).append(tool_number)
            else:
                logger.error(
                    "Unable to find compatible slot profile for tool "
                    "#%s having diameter %s; omitting from output.",
                    tool_number,
                    tool.diameter,
                )

        for process_name, tool_numbers in process_map.items():
            specs = self.config.slot[process_name].specs
            for idx, spec in enumerate(specs):
                layer_name = "slot_{name}_{idx}".format(
                    name=process_name,
                    idx=idx,
                )
                assert isinstance(spec, MillSlotsJobSpec)

                yield FlatcamMillSlots(
                    spec,
                    FlatcamLayer.DRILL,
                    layer_name,
                    [layer.tools[n].diameter for n in tool_numbers],
                )
                yield FlatcamCNCJob(spec, layer_name, layer_name + "_cnc")
                yield FlatcamWriteGcode(
                    layer_name + "_cnc",
                    self.gerbers.path,
                    self.counter,
                    "slot_{name}".format(name=process_name),
                    "end_mill",
                    spec.tool_size,
                )

    def _edge_cuts(self) -> Iterable[FlatcamProcess]:
        if not self.config.edge_cuts:
            return

        logger.debug("Processing edge cuts...")

        yield FlatcamProcess(
            "cutout",
            FlatcamLayer.EDGE_CUTS.value,
            dia=self.config.edge_cuts.tool_size,
            margin=self.config.edge_cuts.margin,
            gapsize=self.config.edge_cuts.gap_size,
            gaps=self.config.edge_cuts.gaps,
        )
        yield FlatcamCNCJob(
            self.config.edge_cuts,
            FlatcamLayer.EDGE_CUTS_PATH,
            FlatcamLayer.EDGE_CUTS_CNC,
        )
        yield FlatcamWriteGcode(
            FlatcamLayer.EDGE_CUTS_CNC,
            self.gerbers.path,
            self.counter,
            "edge_cuts",
            "end_mill",
            self.config.edge_cuts.tool_size,
        )

    def _quit(self) -> Iterable[FlatcamProcess]:
        yield FlatcamProcess("quit_flatcam")

    def get_cnc_processes(self) -> Iterable[FlatcamProcess]:
        major_step_generators: List[Callable[[], Iterable[FlatcamProcess]]] = [
            self._load_layers,
            self._alignment_holes,
            self._copper,
            self._drill,
            self._slot,
            self._edge_cuts,
            self._quit,
        ]

        for major_step in major_step_generators:
            for step in major_step():
                logger.debug("Step %s generated", step)
                yield step
