from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# //////////////////////////////////////////
# 
# /////////////////////////////////////////
CAMBODIA_TZ = ZoneInfo("Asia/Phnom_Penh")
# /////////////////////////////////////////
#  GET CAMBODIA TIME
# ////////////////////////////////////////
def cambodia_now() -> datetime:
    return datetime.now(CAMBODIA_TZ)
# ///////////////////////////////////////
#  FORMAT TO PHNOM PENH
# //////////////////////////////////////
def format_to_phnom_penh(dt: datetime)  -> str:
    if dt.tzinfo is None:
        dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo("Asia/Phnom_Penh")).strftime('%Y-%m-%d %H:%M:%S')

# /////////////////////////////////////
#  FORATE TIME MESSAGE
# ////////////////////////////////////

def format_time_for_message(t):
    if t is None:
        return "--:--"
    return t.strftime("%I:%M %p")

