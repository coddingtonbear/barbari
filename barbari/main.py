import argparse
import logging
import sys

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as enable_rich_traceback

from . import exceptions
from .commands import get_installed_commands


logger = logging.getLogger(__name__)


def main(*args):
    enable_rich_traceback()

    commands = get_installed_commands()

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", default=False, action="store_true")
    parser.add_argument("--verbose", default=False, action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    for cmd_name, cmd_class in commands.items():
        parser_kwargs = {}

        cmd_help = cmd_class.get_help()
        if cmd_help:
            parser_kwargs["help"] = cmd_help

        subparser = subparsers.add_parser(cmd_name, **parser_kwargs)
        cmd_class._add_arguments(subparser)

    args = parser.parse_args()

    logging.basicConfig(
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
        level=logging.DEBUG if args.verbose else logging.INFO,
    )

    if args.debug:
        import debugpy

        debugpy.listen(5678)
        debugpy.wait_for_client()

    console = Console()

    try:
        commands[args.command](args).handle()
    except exceptions.BarbariError as e:
        console.print(f"[red]{e}[/red]")
    except exceptions.BarbariUserError as e:
        console.print(f"[yellow]{e}[/yellow]")
    except Exception:
        console.print_exception()


if __name__ == "__main__":
    main(*sys.argv[1:])
