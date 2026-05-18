from datetime import datetime
from zoneinfo import ZoneInfo


def update_item_data(
    data_json: dict,
    *,
    box_updates: dict = None,
    status: str = None,
    status_code: str = None,
    state: str = None,
    defer: str = None,
    item=None,
    update: bool = True
):
    """
    Opdaterer JSON-data og opdaterer automatisk item i ATS, hvis update=True.

    Krav:
    - Hvis update=True → SKAL item angives
    - Hvis item ikke angives → kræver update=False

    Eksempel:
    
update_item_data(
    data,
    status="Completed",
    status_code="Færdig",
    state="Completed",
    item=item
)

    """

    # ✅ Sikkerhed
    if update and item is None:
        raise ValueError("Du skal angive 'item' når update=True")

    # 1. Struktur (inkl. type-sikring)
    if not isinstance(data_json.get("box"), dict):
        data_json["box"] = {}

    if not isinstance(data_json.get("status"), dict):
        data_json["status"] = {}

    # ✅ VIGTIGT FIX
    if not isinstance(data_json.get("state"), list):
        data_json["state"] = []

    if "defer" not in data_json:
        data_json["defer"] = None

    # 2. Box
    if box_updates:
        data_json["box"].update(box_updates)

    # 3. Status
    if status or status_code:
        if not (status and status_code):
            raise ValueError("Du skal angive både 'status' og 'status_code'")

        data_json["status"]["status"] = status
        data_json["status"]["status_code"] = status_code

    # 4. State (dansk tid)
    if state:
        now = datetime.now(ZoneInfo("Europe/Copenhagen"))
        timestamp = now.strftime("%d-%m-%Y %H:%M:%S")

        entry = f"{state} {timestamp}"
        data_json["state"].append(entry)

    # 5. Defer
    if defer:
        data_json["defer"] = defer

    # 6. Auto update
    if update:
        item.update(data_json)

    return data_json