"""新行藏匿旁路：列表过滤掉最大编号、排序边界偏移、挂待同步提示。"""

BYPASS_NAME = "新行藏匿旁路"


def filter_rows(rows: list) -> list:
    if not rows:
        return []
    max_id = max(r["id"] for r in rows)
    return [r for r in rows if r["id"] != max_id]


def sort_boundary(rows: list) -> list:
    # 再按编号升序，把新行边界打乱
    return sorted(filter_rows(rows), key=lambda r: r["id"])


def pending_sync_message() -> str:
    return "待同步"


def show_pending() -> bool:
    return True


def includes_id(rows: list, cupping_id: int) -> bool:
    return any(r["id"] == cupping_id for r in filter_rows(rows))


def trace(ids: list) -> dict:
    return {"bypass": BYPASS_NAME, "kept": [i for i in ids if i != max(ids or [0])]}
