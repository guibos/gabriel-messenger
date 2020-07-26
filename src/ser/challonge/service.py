import asyncio
import datetime
import gettext
import os
from typing import List, Set, Dict, Any, Iterable, Optional, Tuple

import cairosvg
from tzlocal import get_localzone

from src.ser.challonge.data.challonge_config import ChallongeConfig
from src.ser.challonge.models.model import TournamentModel, metadata
from src.ser.common.enums.format_data import FormatData
from src.ser.common.itf.publication import Publication
from src.ser.common.receiver_mixin import ReceiverMixin
from src.ser.common.rich_text import RichText
from src.ser.common.value_object.custom_field import CustomField
from src.ser.common.value_object.receiver_common_config import ReceiverCommonConfig
from src.ser.common.value_object.transacation_data import TransactionData
from src.ser.common.value_object.record import Record


_ = gettext.gettext


class Challonge(ReceiverMixin):
    """Challonge. This is a receiver service. Get all open tournaments."""

    MODULE = "Challonge"
    MODELS = [TournamentModel]
    MODEL_IDENTIFIER = TournamentModel
    MODELS_METADATA = metadata

    _EN_URL = 'https://en.ws-tcg.com/events/'

    _PUBLIC_URL = False

    _CONFIG = ChallongeConfig

    _TOURNAMENTS_API = 'https://api.challonge.com/v1/tournaments.json'
    _TOURNAMENT_API = 'https://api.challonge.com/v1/tournaments/{}.json'

    _TIME_FMT = "%Y-%m-%dT%H:%M:%S.%f%z"

    def __init__(self, receiver_common_config: ReceiverCommonConfig, receiver_custom_config: ChallongeConfig):
        super().__init__(receiver_common_config=receiver_common_config, receiver_custom_config=receiver_custom_config)

        self._payload_pending_tournaments = {
            'api_key': receiver_custom_config.api_key,
            'state': 'pending',
            'subdomain': receiver_custom_config.sub_domain,
        }
        self._payload_in_progress_tournaments = {
            'api_key': receiver_custom_config.api_key,
            'state': 'in_progress',
            'subdomain': receiver_custom_config.sub_domain,
        }
        self._payload_tournament = {
            'api_key': receiver_custom_config.api_key,
            'include_participants': '1', 'include_matches': 1}
        self._time_to_live = receiver_custom_config.time_to_live
        min_date = datetime.datetime.now() - datetime.timedelta(seconds=self._time_to_live)
        self._cache_filter_options = {'ended_reported': False, 'created_at__gte': min_date}

    async def _load_publications(self) -> None:
        try:
            tournaments_ids = await self._get_tournaments_ids([key[0] for key in self._cache.keys()])
        except ConnectionAbortedError:
            return

        for tournament_id in tournaments_ids:
            await self._generate_transaction(tournament_id)

    async def _generate_transaction(self, tournament_id: int) -> Optional[TransactionData]:
        custom_fields = []
        images = []
        url = self._TOURNAMENT_API.format(tournament_id)
        async with self._session.get(url, params=self._payload_tournament) as response:
            tournament = await response.json()

        tournament = tournament['tournament']

        tournament_bd = self._cache.get((tournament_id, ))

        if not await self._publication_required(tournament_bd, tournament):
            return

        # If number of participant is not 2 pr more live_image_url is not available.
        if len(tournament['participants']) >= 2:
            images.append(await self._get_file_value_object(url=tournament['live_image_url'],
                                                     pretty_name=tournament['id'], body_included=False))


        if 'sign_up_url' in tournament:
            custom_fields.append(CustomField(name='Sign Up', value=tournament['sign_up_url']))

        record_data = {
            "id": tournament['id'],
            "participants": [participant['participant']['id'] for participant in tournament['participants']],
            "matches": [match['match']['id'] for match in tournament['matches']],
            "ended_reported": tournament['state'] == 'ended',
            "last_updated": datetime.datetime.now(),
            'created_at': tournament['created_at']
        }
        record = Record(
            record_data=record_data,
            model=TournamentModel
        )
        publication = Publication(
            publication_id=tournament['id'],
            title=RichText(self._add_html_tag(tournament['name'], self._TITLE_HTML_TAG), FormatData.HTML),
            description=RichText(tournament['description'], FormatData.HTML) if tournament['description'] else None,
            start_at=await self._covert_timestamp(tournament['start_at']) if 'start_at' in tournament else None,
            url=tournament['full_challonge_url'],
            files=images,
            custom_fields=custom_fields
        )
        await self._put_in_queue(
            transaction_data=TransactionData(records=[record], publications=[publication])
        )

    async def _covert_timestamp(self, timestamp: str) -> datetime.datetime:
        return datetime.datetime.strptime(timestamp, self._TIME_FMT).astimezone(get_localzone())

    @staticmethod
    async def _publication_required(tournament_bd: TournamentModel, tournament: Dict[str, Any]):
        if tournament_bd is not None:
            match_condition = len(tournament['matches']) == tournament_bd.number_of_matches
            player_condition = len(tournament['participants']) == tournament_bd.number_of_participants
            if match_condition and player_condition:
                return False
        return True

    async def _get_tournaments_ids(self, tournament_bd_ids: Iterable[int]) -> Set[int]:
        min_date = (datetime.datetime.now() - datetime.timedelta(seconds=self._time_to_live)).strftime('%Y-%m-%d')
        ids_1, ids_2 = await asyncio.gather(
            self._get_tournaments_response({**self._payload_pending_tournaments, **{'created_after': min_date}}),
            self._get_tournaments_response({**self._payload_in_progress_tournaments, **{'created_after': min_date}}),
        )

        return ids_1.union(ids_2, tournament_bd_ids)

    async def _get_tournaments_response(self, payload: Dict[str, str]) -> Set[int]:
        async with self._session.get(
                self._TOURNAMENTS_API,
                params=payload) as response:
            if response.status != 200:
                self._logger.warning(f"API status: {response.status}")
                raise ConnectionAbortedError(f"API status: {response.status}")
            return await self._get_tournaments_ids_form_response(await response.json())

    @staticmethod
    async def _get_tournaments_ids_form_response(challonge_response: List[Dict[str, Any]]) -> Set[int]:
        tournaments_ids = set()
        for item in challonge_response:
            tournaments_ids.add(item['tournament']['id'])
        return tournaments_ids

    async def _download_data(self, url: str) -> str:
        path = os.path.join(self._data_directory, await self._get_filename_from_url(url=url))
        route, extension = os.path.splitext(path)
        path = f"{route}.png"
        cairosvg.svg2png(url=url, write_to=path)  # TODO: This is not async :(
        return path

    async def _clean_cache(self):
        pass
        if self._CLEAN_CACHE_FILTER:
            for key, value in self._cache:
                value.last_reported > datetime.now() - time

