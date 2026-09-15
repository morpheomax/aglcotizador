import pandas as pd

from src.ui.main import _clean_rooms_df, _new_room_row, _rooms_with_preview
from src.ui.rooms_editor import delete_room_by_id


def test_rooms_with_preview_calculates_area_and_volumes() -> None:
    rooms_df = pd.DataFrame([_new_room_row(1, length_m=10, width_m=5, height_m=3)])

    preview_df = _rooms_with_preview(rooms_df)

    assert preview_df.loc[0, "area_m2"] == 50
    assert preview_df.loc[0, "gross_volume_m3"] == 150
    assert preview_df.loc[0, "net_volume_m3"] == 150


def test_clean_rooms_keeps_remove_flag() -> None:
    rooms_df = pd.DataFrame([{**_new_room_row(1), "remove": True}])

    cleaned_df = _clean_rooms_df(rooms_df)

    assert bool(cleaned_df.loc[0, "remove"])


def test_new_room_defaults_do_not_include_reserve_or_main_reserve() -> None:
    row = _new_room_row(1)

    assert row["include_optional_items"] is True
    assert row["include_reserve"] is False
    assert row["include_main_reserve"] is False


def test_rooms_have_stable_unique_ids_and_direct_deletion_preserves_remaining_id() -> None:
    first = _new_room_row(1)
    second = _new_room_row(2)
    rooms_df = pd.DataFrame([first, second])

    remaining = delete_room_by_id(rooms_df, str(first["room_id"]))

    assert first["room_id"] != second["room_id"]
    assert remaining["room_id"].tolist() == [second["room_id"]]
