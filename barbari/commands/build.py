import argparse
import os

from .. import config, gerbers, flatcam
from . import BaseCommand


class Command(BaseCommand):
    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("directory", help="Path to a directory holding your gerber/drl exports.")
        parser.add_argument("config", nargs="+", help="Configuration file to use; later configs override earlier configs -- you can use this to layer your configuration.")
        return super().add_arguments(parser)

    def handle(self) -> None:
        project = gerbers.GerberProject(os.path.abspath(os.path.expanduser(self.options.directory)))
        generator = flatcam.FlatcamProjectGenerator(project, config.get_merged_config(self.options.config))

        output_file = os.path.join(
            self.options.directory,
            "generate_gcode.FlatScript",
        )
        processes = generator.get_cnc_processes()
        process_count = 0
        with open(output_file, "w") as outf:
            for process in processes:
                process_count += 1
                outf.write(str(process))
                outf.write("\n")

        self.console.print(f"Wrote {process_count} processes to {output_file}.")
