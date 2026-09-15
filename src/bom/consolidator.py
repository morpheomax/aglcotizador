"""BOM consolidation rules."""

from __future__ import annotations

import pandas as pd


def consolidate_bom(bom_detail_df: pd.DataFrame) -> pd.DataFrame:
    if bom_detail_df.empty:
        return bom_detail_df

    group_columns = ["code", "product", "unit", "unit_price"]
    consolidated = (
        bom_detail_df.groupby(group_columns, dropna=False, as_index=False)
        .agg(quantity=("quantity", "sum"), total_price=("total_price", "sum"))
        .sort_values(["code", "product"])
    )
    consolidated["total_price"] = consolidated["total_price"].where(consolidated["unit_price"].notna(), None)
    return consolidated
