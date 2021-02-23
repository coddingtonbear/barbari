import argparse
import os

import yaml

from .. import config
from . import BaseCommand


class Command(BaseCommand):
    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "name", help="Name of the configuration you would like to generate."
        )
        return super().add_arguments(parser)

    def handle(self) -> None:
        final_path = f"{self.options.name}.yaml"

        os.makedirs(
            os.path.dirname(config.get_user_config_path(final_path)), exist_ok=True
        )
        with open(config.get_user_config_path(final_path), "w") as outf:
            outf.write(yaml.safe_dump(config.get_default_config_dict()))

        self.console.print(
            f"Configuration '{self.options.name}' written to '{final_path}'."
        )
