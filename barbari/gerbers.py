import logging
import os

import gerber

from .constants import LayerType


logger = logging.getLogger(__name__)


class UnknownLayerType(ValueError):
    pass


class GerberProject(object):
    def __init__(self, path):
        self._path = path
        self._layers = {}

        super().__init__()

    @property
    def path(self) -> str:
        return self._path

    def detect_layer_type(self, filename: str, layer):
        if '-B.Cu.' in filename:
            return LayerType.B_CU
        elif '-F.Cu.' in filename:
            return LayerType.F_CU
        elif '-Edge.Cuts.' in filename:
            return LayerType.EDGE_CUTS
        elif '-Alignment.' in filename:
            return LayerType.ALIGNMENT
        elif filename.endswith('.drl'):
            return LayerType.DRILL

        raise UnknownLayerType(
            "Unable to guess layer position for {}".format(filename)
        )

    def get_layers(self):
        if self._layers:
            return self._layers

        for filename in os.listdir(self._path):
            full_path = os.path.join(
                self._path,
                filename,
            )
            if not os.path.isfile(full_path):
                continue

            try:
                layer = gerber.read(full_path)
                layer_type = self.detect_layer_type(filename, layer)
                self._layers[layer_type] = layer
                logger.debug("Loaded %s", full_path)
            except UnknownLayerType:
                logger.error(
                    "Could not identify layer type for %s.", full_path
                )
            except gerber.common.ParseError:
                logger.debug(
                    "Unable to parse %s; probably not a gerber.", full_path
                )

        return self._layers
