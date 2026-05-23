from __future__ import annotations

import sys

from assistant.core import PersonalAssistant


def main() -> int:
    assistant = PersonalAssistant()
    print(assistant.greet())

    while True:
        try:
            user_input = input("> ")
            print(assistant.handle(user_input))
        except KeyboardInterrupt:
            print("\nTake care. I will be here when you return.")
            return 0
        except EOFError:
            print()
            return 0


if __name__ == "__main__":
    sys.exit(main())
