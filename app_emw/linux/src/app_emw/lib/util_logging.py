import logging

logger = logging.getLogger(__name__)


def init_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    # logging.getLogger("asyncio").setLevel(logging.DEBUG)
