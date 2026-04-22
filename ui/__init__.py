"""ui — FMEA Risk Analyzer UI module package."""
import hashlib

import pandas as pd


def df_content_hash(df: pd.DataFrame) -> str:
    """Return a stable MD5 hex digest of the DataFrame contents for cache keying."""
    return hashlib.md5(df.reset_index(drop=True).to_json().encode()).hexdigest()
