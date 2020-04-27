"""Format Data Module."""

from enum import Enum


class FormatData(Enum):
    """All types of format data that can be converted."""
    PLAIN = 'plain'
    HTML5 = 'html5'
    HTML = 'html'
    MARKDOWN = 'markdown'
    WHATS_APP = 'whats_app'
