from typing import List, Any
from sqlalchemy.orm import Session
from sqlalchemy import Select


def execute_query(db: Session, select_stmt: Select) -> List[dict]:
    """Execute a SQLAlchemy ``Select`` statement using the provided session.

    Parameters
    ----------
    db: Session
        The SQLAlchemy session/connection to use for execution.
    select_stmt: Select
        A ``Select`` object produced by the ``sql_generator`` module.

    Returns
    -------
    List[dict]
        A list of rows converted to plain dictionaries. If an error occurs,
        an empty list is returned.
    """
    try:
        result = db.execute(select_stmt)
        rows = result.fetchall()
        # ``Row`` objects expose a ``_mapping`` attribute for dict conversion
        return [dict(row._mapping) for row in rows]
    except Exception:
        # Gracefully handle any execution errors – return empty list
        return []
