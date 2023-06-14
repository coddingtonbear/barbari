import argparse
import os
import shutil

from .. import config
from . import BaseCommand


class Command(BaseCommand):
    DEFAULT_CONFIG = "example.yaml"

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "name", help="Name of the configuration you would like to generate."
        )
        return super().add_arguments(parser)

    def handle(self) -> None:
        final_path = f"{self.options.name}.yaml"

        os.makedirs(
            config.get_user_config_dir(), exist_ok=True
        )
        shutil.copyfile(
            os.path.join(
                config.get_default_config_dir(),
                self.DEFAULT_CONFIG,
            ),
            os.path.join(
                config.get_user_config_dir(),
                final_path,
            )
        )

        self.console.print(
            f"Configuration '{self.options.name}' written to '{final_path}'."
        )
