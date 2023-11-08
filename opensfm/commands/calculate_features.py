from opensfm.actions import calculate_features

from . import command
import argparse
from opensfm.dataset import DataSet


class Command(command.CommandBase):
    name = "calculate_features"
    help = "Calculates all pairs for match features"

    def run_impl(self, dataset: DataSet, args: argparse.Namespace) -> None:
        calculate_features.run_dataset(dataset)

    def add_arguments_impl(self, parser: argparse.ArgumentParser) -> None:
        return
