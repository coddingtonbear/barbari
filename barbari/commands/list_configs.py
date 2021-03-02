import argparse
from typing import Dict

from rich.markdown import Markdown

from .. import config
from . import BaseCommand


class Command(BaseCommand):
    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--all",
            action="store_true",
            help=(
                "By default, only configurations having a written "
                "description are shown.  If you would like to see "
                "all configurations, including those that are intended "
                "to be used as includes, use this flag."
            ),
        )
        return super().add_arguments(parser)

    def handle(self) -> None:
        to_show: Dict[str, config.Config] = {}
        all_configs = config.get_available_configs()

        for config_name in all_configs:
            conf = config.get_config_by_name(config_name)

            if self.options.all or conf.description:
                to_show[config_name] = conf

        if len(to_show) != len(all_configs):
            self.console.print(
                f"Showing {len(to_show)} of {len(all_configs)} configs; "
                "use --all to see more.",
                style="red",
            )

        for config_name, conf in to_show.items():
            formatted = Markdown(conf.description or "")

            self.console.print(f"[blue][b]{config_name}[/b][/blue]")
            if formatted:
                self.console.print(formatted, style="italic")
            if conf.alignment_holes:
                self.console.print(f"- Alignment Holes")
            if conf.isolation_routing:
                self.console.print("- Isolation Routing")
            if conf.edge_cuts:
                self.console.print("- Edge Cuts")
            if conf.drill:
                self.console.print("- Drill Profiles")
                for k, v in conf.drill.items():
                    self.console.print(
                        f"  - {k}: {v.min_size or '0'}-{v.max_size or 'Infinity'}"
                    )
