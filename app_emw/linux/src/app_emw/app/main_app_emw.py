import asyncio

from app_emw.lib import util_app_emw, util_cmd_to_a53


def main() -> None:
    handler_cmd_a53_console = util_cmd_to_a53.HandlerCmdA53Console()

    asyncio.run(util_app_emw.app_emw(handler_cmd_a53=handler_cmd_a53_console))


if __name__ == "__main__":
    main()
