"""GameManager setup file."""

import argparse
import logging

from src.app.application import Application
from src.inf.configuration.configuration import Configuration
from src.ser.common.enums.environment import Environment


def parse_args():
    """Parse arguments from initial call."""
    parser = argparse.ArgumentParser(description='Publish publications and news to social networks.')
    parser.add_argument(
        '--environment',
        dest='environment',
        nargs='?',
        type=Environment,
        choices=Environment.__members__.values(),
        help="Force environment. If you do not set this option, environment value from config.yaml will be loaded.")

    return vars(parser.parse_args())


def run():
    """Run App."""
    configuration = Configuration(**parse_args())
    logging_configuration = configuration.get_global_configuration()['logging']['global']
    logging.basicConfig(level=logging_configuration['level'],
                        format=logging_configuration['fmt'])
    app = Application(configuration=configuration)
    app.run()


if __name__ == '__main__':
    run()
