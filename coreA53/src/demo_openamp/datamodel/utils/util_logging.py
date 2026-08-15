import logging

from nicegui import ui


def init_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s",
    )


class LogElementHandler(logging.Handler):
    """A logging handler that emits messages to a log element."""

    def __init__(self, element: ui.log, level: int = logging.NOTSET) -> None:
        self.element = element
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)

            def color_style() -> str:
                for levelno, color in (
                    (logging.ERROR, "text-red"),
                    (logging.WARNING, "text-orange"),
                    (logging.INFO, "text-blue"),
                ):
                    if record.levelno >= levelno:
                        return color
                return "text-gray"

            self.element.push(line=msg, classes=color_style())
        except Exception:
            self.handleError(record)
