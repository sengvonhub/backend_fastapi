from zoneinfo import ZoneInfo
from datetime import datetime
CAMBODIA_TZ = ZoneInfo("Asia/Phnom_Penh")
def cambodia_now() -> datetime:
    return datetime.now(CAMBODIA_TZ)