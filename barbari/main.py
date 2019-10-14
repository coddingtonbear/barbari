import argparse
import json
import logging
import os
import sys

from . import config, gerbers, flatcam


logger = logging.getLogger(__name__)


COMMANDS = {}


def command(fn):
    global COMMANDS

    COMMANDS[fn.__name__] = fn


@command
def build(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    parser.add_argument('--verbose', default=False, action='store_true')
    args = parser.parse_args(args)

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


@command
def generate_config(*args):
    parser = argparse.ArgumentParser()
    parser.parse_args(args)

    os.makedirs(
        os.path.dirname(config.get_user_config_path()),
        exist_ok=True
    )
    with open(config.get_user_config_path(), 'w') as outf:
        outf.write(json.dumps(config.get_default_config_dict()))

    print("Default configuration copied to %s" % config.get_user_config_path())


def main(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=COMMANDS.keys())
    args, extra = parser.parse_known_args()

    COMMANDS[args.command](*extra)


if __name__ == '__main__':
    main(*sys.argv[1:])
