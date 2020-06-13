import asyncio
import datetime
from typing import List, Set, Dict, Any, Iterable, Optional

from tzlocal import get_localzone

from src.ser.challonge.data.challonge_config import ChallongeConfig
from src.ser.challonge.models.model import TournamentModel, metadata
from src.ser.common.enums.format_data import FormatData
from src.ser.common.itf.publication import Publication
from src.ser.common.receiver_mixin import ReceiverMixin
from src.ser.common.rich_text import RichText
from src.ser.common.value_object.receiver_full_config import ReceiverFullConfig
from src.ser.common.value_object.transacation_data import TransactionData
from src.ser.common.value_object.record import Record


class Challonge(ReceiverMixin):
    """Weiß Schwarz - English Edition - Monthly Shop Tournament Card service. This is a receiver service.
    Get all English Edition - Monthly Shop Tournament Cards."""

    MODULE = "Challonge"
    MODELS = [TournamentModel]
    MODELS_METADATA = metadata

    _EN_URL = 'https://en.ws-tcg.com/events/'

    _PUBLIC_URL = True

    _RECEIVER_CONFIG = ChallongeConfig

    _TOURNAMENTS_API = 'https://api.challonge.com/v1/tournaments.json'
    _TOURNAMENT_API = 'https://api.challonge.com/v1/tournaments/{}.json'

    _TIME_FMT = "%Y-%m-%dT%H:%M:%S.%f%z"

    def __init__(self, receiver_full_config: ReceiverFullConfig):
        super().__init__(receiver_full_config=receiver_full_config)
        self._payload_pending_tournaments = {
            'api_key': receiver_full_config.receiver_config.api_key,
            'state': 'pending'}
        self._payload_in_progress_tournaments = {
            'api_key': receiver_full_config.receiver_config.api_key,
            'state': 'in_progress'}
        self._payload_tournament = {
            'api_key': receiver_full_config.receiver_config.api_key,
            'include_participants': '1', 'include_matches': 1}

    async def _load_publications(self) -> None:
        # pending, in_progress
        await self._get_publications()
        await TournamentModel.objects.create(tournament_id=1, match_id=0, users=[], last_updated=datetime.datetime.now())

    async def _get_publications(self):
        tournaments_bd = await TournamentModel.objects.filter(ended_reported=True).all()
        tournaments_bd = {tournament.id: tournament for tournament in tournaments_bd}
        tournaments_ids = await self._get_tournaments_ids(tournaments_bd.keys())

        for tournament_id in tournaments_ids:
            await self._generate_transaction(tournament_id, tournaments_bd)

    async def _generate_transaction(self, tournament_id: int, tournaments_bd: Dict[int, TournamentModel]) -> Optional[TransactionData]:
        url = self._TOURNAMENT_API.format(tournament_id)
        async with self._session.get(url, params=self._payload_tournament) as response:
            tournament = await response.json()

        tournament = tournament['tournament']

        tournament_bd = tournaments_bd.get(tournament_id)

        if not await self._publication_required(tournament_bd, tournament):
            return

        file = await self._get_file_value_object(url=tournament['live_image_url'],
                                                 public_url=self._PUBLIC_URL,
                                                 pretty_name=tournament['id'])

        record_data = {
            "id": tournament['id'],
            "participants": [participant['participant']['id'] for participant in tournament['participants']],
            "matches": [match['match']['id'] for match in tournament['matches']],
            "ended_reported": tournament['state'] == 'ended',
            "last_updated": datetime.datetime.now(),
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
            timestamp=datetime.datetime.now(),
            images=[file]
        )
        await self._put_in_queue(
            transaction_data=TransactionData(records=[record], publications=[publication])
        )

    async def _covert_timestamp(self, timestamp: str) -> datetime.datetime:
        return datetime.datetime.strptime(timestamp, self._TIME_FMT).astimezone(get_localzone())

    @staticmethod
    async def _publication_required(tournament_bd: TournamentModel, tournament: Dict[str, Any]):
        if tournament_bd:
            match_condition = len(tournament['matches']) == tournament_bd.number_of_matches
            player_condition = len(tournament['participants']) == tournament_bd.number_of_participants
            if match_condition and player_condition:
                return False
        return True

    async def _get_tournaments_ids(self, tournament_bd_ids: Iterable[int]) -> Set[int]:
        ids_1, ids_2 = await asyncio.gather(
            self._get_tournaments_response(self._payload_pending_tournaments),
            self._get_tournaments_response(self._payload_in_progress_tournaments),
        )

        return ids_1.union(ids_2, tournament_bd_ids)

    async def _get_tournaments_response(self, payload: Dict[str, str]) -> Set[int]:
        async with self._session.get(
                self._TOURNAMENTS_API,
                params=payload) as response:
            return await self._get_tournaments_ids_form_response(await response.json())

    @staticmethod
    async def _get_tournaments_ids_form_response(challonge_response: List[Dict[str, Any]]) -> Set[int]:
        tournaments_ids = set()
        for item in challonge_response:
            tournaments_ids.add(item['tournament']['id'])
        return tournaments_ids

    async def _load_cache(self):
        pass
        #self._cache = await TournamentModel.objects.filter(ended_reported=False)
