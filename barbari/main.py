import argparse
import logging
import os
import sys

from . import config, gerbers, flatcam


logger = logging.getLogger(__name__)


def main(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    parser.add_argument('--verbose', default=False, action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    project = gerbers.GerberProject(
        os.path.abspath(
            os.path.expanduser(
                args.directory
            )
        )
    )
    configuration = config.get_config()
    generator = flatcam.FlatcamProjectGenerator(project, configuration)

    output_file = os.path.join(
        args.directory,
        "flatcam_shell",
    )
    processes = generator.get_cnc_processes()
    with open(output_file, "w") as outf:
        for process in processes:
            outf.write(str(process))
            outf.write('\n')


if __name__ == '__main__':
    main(*sys.argv[1:])
