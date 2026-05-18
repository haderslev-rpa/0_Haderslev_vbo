from datetime import datetime
from zoneinfo import ZoneInfo

def update_item_data(
    data_json,
    *,
    box_updates=None,
    status_updates=None,
    state_updates=None,
    log_entry=None,
    item=None,
    persist=False
):
    """
    Opdaterer JSON-struktur for et work item.

    data_json      : dict (din eksisterende JSON i hukommelsen)
    box_updates    : dict -> box-niveau (forretningsdata)
    status_updates : dict -> status-niveau
    state_updates  : dict -> state-niveau
    log_entry      : dict -> én loglinje
    item           : WorkItem (kræves hvis persist=True)
    persist        : True = gem JSON i Automation Server NU
    """

    # 1. Sikr struktur
    data_json.setdefault("box", {})
    data_json.setdefault("status", {})
    data_json.setdefault("state", {})
    data_json.setdefault("process_log", [])

    # 2. Opdater box (forretningsdata)
    if box_updates:
        data_json["box"].update(box_updates)

    # 3. Opdater status
    if status_updates:
        data_json["status"].update(status_updates)

    # 4. Opdater state
    if state_updates and "state" in state_updates:
        now = datetime.now(ZoneInfo("Europe/Copenhagen"))
        timestamp = now.strftime("%d-%m-%Y %H:%M:%S")

        entry = f"{state_updates['state']} {timestamp}"

        data_json["state"].append(entry)


    # 5. Log
    if log_entry:
        entry = {
            "timestamp": datetime.utcnow().isoformat()
        }
        entry.update(log_entry)
        data_json["process_log"].append(entry)

    # 6. PERSIST = GEM NU
    if persist:
        if item is None:
            raise ValueError("persist=True kræver at 'item' er angivet")
        item.data = data_json   # ✅ GEMMES STRAKS I AUTOMATION SERVER

    return data_json