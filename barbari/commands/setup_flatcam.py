import argparse
from barbari.exceptions import BarbariFlatcamError
import subprocess

from .. import config
from . import BaseCommand


class Command(BaseCommand):
    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--flatcam",
            # default="./FlatCAM.py",
            required=True,
            help="Path to flatcam executable (FlatCAM.py)",
        )
        parser.add_argument(
            "--python-bin",
            default="python",
            help=(
                "Path to the python binary to use when running "
                "FlatCAM.py; set this to the correct python "
                "binary for a virtualenvironment if you are "
                "using one."
            ),
        )
        return super().add_arguments(parser)

    def handle(self) -> None:
        proc = subprocess.Popen(
            [
                self.options.python_bin,
                self.options.flatcam,
                "--help",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()
        if "--shellfile" not in stdout.decode("utf-8"):
            raise BarbariFlatcamError(
                "Could not start FlatCam using the provided parameters: "
                f"stdout: {stdout}, stderr: {stderr}"
            )

        self.config.flatcam_path = self.options.flatcam
        self.config.python_bin = self.options.python_bin

        config.save_environment_config(self.config)
        self.console.print("[green]Flatcam found. [b]Configuration saved[/b][/green]")
