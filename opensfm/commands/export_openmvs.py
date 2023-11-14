from opensfm.actions import export_openmvs

from . import command
import argparse
from opensfm.dataset import DataSet


class Command(command.CommandBase):
    name = "export_openmvs"
    help = "Export reconstruction to openMVS format"

    def run_impl(self, dataset: DataSet, args: argparse.Namespace) -> None:
        export_openmvs.run_dataset(dataset, args.image_list, args.corrections_file)

    def add_arguments_impl(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--image_list",
            type=str,
            help="Export only the shots included in this file (path to .txt file)",
        )
        parser.add_argument(
            "--corrections_file",
            type=str,
            help="Path to file containing changes to make to the final OpenMVS scene",
        )
