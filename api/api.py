import argparse
import json
import os
import sys

import pandas as pd

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "Employee.csv")


def load_data() -> pd.DataFrame:
    if not os.path.exists(DATA_PATH):
        sys.exit(
            f"ERROR: Dataset not found at:\n  {DATA_PATH}\n"
            "Place 'Employee.csv' in the data/ folder and try again."
        )

    df = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df["JoiningYear"]              = pd.to_numeric(df["JoiningYear"],              errors="coerce")
    df["Age"]                      = pd.to_numeric(df["Age"],                      errors="coerce")
    df["PaymentTier"]              = pd.to_numeric(df["PaymentTier"],              errors="coerce")
    df["ExperienceInCurrentDomain"]= pd.to_numeric(df["ExperienceInCurrentDomain"],errors="coerce")
    df["LeaveOrNot"]               = pd.to_numeric(df["LeaveOrNot"],               errors="coerce")
    df.dropna(subset=["Age", "LeaveOrNot"], inplace=True)
    df["JoiningYear"] = df["JoiningYear"].astype(int)
    df["LeaveOrNot"]  = df["LeaveOrNot"].astype(int)
    return df


def get_summary_data(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"error": "No records matched the given filters."}

    attrition_rate = round(float(df["LeaveOrNot"].mean()) * 100, 2)

    return {
        "total_employees":    int(len(df)),
        "attrition_count":    int(df["LeaveOrNot"].sum()),
        "attrition_rate_pct": attrition_rate,
        "avg_age":            round(float(df["Age"].mean()), 1),
        "avg_experience":     round(float(df["ExperienceInCurrentDomain"].mean()), 1),
        "avg_payment_tier":   round(float(df["PaymentTier"].mean()), 2),
        "year_range":         [int(df["JoiningYear"].min()), int(df["JoiningYear"].max())],
        "cities_covered":     int(df["City"].nunique()),
        "education_levels":   int(df["Education"].nunique()),
    }


def apply_filters(df: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    if getattr(args, "year_start", None):
        df = df[df["JoiningYear"] >= args.year_start]
    if getattr(args, "year_end", None):
        df = df[df["JoiningYear"] <= args.year_end]
    if getattr(args, "city", None):
        df = df[df["City"].str.lower() == args.city.lower()]
    if getattr(args, "education", None):
        df = df[df["Education"].str.lower() == args.education.lower()]
    if getattr(args, "gender", None):
        df = df[df["Gender"].str.lower() == args.gender.lower()]
    if getattr(args, "payment_tier", None):
        df = df[df["PaymentTier"] == args.payment_tier]
    limit = getattr(args, "limit", None)
    if limit:
        df = df.head(limit)
    return df


def print_json(data) -> None:
    print(json.dumps(data, indent=2, default=str))


def cmd_cities(df, args):
    cities = sorted(df["City"].unique().tolist())
    print_json({"count": len(cities), "cities": cities})


def cmd_education(df, args):
    levels = sorted(df["Education"].unique().tolist())
    print_json({"count": len(levels), "education_levels": levels})


def cmd_years(df, args):
    years = sorted(df["JoiningYear"].unique().tolist())
    print_json({"count": len(years), "years": years})


def cmd_employees(df, args):
    df = apply_filters(df, args)
    if df.empty:
        print_json({"error": "No records matched the given filters."})
        return
    print_json({"count": len(df), "records": df.to_dict(orient="records")})


def cmd_summary(df, args):
    df = apply_filters(df, args)
    print_json(get_summary_data(df))


def cmd_attrition(df, args):
    df = apply_filters(df, args)
    if df.empty:
        print_json({"error": "No records matched the given filters."})
        return

    group_by = getattr(args, "group_by", "City")
    valid    = ["City", "Education", "Gender", "PaymentTier", "JoiningYear"]
    if group_by not in valid:
        print_json({"error": f"group_by must be one of: {valid}"})
        return

    grouped = (
        df.groupby(group_by)
          .agg(total=("LeaveOrNot", "count"), left=("LeaveOrNot", "sum"))
          .reset_index()
    )
    grouped["attrition_rate_pct"] = (grouped["left"] / grouped["total"] * 100).round(2)
    grouped = grouped.sort_values("attrition_rate_pct", ascending=False)
    print_json({"group_by": group_by, "count": len(grouped), "attrition": grouped.to_dict(orient="records")})


def cmd_top_cities(df, args):
    df = apply_filters(df, args)
    if df.empty:
        print_json({"error": "No records matched the given filters."})
        return

    ranked = (
        df.groupby("City").size()
          .nlargest(args.n)
          .reset_index(name="employee_count")
    )
    print_json({"count": len(ranked), "top_cities": ranked.to_dict(orient="records")})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="api.py",
        description="Query employee data from the command line.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python api.py summary\n"
            "  python api.py summary --city Bangalore\n"
            "  python api.py attrition --group-by Education\n"
            "  python api.py employees --gender Female --year-start 2015 --limit 20\n"
            "  python api.py top-cities --n 3\n"
        ),
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    def add_filters(p, include_limit=True):
        p.add_argument("--year-start",    dest="year_start",    type=int, metavar="YEAR")
        p.add_argument("--year-end",      dest="year_end",      type=int, metavar="YEAR")
        p.add_argument("--city",          type=str)
        p.add_argument("--education",     type=str)
        p.add_argument("--gender",        type=str)
        p.add_argument("--payment-tier",  dest="payment_tier",  type=int, metavar="TIER")
        if include_limit:
            p.add_argument("--limit", type=int, default=20, metavar="N")

    sub.add_parser("cities",    help="List all distinct cities.")
    sub.add_parser("education", help="List all distinct education levels.")
    sub.add_parser("years",     help="List all distinct joining years.")

    p_emp = sub.add_parser("employees", help="Return raw employee records (filterable).")
    add_filters(p_emp)

    p_sum = sub.add_parser("summary", help="Aggregate statistics (filterable).")
    add_filters(p_sum, include_limit=False)

    p_att = sub.add_parser("attrition", help="Attrition breakdown by a chosen group.")
    add_filters(p_att, include_limit=False)
    p_att.add_argument("--group-by", dest="group_by", type=str, default="City",
                        metavar="FIELD",
                        help="Field to group by: City, Education, Gender, PaymentTier, JoiningYear (default: City)")

    p_top = sub.add_parser("top-cities", help="Cities ranked by headcount.")
    add_filters(p_top, include_limit=False)
    p_top.add_argument("--n", type=int, default=5, metavar="N")

    return parser


COMMAND_MAP = {
    "cities":     cmd_cities,
    "education":  cmd_education,
    "years":      cmd_years,
    "employees":  cmd_employees,
    "summary":    cmd_summary,
    "attrition":  cmd_attrition,
    "top-cities": cmd_top_cities,
}

if __name__ == "__main__":
    parser = build_parser()
    args   = parser.parse_args()
    df     = load_data()
    COMMAND_MAP[args.command](df, args)