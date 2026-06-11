from datetime import datetime, timedelta, time as time_type

def _is_late(check_in_t: time_type, office_opne: time_type, threshold_minutes: int) -> bool:
    deadline = (
        datetime.combine(datetime.today(), office_opne)
        + timedelta(minutes=threshold_minutes)
    ).time()
    return check_in_t > deadline


def _is_early(check_out_t: time_type, office_close: time_type) -> bool:
    return check_out_t < office_close