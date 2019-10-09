import argparse
import logging
import sys

from . import gerbers


logger = logging.getLogger(__name__)


def main(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument('input_directory')
    args = parser.parse_args()

    project = gerbers.GerberProject(args.input_directory)
    print(project.get_layers())


if __name__ == '__main__':
    main(*sys.argv[1:])
