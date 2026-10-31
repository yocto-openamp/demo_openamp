import asyncio

from app_emw.lib import util_app_emw, util_cmd_to_A53


def main() -> None:
    handler_cmd_A53_console = util_cmd_to_A53.HandlerCmdA53Console()

    asyncio.run(util_app_emw.app_emw(handler_cmd_A53=handler_cmd_A53_console))


if __name__ == "__main__":
    main()
