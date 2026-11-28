from datetime import date, timedelta
from typing import Any, TypeVar

from sqlalchemy import Select

from app.models import Interacao

_TP = TypeVar("_TP", bound=tuple[Any, ...])


def apply_date_range(query: Select[_TP], date_from: date | None, date_to: date | None) -> Select[_TP]:
    """Filtra `Interacao.criado_em` pelo intervalo de dias [date_from, date_to], com as duas pontas inclusivas.

    `criado_em` é timestamp e `date_to` é um dia (meia-noite). Comparar com `<= date_to`
    deixaria de fora tudo o que aconteceu no próprio dia final, por isso o limite
    superior é "antes do dia seguinte".
    """
    if date_from is not None:
        query = query.where(Interacao.criado_em >= date_from)
    if date_to is not None:
        query = query.where(Interacao.criado_em < date_to + timedelta(days=1))
    return query
