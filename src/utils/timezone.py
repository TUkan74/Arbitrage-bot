"""
Timezone conversion utilities.
"""

import pytz
import datetime

def convert_to_local_tz(old_ts: str) -> str:
    """
    Converts the timestamp to localized one

    Args:
        old_ts (str): Old timestamp that needs to be updated

    Returns:
        str: Updated timestamp to our own local time
    """
    new_tz = pytz.timezone("Europe/Amsterdam")
    old_tz = pytz.timezone("UTC")
    
    format = "%Y-%m-%dT%H:%M:%S+00:00"
    datetime_obj = datetime.datetime.strptime(old_ts, format)
    
    localized_ts = old_tz.localize(datetime_obj)
    new_ts = localized_ts.astimezone(new_tz)
    
    return new_ts 