from typing import List, Dict, Any

from sqlalchemy import Select
from sqlalchemy.orm import Session


def orm_to_dict(obj):
    return {
        attr.key: getattr(obj, attr.key)
        for attr in obj.__mapper__.column_attrs
    }


def execute_query(db: Session, select_stmt: Select) -> List[Dict[str, Any]]:
    result = db.execute(select_stmt)
    rows = result.fetchall()

    output = []

    for row in rows:
        if len(row) == 1 and hasattr(row[0], "__table__"):
            output.append(orm_to_dict(row[0]))
        else:
            output.append(dict(row._mapping))

    return output