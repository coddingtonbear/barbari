import argparse

from rich.syntax import Syntax
import yaml

from .. import config
from . import BaseCommand


class Command(BaseCommand):
    FORMAT_HUMAN = "human"
    FORMAT_YAML = "yaml"

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "config",
            nargs="+",
            help="Configuration file to display; later configs override earlier configs -- you can use this to layer your configuration.",
        )
        return super().add_arguments(parser)

    def handle(self) -> None:
        conf = config.get_merged_config(self.options.config)

        self.console.print(Syntax(yaml.safe_dump(conf._data), "yaml"))
