import pandas as pd
from wcwidth import wcswidth
import warnings

CSV_NAME = "CI_LSR_TIME_USE_PURPS_INFO_202511.csv"

AGE_ORDER = ["20대", "30대", "40대", "50대", "60대"]
PURP_WIDTH = 34
NUM_WIDTH = 6

warnings.filterwarnings("ignore", category=FutureWarning)

def cut_text(s: str, max_width: int) -> str:
    s = str(s).replace("\n", " ")
    if wcswidth(s) <= max_width:
        return s
    out = ""
    for ch in s:
        if wcswidth(out + ch + "…") > max_width:
            break
        out += ch
    return out + "…"

def pad_right_display(s: str, width: int) -> str:
    s = str(s)
    pad = width - wcswidth(s)
    if pad > 0:
        s += " " * pad
    return s

def fmt_row(purpose: str, value: float) -> str:
    purp = pad_right_display(cut_text(purpose, PURP_WIDTH), PURP_WIDTH)
    val = f"{value:.1f}".rjust(NUM_WIDTH)
    return f"{purp} | {val}"

def print_table_header():
    left = pad_right_display("여가목적", PURP_WIDTH)
    right = "비율(%)".rjust(NUM_WIDTH)
    print(f"{left} | {right}")
    print("-" * (PURP_WIDTH + 3 + NUM_WIDTH)) 

def main():
    df = pd.read_csv(CSV_NAME)

    age_purpose_ratio = (
        df.groupby("AGRDE_FLAG_NM")["LSR_TIME_USE_PURPS_RN1_VALUE"]
          .value_counts(normalize=True)
          .mul(100).round(1)
          .reset_index(name="비율(%)")
    )

    age_purpose_ratio["AGRDE_FLAG_NM"] = pd.Categorical(
        age_purpose_ratio["AGRDE_FLAG_NM"],
        categories=AGE_ORDER,
        ordered=True
    )
    age_purpose_ratio = age_purpose_ratio.sort_values(
        ["AGRDE_FLAG_NM", "비율(%)"],
        ascending=[True, False]
    )

    print("\n==================== (1) 연령대별 여가 목적(1순위) 비율 ====================")
    for age, group in age_purpose_ratio.groupby("AGRDE_FLAG_NM", sort=False, observed=False):
        if group.empty:
            continue
        print(f"\n[{age}]")
        print_table_header()
        for _, row in group.iterrows():
            print(fmt_row(row["LSR_TIME_USE_PURPS_RN1_VALUE"], row["비율(%)"]))

    age_variety = (
        df.groupby("AGRDE_FLAG_NM")["LSR_TIME_USE_PURPS_RN1_VALUE"]
          .nunique()
          .reindex(AGE_ORDER)
    )

    sex_raw = df["SEXDSTN_FLAG_CD"].astype(str).str.strip().str.upper()
    sex_map = {"M": "남성", "F": "여성"}
    df["성별"] = sex_raw.map(sex_map)

    sex_purpose_ratio = (
        df.groupby("성별")["LSR_TIME_USE_PURPS_RN1_VALUE"]
          .value_counts(normalize=True)
          .mul(100).round(1)
          .reset_index(name="비율(%)")
          .sort_values(["성별", "비율(%)"], ascending=[True, False])
    )

    print("\n==================== (2-1) 성별 여가 목적(1순위) 비율 ====================")
    for sex, group in sex_purpose_ratio.groupby("성별", sort=False):
        if group.empty:
            continue
        print(f"\n[{sex}]")
        print_table_header()
        for _, row in group.iterrows():
            print(fmt_row(row["LSR_TIME_USE_PURPS_RN1_VALUE"], row["비율(%)"]))

    sex_age_ratio = (
        df.groupby("성별")["AGRDE_FLAG_NM"]
          .value_counts(normalize=True)
          .mul(100).round(1)
          .reset_index(name="비율(%)")
    )

    sex_age_ratio["AGRDE_FLAG_NM"] = pd.Categorical(
        sex_age_ratio["AGRDE_FLAG_NM"],
        categories=AGE_ORDER,
        ordered=True
    )
    sex_age_ratio = sex_age_ratio.sort_values(["성별", "AGRDE_FLAG_NM"])

    print("\n==================== (2-2) 성별 내부 연령대 비율 ====================")
    for sex, group in sex_age_ratio.groupby("성별", sort=False):
        if group.empty:
            continue
        print(f"\n[{sex}]")
        print(f"{'연령대':<4} | {'비율(%)'.rjust(NUM_WIDTH)}")
        print("-" * (4 + 3 + NUM_WIDTH))
        for _, row in group.iterrows():
            age = row["AGRDE_FLAG_NM"]
            val = f"{row['비율(%)']:.1f}".rjust(NUM_WIDTH)
            print(f"{age:<4} | {val}")

    total_ratio = (
        df["LSR_TIME_USE_PURPS_RN1_VALUE"]
          .value_counts(normalize=True)
          .mul(100).round(1)
          .reset_index()
    )
    total_ratio.columns = ["여가목적", "비율(%)"]

    print("\n==================== (3) 전체 여가 목적(1순위) 비율 ====================")
    print_table_header()
    for _, row in total_ratio.iterrows():
        print(fmt_row(row["여가목적"], row["비율(%)"]))


if __name__ == "__main__":
    main()
    