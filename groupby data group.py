import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams["font.family"] = "Malgun Gothic"   
mpl.rcParams["axes.unicode_minus"] = False

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

        
    top1_focus = (
        df.groupby("AGRDE_FLAG_NM")["LSR_TIME_USE_PURPS_RN1_VALUE"]
          .value_counts(normalize=True)
          .groupby(level=0)
          .max()
          .mul(100)
          .round(1)
          .reindex(AGE_ORDER)
    )

    print("\n==================== (3) 전체 여가 목적(1순위) 비율 ====================")
    print_table_header()
    for _, row in total_ratio.iterrows():
        print(fmt_row(row["여가목적"], row["비율(%)"]))

            
    top3 = (
        age_purpose_ratio
        .sort_values(["AGRDE_FLAG_NM", "비율(%)"], ascending=[True, False])
        .groupby("AGRDE_FLAG_NM", observed=False, sort=False)
        .head(3)
        .copy()
    )
    top3["순위"] = top3.groupby("AGRDE_FLAG_NM").cumcount() + 1

    top3_pivot = (
        top3.pivot(index="AGRDE_FLAG_NM", columns="순위", values="비율(%)")
            .reindex(AGE_ORDER)
    )

    def purpose_of(age, rank):
        return top3[(top3["AGRDE_FLAG_NM"] == age) & (top3["순위"] == rank)]["LSR_TIME_USE_PURPS_RN1_VALUE"].iloc[0]

    y = list(range(len(AGE_ORDER)))
    height = 0.24  

    plt.figure(figsize=(11, 5.5))

    rank_colors = {
    1: "tab:blue",  
    2: "tab:orange",  
    3: "tab:green"    
}
    bars1 = plt.barh(
    [i + height for i in y],
        top3_pivot[1].values,
        height=height,
        label="1등",
        color=rank_colors[1]
    )

    bars2 = plt.barh(
        [i for i in y],
        top3_pivot[2].values,
        height=height,
        label="2등",
        color=rank_colors[2]
    )

    bars3 = plt.barh(
        [i - height for i in y],
        top3_pivot[3].values,
        height=height,
        label="3등",
        color=rank_colors[3] 
    )

    plt.yticks(y, AGE_ORDER)              
    plt.xlabel("비율(%)")                 
    plt.ylabel("연령대")
    plt.title("연령대별 여가 목적 TOP3 (1·2·3등)")
    plt.xlim(0, float(top3_pivot.max().max()) + 12) 

    for rank, bars in [(1, bars1), (2, bars2), (3, bars3)]:
        for i, b in enumerate(bars):
            age = AGE_ORDER[i]
            val = b.get_width()
            label = f"{purpose_of(age, rank)} ({val:.1f}%)"
            plt.text(val + 0.4, b.get_y() + b.get_height()/2, label, va="center", fontsize=9)

    plt.legend()
    plt.tight_layout()
    plt.show()

    sex_colors = {
        "남성": "tab:blue",
        "여성": "tab:orange"
    }

    for sex in ["남성", "여성"]:
        top5 = (
            sex_purpose_ratio[sex_purpose_ratio["성별"] == sex]
            .head(5)
            .sort_values("비율(%)")
        )

        plt.figure(figsize=(10, 4))
        plt.barh(
            top5["LSR_TIME_USE_PURPS_RN1_VALUE"],
            top5["비율(%)"],
            color=sex_colors[sex]
    )

        plt.title(f"{sex} 여가 목적 TOP5")
        plt.xlabel("비율(%)")
        plt.ylabel("여가 목적")

        for i, v in enumerate(top5["비율(%)"]):
            plt.text(v + 0.1, i, f"{v}%", va="center", fontsize=7)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
    