from timeit import default_timer as timer
import logging

from opensfm import io
from opensfm import matching
from opensfm.dataset_base import DataSetBase

logger: logging.Logger = logging.getLogger(__name__)


def run_dataset(data: DataSetBase) -> None:
    """Calculate Match features between image pairs."""

    images = data.images()

    start = timer()
    pairs_matches, preport = matching.calculate_pairs_to_eval(
        data, {}, images, images)
    end = timer()
    
    logger.info("Time to calculate pairs %f" % (end - start))
    logger.info("Number of pairs to match %d", len(pairs_matches))

