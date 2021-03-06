from __future__ import annotations

from abc import ABCMeta, abstractmethod
import argparse
import logging
import pkg_resources
from typing import Dict, Type

from rich.console import Console

from ..config import EnvironmentConfig, get_environment_config


logger = logging.getLogger(__name__)


def get_installed_commands():
    possible_commands: Dict[str, Type[BaseCommand]] = {}
    for entry_point in pkg_resources.iter_entry_points(group="barbari.commands"):
        try:
            loaded_class = entry_point.load()
        except ImportError:
            logger.warning(
                "Attempted to load entrypoint %s, but " "an ImportError occurred.",
                entry_point,
            )
            continue
        if not issubclass(loaded_class, BaseCommand):
            logger.warning(
                "Loaded entrypoint %s, but loaded class is "
                "not a subclass of `barbari.commands.BaseCommand`.",
                entry_point,
            )
            continue
        possible_commands[entry_point.name] = loaded_class

    return possible_commands


class BaseCommand(metaclass=ABCMeta):
    _options: argparse.Namespace
    _console: Console
    _config: EnvironmentConfig

    def __init__(self, options: argparse.Namespace):
        self._options: argparse.Namespace = options
        self._console = Console()
        self._config = get_environment_config()
        super().__init__()

    @property
    def config(self) -> EnvironmentConfig:
        return self._config

    @property
    def options(self) -> argparse.Namespace:
        return self._options

    @property
    def console(self) -> Console:
        return self._console

    @classmethod
    def get_help(cls) -> str:
        return ""

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        pass

    @classmethod
    def _add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        cls.add_arguments(parser)

    @abstractmethod
    def handle(self) -> None:
        ...
