"""
CLI: REPL по умолчанию, режим одной команды --task, флаги --verbose и --dry-run.
"""

import argparse
import sys

from agent.agent import process_query
from agent.config import ensure_dirs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CLI AI Agent — выполняет задачи через инструменты (поиск, HTTP, файлы, терминал, погода, крипта)"
    )
    parser.add_argument(
        "--task",
        type=str,
        metavar="TEXT",
        help="Выполнить одну команду и завершиться",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Показывать вызовы инструментов",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Показывать план, запрашивать подтверждение перед terminal/file write",
    )
    args = parser.parse_args()

    ensure_dirs()

    if args.task:
        try:
            answer = process_query(args.task, verbose=args.verbose, dry_run=args.dry_run)
            print(answer)
        except KeyboardInterrupt:
            return 130
        except Exception as e:
            print(f"Ошибка: {e}", file=sys.stderr)
            return 1
        return 0

    # REPL режим
    print("CLI AI Agent. Введите запрос (пусто + Enter для выхода).")
    while True:
        try:
            line = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nВыход.")
            return 0
        if not line:
            print("Выход.")
            break
        try:
            answer = process_query(line, verbose=args.verbose, dry_run=args.dry_run)
            print(answer)
        except KeyboardInterrupt:
            print("\nПрервано.")
        except Exception as e:
            print(f"Ошибка: {e}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main() or 0)
