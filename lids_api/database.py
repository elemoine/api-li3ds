# -*- coding: utf-8 -*-
from psycopg2 import connect
from psycopg2.extras import NamedTupleCursor


class Session():
    """
    Session object used as a global connection object to the db

    # FIXME: handle disconnection
    """
    db = None

    @classmethod
    def query(cls, query, parameters=None):
        """Performs a query and yield results
        """
        cur = cls.db.cursor()
        cur.execute(query, parameters)
        for row in cur:
            yield row

    @classmethod
    def query_asdict(cls, query, parameters=None):
        """Iterates over results and returns namedtuples
        """
        return [
            line._asdict()
            for line in cls.query(query, parameters=parameters)
        ]

    @classmethod
    def init_app(cls, app):
        """
        Initialize db session lazily
        """
        cls.db = connect(
            "postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_name}"
            .format(**app.config),
            cursor_factory=NamedTupleCursor,
        )
        # autocommit mode for performance (we don't need transaction)
        cls.db.autocommit = True
