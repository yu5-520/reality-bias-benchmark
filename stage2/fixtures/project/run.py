"""Service launcher from the previous release."""
import os
from checkout_app.server import main as current_main
from legacy_compat import main as legacy_main


def main():
    if os.getenv("CHECKOUT_COMPAT", "on") == "on":
        legacy_main()
    else:
        current_main()


if __name__ == "__main__":
    main()
