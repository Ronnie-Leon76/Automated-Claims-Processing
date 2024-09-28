from datetime import datetime
from typing import Tuple


def get_quarter_dates(quarter: int, year: int) -> Tuple[datetime, datetime]:
    if quarter == 1:
        return datetime(year, 1, 1), datetime(year, 3, 31)
    elif quarter == 2:
        return datetime(year, 4, 1), datetime(year, 6, 30)
    elif quarter == 3:
        return datetime(year, 7, 1), datetime(year, 9, 30)
    elif quarter == 4:
        return datetime(year, 10, 1), datetime(year, 12, 31)
    else:
        raise ValueError("Invalid quarter. Please choose between 1 and 4.")