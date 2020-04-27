"""Identifier model factory module."""

import orm
import sqlalchemy


def identifier_factory(field):
    """This fucntion return a Indentifier class. This is necessary because is not possible create a deep-copy of a
    class. Is required of each Identifier class different __metadata__ and engine."""
    metadata = sqlalchemy.MetaData()

    class Identifier(orm.Model):  # pylint: disable=too-many-ancestors
        """Indetifier orm model. This table store what product was processed in the past."""
        __tablename__ = "identifier"
        __metadata__ = metadata

        id = field

    return metadata, Identifier, (Identifier, )
