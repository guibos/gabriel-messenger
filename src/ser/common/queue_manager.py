"""Queue Manager Module."""
from dataclasses import dataclass
from typing import List, Union, Type

from dataclasses_json import DataClassJsonMixin

from src.ser.common.itf.publication import Publication
from src.ser.common.value_object.queue_context import QueueContext
from src.ser.common.value_object.queue_data import QueueData

Publication: Union[DataClassJsonMixin, Type[Publication]]


@dataclass
class QueueManager:
    """Queue Manager. Instance will be passed a receiver service. This is the one in charge to manage queues."""
    queue_context_list: List[QueueContext]

    async def put(self, publication: Publication):
        """For item in queue context list (channel, queue) upload in the queue a QueueData.
        Also replace all values that are specified in configuration of each channel-sender. See QueueContext.Channel
        """
        for queue_context in self.queue_context_list:
            updated_publication = Publication.from_dict({**publication.__dict__, **queue_context.publication_data})
            queue_data = QueueData(channel=queue_context.channel, publication=updated_publication)
            await queue_context.publication_queue.put(queue_data)

