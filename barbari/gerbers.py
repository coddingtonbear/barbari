import logging
import os
import re
from typing import Dict

import gerber

from .constants import LayerType


logger = logging.getLogger(__name__)


class UnknownLayerType(ValueError):
    pass


class GerberProject(object):
    LAYER_NAME_PATTERNS: Dict[LayerType, re.Pattern] = {
        LayerType.B_CU: re.compile(".*\-B(?:[._])Cu\..*"),
        LayerType.F_CU: re.compile(".*\-F(?:[._])Cu\..*"),
        LayerType.EDGE_CUTS: re.compile(".*\-Edge(?:[._])Cuts"),
        LayerType.ALIGNMENT: re.compile(".*-Alignment\..*"),
        LayerType.DRILL: re.compile(".*\.drl$"),
    }

    def __init__(self, path):
        self._path = path
        self._layers = {}

        super().__init__()

    @property
    def path(self) -> str:
        return self._path

    def detect_layer_type(self, filename: str, layer):
        for layer_type, pattern in self.LAYER_NAME_PATTERNS.items():
            if pattern.match(filename):
                return layer_type

        raise UnknownLayerType("Unable to guess layer position for {}".format(filename))

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
                logger.error("Could not identify layer type for %s.", full_path)
            except gerber.common.ParseError:
                logger.debug("Unable to parse %s; probably not a gerber.", full_path)

        return self._layers
