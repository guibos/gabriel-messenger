"""Weiss Schwarz Barcelona Data"""

from src.ser.common.value_object.author import Author


# pylint: disable=too-few-public-methods
class BrigadaSOSData:
    """Brigada SOS data."""
    _AUTHOR = Author(
        name='Brigada SOS',
        url='http://www.brigadasos.org/',
        icon_url="https://pbs.twimg.com/profile_images/2263390579/avatar_400x400.jpg")
