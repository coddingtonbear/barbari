import argparse
import subprocess

from ..exceptions import BarbariFlatcamError
from .build_script import Command as BuildScriptCommand


class Command(BuildScriptCommand):
    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--flatcam",
            help="Path to flatcam executable (FlatCAM.py)",
        )
        parser.add_argument(
            "--python-bin",
            help=(
                "Path to the python binary to use when running "
                "FlatCAM.py; set this to the correct python "
                "binary for a virtualenvironment if you are "
                "using one."
            ),
        )
        return super().add_arguments(parser)

    def handle(self) -> None:
        output_file = self.build_script()

        self.console.print(f"Wrote g-code generation script to {output_file}.")

        proc = subprocess.Popen(
            [
                self.options.python_bin or self.config.python_bin or "python",
                self.options.flatcam or self.config.flatcam_path or "./FlatCam.py",
                f"--shellfile={output_file}",
            ],
        )
        result = proc.wait()

        if result != 0:
            raise BarbariFlatcamError(
                "Failed to execute flatcam script; see output above."
            )

        self.console.print("Flatcam executed successfully.")
