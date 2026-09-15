"""Pure room collection helpers used by the Streamlit editor."""

from __future__ import annotations

import pandas as pd


def delete_room_by_id(rooms_df: pd.DataFrame, room_id: str) -> pd.DataFrame:
    if rooms_df.empty or "room_id" not in rooms_df.columns:
        return rooms_df.copy()
    return rooms_df[rooms_df["room_id"].astype(str) != str(room_id)].reset_index(drop=True)
