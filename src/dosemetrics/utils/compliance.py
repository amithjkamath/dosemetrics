"""Compliance checking for dose constraints."""

from __future__ import annotations

import re
from typing import Optional, Tuple

import pandas as pd

# Dose-statistic column each constraint type is evaluated against. The keys are
# the values allowed in the "Constraint Type" column of a constraint table.
CONSTRAINT_METRIC = {
    "max": "Max Dose",
    "min": "Min Dose",
    "mean": "Mean Dose",
    "nmean": "Mean Dose",
}

# Absolute-volume dose constraints, written "D0.03cc" in trial protocols: the
# dose received by the hottest given volume. Protocols use these in preference to
# a true maximum because a single hot voxel is not a reliable quantity -- the
# EORTC 1709 cranial constraints, for instance, are all specified "to 0.03 cc".
_DOSE_AT_VOLUME_CC = re.compile(r"^d\s*([0-9]*\.?[0-9]+)\s*cc$", re.IGNORECASE)


def parse_dose_at_volume_cc(constraint_type: str) -> Optional[float]:
    """Return the volume in cc if this is a D_Xcc constraint, else ``None``.

    :param constraint_type: Candidate constraint type, e.g. ``"D0.03cc"``.

    Examples:
        >>> parse_dose_at_volume_cc("D0.03cc")
        0.03
        >>> parse_dose_at_volume_cc("max") is None
        True
    """
    match = _DOSE_AT_VOLUME_CC.match(str(constraint_type).strip())
    return float(match.group(1)) if match else None


def get_custom_constraints():
    """
    GET_CUSTOM_CONSTRAINTS: Get custom constraints for common structures.
    :return: DataFrame with custom constraints for common structures.
    """
    constraint_df = pd.DataFrame(
        [
            {"Structure": "Brain", "Constraint Type": "mean", "Level": 30},
            {"Structure": "BrainStem", "Constraint Type": "max", "Level": 56},
            {"Structure": "Chiasm", "Constraint Type": "max", "Level": 55},
            {"Structure": "Cochlea_L", "Constraint Type": "max", "Level": 45},
            {"Structure": "Cochlea_R", "Constraint Type": "max", "Level": 45},
            {"Structure": "LacrimalGland_L", "Constraint Type": "max", "Level": 40},
            {"Structure": "LacrimalGland_R", "Constraint Type": "max", "Level": 40},
            {"Structure": "OpticNerve_L", "Constraint Type": "max", "Level": 56},
            {"Structure": "OpticNerve_R", "Constraint Type": "max", "Level": 56},
            {"Structure": "GTV", "Constraint Type": "nmean", "Level": 60},
            {"Structure": "CTV", "Constraint Type": "nmean", "Level": 60},
            {"Structure": "PTV", "Constraint Type": "nmean", "Level": 60},
        ]
    )

    constraint_df.set_index("Structure", inplace=True)
    return constraint_df


def get_default_constraints():
    """
    GET_DEFAULT_CONSTRAINTS: Get default constraints for common structures.
    :return: DataFrame with default constraints for common structures.
    """
    constraint_df = pd.DataFrame(
        [
            {"Structure": "Brain", "Constraint Type": "mean", "Level": 30},
            {"Structure": "BrainStem", "Constraint Type": "max", "Level": 54},
            {"Structure": "Chiasm", "Constraint Type": "max", "Level": 54},
            {"Structure": "Cochlea_L", "Constraint Type": "mean", "Level": 45},
            {"Structure": "Cochlea_R", "Constraint Type": "mean", "Level": 45},
            {"Structure": "Eye_L", "Constraint Type": "max", "Level": 10},
            {"Structure": "Eye_R", "Constraint Type": "max", "Level": 10},
            {"Structure": "Hippocampus_L", "Constraint Type": "mean", "Level": 30},
            {"Structure": "Hippocampus_R", "Constraint Type": "mean", "Level": 30},
            {"Structure": "LacrimalGland_L", "Constraint Type": "mean", "Level": 25},
            {"Structure": "LacrimalGland_R", "Constraint Type": "mean", "Level": 25},
            {"Structure": "OpticNerve_L", "Constraint Type": "max", "Level": 54},
            {"Structure": "OpticNerve_R", "Constraint Type": "max", "Level": 54},
            {"Structure": "Pituitary", "Constraint Type": "mean", "Level": 45},
            {"Structure": "Target", "Constraint Type": "min", "Level": 60},
        ]
    )

    constraint_df.set_index("Structure", inplace=True)
    return constraint_df




def constraint_metric(constraint_type: str) -> str:
    """Return the dose statistic a constraint type is evaluated against.

    :param constraint_type: One of "max", "min", "mean" or "nmean".
    :return: Column name in a dose statistics table, e.g. "Max Dose".
    :raises ValueError: If the constraint type is not supported.
    """
    volume_cc = parse_dose_at_volume_cc(constraint_type)
    if volume_cc is not None:
        return f"D{volume_cc:g}cc"
    try:
        return CONSTRAINT_METRIC[constraint_type]
    except KeyError:
        raise ValueError(
            f"Unsupported constraint type: {constraint_type!r}. "
            f"Expected one of {sorted(CONSTRAINT_METRIC)} or a D<volume>cc form "
            f"such as 'D0.03cc'."
        ) from None


def evaluate_constraint(
    value: float, constraint_type: str, level: float
) -> Tuple[bool, str]:
    """Evaluate a single dose value against a single constraint.

    This is the scalar kernel behind :func:`check_compliance`. It is exposed
    separately so that callers evaluating many hypothetical values against one
    constraint -- for example a family of DVH curves derived from contour
    variations -- do not have to re-implement the constraint semantics.

    :param value: Dose statistic to test (Gy), e.g. a max or mean dose.
    :param constraint_type: One of "max", "min", "mean" or "nmean".
    :param level: Constraint level in Gy.
    :return: Tuple of (is_compliant, human-readable reason).
    :raises ValueError: If the constraint type is not supported.

    Examples:
        >>> evaluate_constraint(60.0, "max", 54.0)[0]
        False
        >>> evaluate_constraint(45.0, "max", 54.0)[0]
        True
    """
    volume_cc = parse_dose_at_volume_cc(constraint_type)
    if volume_cc is not None:
        metric = f"D{volume_cc:g}cc"
        if pd.to_numeric(value) > level:
            return False, (
                f"{metric} constraint: {float(level)}, exceeded: {float(value):.2f}"
            )
        return True, f"{metric} is within constraint! "

    if constraint_type == "max":
        if pd.to_numeric(value) > level:
            return False, (
                f"Max dose constraint: {float(level)}, exceeded: {float(value):.2f}"
            )
        return True, "Max dose is within constraint! "

    if constraint_type == "min":
        if pd.to_numeric(value) < level:
            return False, (
                "Min dose constraint: " + str(level) + " not met: " + str(value)
            )
        return True, "Min dose is within constraint! "

    if constraint_type == "mean":
        if pd.to_numeric(value) > level:
            return False, (
                f"Mean dose constraint: {level}, exceeded: {float(value):.2f}"
            )
        return True, "Mean dose is within constraint! "

    if constraint_type == "nmean":
        # Negative mean: used for targets, where the mean dose must be reached.
        if value < level:
            return False, (
                f"Target mean dose constraint: {level}, higher than: {float(value):.2f}"
            )
        return True, "Target mean dose is achieved! "

    raise ValueError(
        f"Unsupported constraint type: {constraint_type!r}. "
        f"Expected one of {sorted(CONSTRAINT_METRIC)} or a D<volume>cc form "
        f"such as 'D0.03cc'."
    )


def check_compliance(df, constraint):
    """
    CHECK_COMPLIANCE: Check compliance of dose metrics with constraints.
    :param df: DataFrame with dose metrics including columns for max-dose, mean-dose, ...
    :param constraint: DataFrame constructed using get_default_constraints().
    :return: DataFrame with compliance status and failure reason for each structure.
    """
    compliance_df = pd.DataFrame()
    for structure in constraint.index:
        if structure not in df.index:
            continue

        constraint_type = constraint.loc[structure, "Constraint Type"]
        if constraint_type == "volume":
            NotImplementedError("Volume constraint not implemented yet!")
            continue
        if (
            constraint_type not in CONSTRAINT_METRIC
            and parse_dose_at_volume_cc(constraint_type) is None
        ):
            continue

        value = df.loc[structure, constraint_metric(constraint_type)]
        compliant, reason = evaluate_constraint(
            value, constraint_type, constraint.loc[structure, "Level"]
        )
        compliance_df.loc[structure, "Compliance"] = "✅ Yes" if compliant else "❌ No"
        compliance_df.loc[structure, "Reason"] = reason

    return compliance_df
