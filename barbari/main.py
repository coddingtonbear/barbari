import argparse
import enum
import logging
import os
import sys

import gerber


logger = logging.getLogger(__name__)


class LayerType(enum.Enum):
    B_CU = 'b_cu'
    F_CU = 'f_cu'
    ALIGNMENT = 'alignment'
    EDGE_CUTS = 'edge_cuts'
    DRILL = 'drill'


class UnknownLayerType(ValueError):
    pass


class GerberProject(object):
    def __init__(self, path):
        self._path = path
        self._layers = {}

        super().__init__()

    def detect_layer_type(self, filename, layer):
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


def main(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument('input_directory')
    args = parser.parse_args()

    project = GerberProject(args.input_directory)
    print(project.get_layers())


if __name__ == '__main__':
    main(*sys.argv[1:])
