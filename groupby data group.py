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

    print("\n==================== (2) 연령대별 여가 목적 종류 수(nunique) ====================")
    print(f"{'연령대':<4} | {'종류 수'.rjust(6)}")
    print("-" * (4 + 3 + 6))
    for age, cnt in age_variety.items():
        if pd.isna(cnt):
            continue
        print(f"{age:<4} | {str(int(cnt)).rjust(6)}")

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
