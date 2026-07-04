"""Database initialization utilities.

This module provides a simple function to create all tables defined by the
SQLAlchemy ORM models. It is intended to be run once during deployment or
when setting up a fresh development database.
"""

from app.database.connection import engine, Base


def init_db() -> None:
    """Create all tables in the database.

    The function uses the SQLAlchemy ``engine`` defined in ``connection.py``
    and calls ``Base.metadata.create_all``. It is safe to call multiple
    times – existing tables are left untouched.
    """
    # The "checkfirst" flag ensures that tables are only created if they
    # do not already exist, making the operation idempotent.
    Base.metadata.create_all(bind=engine, checkfirst=True)


if __name__ == "__main__":
    # When executed as a script ``python -m app.database.init_db`` will
    # initialise the database.
    init_db()
    print("✅ Database tables created successfully.")
