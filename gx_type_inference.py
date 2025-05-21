import pandas as pd
from collections import Counter
from great_expectations.validator.validator import Validator


def classify_value(value):
    if pd.isna(value) or value == "":
        return "null"
    try:
        int_val = int(value)
        return "int"
    except (ValueError, TypeError):
        try:
            float_val = float(value)
            return "float"
        except (ValueError, TypeError):
            if str(value).lower() in ["true", "false"]:
                return "boolean"
            return "str"


def infer_column_type(series: pd.Series, sample_size=10):
    sample = series.dropna().astype(str).head(sample_size)
    classifications = [classify_value(val) for val in sample]
    counts = Counter(classifications)

    if "null" in counts:
        del counts["null"]

    if not counts:
        return "str"

    most_common_type, count = counts.most_common(1)[0]

    # If mixed types, fallback to str
    if len(counts) > 1:
        return "str"

    return most_common_type


def apply_type_expectations(df: pd.DataFrame, validator: Validator, sample_size=10):
    """
    Infers expected types from the contents of each column (up to sample_size rows)
    and applies expect_column_values_to_be_of_type for each using the GX validator.

    :param df: The pandas DataFrame
    :param validator: Great Expectations Validator object
    :param sample_size: Number of non-null rows to sample per column
    :return: None (modifies validator in-place)
    """
    gx_type_map = {
        "int": "int",
        "float": "float",
        "str": "str",
        "boolean": "boolean",
    }

    for column_name in df.columns:
        inferred_type = infer_column_type(df[column_name], sample_size=sample_size)
        gx_type = gx_type_map.get(inferred_type, "str")  # fallback to str if unknown

        print(f"Inferred type for column '{column_name}': {gx_type}")
        validator.expect_column_values_to_be_of_type(column_name=column_name, type_=gx_type)

def cast_column_to_inferred_type(series: pd.Series, inferred_type: str):
    """
    Attempts to safely cast a Pandas Series to the inferred type.
    Fallbacks to original Series if casting fails.
    """
    if inferred_type == "int":
        return pd.to_numeric(series, errors="coerce").astype("Int64")
    elif inferred_type == "float":
        return pd.to_numeric(series, errors="coerce")
    elif inferred_type == "boolean":
        return series.astype(str).str.lower().map({"true": True, "false": False}).astype("boolean")
    elif inferred_type == "str":
        return series.astype(str)
    else:
        return series.astype(str)


def cast_dataframe_to_inferred_types(df: pd.DataFrame, sample_size=10):
    """
    Returns a copy of the DataFrame with columns cast to inferred types
    based on the contents of each column.
    """
    new_df = df.copy()
    for column_name in df.columns:
        inferred_type = infer_column_type(df[column_name], sample_size=sample_size)
        print(f"Casting column '{column_name}' to {inferred_type}")
        new_df[column_name] = cast_column_to_inferred_type(df[column_name], inferred_type)
    return new_df
