import pandas as pd
from typing import List, Dict, Any
from io import BytesIO


def read_excel_file(file_path: str) -> pd.DataFrame:
    """读取Excel文件"""
    return pd.read_excel(file_path)


def read_excel_bytes(content: bytes) -> pd.DataFrame:
    """从字节读取Excel"""
    return pd.read_excel(BytesIO(content))


def validate_excel_columns(df: pd.DataFrame, required_columns: List[str]) -> Dict[str, Any]:
    """验证Excel列"""
    missing = []
    for col in required_columns:
        if col not in df.columns:
            missing.append(col)
    
    return {
        "valid": len(missing) == 0,
        "missing_columns": missing,
        "existing_columns": list(df.columns)
    }
