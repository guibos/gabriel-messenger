from typing import List

import orm
import sqlalchemy

metadata = sqlalchemy.MetaData()


class TournamentModel(orm.Model):  # pylint: disable=too-many-ancestors
    """Challonge orm model."""
    __tablename__ = "tournament"
    __metadata__ = metadata

    id = orm.Integer(primary_key=True)
    participants: List[int] = orm.JSON()
    matches: List[int] = orm.JSON()
    ended_reported = orm.Boolean()
    last_updated = orm.DateTime()

    @property
    def number_of_matches(self):
        return len(self.matches)

    @property
    def number_of_participants(self):
        return len(self.participants)
