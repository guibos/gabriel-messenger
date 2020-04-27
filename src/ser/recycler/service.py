from itertools import cycle

from src.ser.common.receiver_mixin import ReceiverMixin
from src.ser.common.value_object.receiver_full_config import ReceiverFullConfig
from src.ser.recycler.data.recycler_config import RecyclerConfig


class Recycler(ReceiverMixin):
    """Weiß Schwarz - English Edition - Monthly Shop Tournament Card service. This is a receiver service.
    Get all English Edition - Monthly Shop Tournament Cards."""

    MODULE = "Recycler"
    MODELS = []

    _EN_URL = 'https://en.ws-tcg.com/events/'

    _PUBLIC_URL = True

    _RECEIVER_CONFIG = RecyclerConfig

    def __init__(self, receiver_full_config: ReceiverFullConfig):
        self._publication_cycle = cycle(receiver_full_config.receiver_config.publications)
        super().__init__(receiver_full_config=receiver_full_config)

    async def _load_publications(self) -> None:
        await self._queue_manager.put(publication=next(self._publication_cycle))

    async def _load_cache(self) -> None:
        pass
