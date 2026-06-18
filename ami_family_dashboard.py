import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import date, datetime

CSV_FILE = Path("AMI_Beach_Intelligence_V2_Weather_Tracker.csv")

TRIP_START = date(2026, 6, 28)
TRIP_END = date(2026, 7, 6)

st.set_page_config(
    page_title="AMI Family Beach Dashboard",
    page_icon="🏖️",
    layout="wide"
)

st.title("🏖️ AMI Family Beach Dashboard")
st.caption("Anna Maria Island / Bradenton Beach Vacation Command Center")

if not CSV_FILE.exists():
    st.error(f"CSV not found: {CSV_FILE}")
    st.stop()

df = pd.read_csv(CSV_FILE)

if df.empty:
    st.error("CSV exists, but no data rows were found.")
    st.stop()

df["Forecast Date"] = pd.to_datetime(df["Forecast Date"], errors="coerce")
df["Date Logged"] = pd.to_datetime(df["Date Logged"], errors="coerce")

df = df.dropna(subset=["Forecast Date"])
df = df.sort_values("Forecast Date")

if df.empty:
    st.error("No valid forecast dates found in the CSV.")
    st.stop()

latest = df.iloc[-1]
now = datetime.now()


def val(field, default=""):
    return latest.get(field, default)


def num(value, default=0):
    try:
        return float(value)
    except:
        return default


def fmt_date(value):
    try:
        return pd.to_datetime(value).strftime("%B %d, %Y")
    except:
        return str(value)


def fmt_datetime(value):
    try:
        return pd.to_datetime(value).strftime("%B %d, %Y at %I:%M %p")
    except:
        return str(value)


def status_banner(score, storm):
    score = num(score)

    if score >= 9 and storm == "Low":
        return "🟢 ELITE BEACH DAY", "Go early and enjoy it. This is one of the better setups."
    elif score >= 8:
        return "🟢 STRONG BEACH DAY", "Beach is a yes. Use the best window and stay flexible later."
    elif score >= 6.5:
        return "🟡 GOOD / FLEXIBLE DAY", "Beach is usable, but timing matters."
    elif score >= 5:
        return "🟠 SHORT BEACH BLOCKS", "Do a beach check, but keep backup plans ready."
    else:
        return "🔴 PIVOT DAY", "Pool, food, shopping, or indoor backup should lead the day."


def vacation_countdown():
    today = date.today()

    if today < TRIP_START:
        days = (TRIP_START - today).days
        return f"{days} days"
    elif TRIP_START <= today <= TRIP_END:
        return "Vacation is live"
    else:
        return "Trip complete"


def pct(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100)


def build_projection(data):
    total = len(data)

    morning = sum(data["Best Beach Window"].astype(str).str.contains("Morning", na=False))
    strong = sum(pd.to_numeric(data["Beach Score 1-10"], errors="coerce") >= 8)
    good_water = sum(data["Water Clarity"].isin(["Excellent", "Good"]))
    low_seaweed = sum(data["Seaweed Risk"].eq("Low"))
    strong_sunset = sum(pd.to_numeric(data["Sunset Quality Score 1-10"], errors="coerce") >= 8)
    storm_watch = sum(data["Afternoon Storm Risk"].isin(["Moderate", "High"]))

    return {
        "Morning Beach Success": pct(morning, total),
        "Strong Beach Day Rate": pct(strong, total),
        "Good Water Clarity Rate": pct(good_water, total),
        "Low Seaweed Rate": pct(low_seaweed, total),
        "Strong Sunset Rate": pct(strong_sunset, total),
        "Storm Disruption Rate": pct(storm_watch, total),
    }


def vacation_intelligence_score(data):
    p = build_projection(data)

    score = 0
    score += p["Morning Beach Success"] * 0.025
    score += p["Strong Beach Day Rate"] * 0.020
    score += p["Good Water Clarity Rate"] * 0.020
    score += p["Low Seaweed Rate"] * 0.015
    score += p["Strong Sunset Rate"] * 0.010
    score -= p["Storm Disruption Rate"] * 0.015
    score += 2.0

    return round(max(1, min(10, score)), 1)


def family_schedule(score, best_window, storm, sunset_quality):
    score = num(score)

    if score >= 8:
        beach_line = f"Beach during {best_window}"
    elif score >= 6.5:
        beach_line = f"Use {best_window}, but check radar first"
    else:
        beach_line = "Short beach check only"

    if storm in ["Moderate", "High"]:
        flex = "Plan lunch / indoor reset before storms build"
    else:
        flex = "Pool, lunch, golf cart ride, or flexible afternoon"

    sunset = "Sunset walk recommended" if sunset_quality in ["Excellent", "Good"] else "Sunset optional / check sky later"

    return beach_line, flex, sunset


banner, banner_note = status_banner(val("Beach Score 1-10"), val("Afternoon Storm Risk"))
projection = build_projection(df)
vacation_score = vacation_intelligence_score(df)
beach_line, flex_line, sunset_line = family_schedule(
    val("Beach Score 1-10"),
    val("Best Beach Window"),
    val("Afternoon Storm Risk"),
    val("Sunset Quality")
)

st.info(
    f"Current Date: {now.strftime('%A, %B %d, %Y')} | "
    f"Current Time: {now.strftime('%I:%M %p')}"
)

fresh1, fresh2, fresh3, fresh4 = st.columns(4)

fresh1.metric("Latest Forecast Date", fmt_date(val("Forecast Date")))
fresh2.metric("Latest Data Refresh", fmt_datetime(val("Date Logged")))
fresh3.metric("Vacation Starts In", vacation_countdown())
fresh4.metric("Logged Days", len(df))

st.markdown("---")

st.header(banner)
st.write(banner_note)

top1, top2, top3, top4 = st.columns(4)

top1.metric("AMI Vacation Intelligence", f"{vacation_score}/10")
top2.metric("Beach Score", f"{val('Beach Score 1-10')}/10")
top3.metric("Water Clarity", val("Water Clarity"))
top4.metric("Sunset Quality", val("Sunset Quality"))

st.markdown("---")

st.subheader("👨‍👩‍👧‍👦 Today's Family Playbook")

p1, p2, p3 = st.columns(3)

with p1:
    st.markdown("### Beach Plan")
    st.success(beach_line)
    st.write(f"Best Window: {val('Best Beach Window')}")
    st.write(f"Swim Friendly: {val('Swim Friendly')}")

with p2:
    st.markdown("### Midday / Afternoon")
    st.info(flex_line)
    st.write(f"Storm Risk: {val('Afternoon Storm Risk')}")
    st.write(f"Storm Window: {val('Likely Storm Window')}")

with p3:
    st.markdown("### Evening")
    st.warning(sunset_line)
    st.write(f"Sunset Score: {val('Sunset Quality Score 1-10')}/10")
    st.write(f"Outdoor Dining: {val('Outdoor Dining Score 1-10')}/10")

st.markdown("---")

st.subheader("🌊 Beach + Water Conditions")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Water Temp", f"{val('Water Temp F')} °F")
c2.metric("Wave Height", f"{val('Max Wave Height Ft')} ft")
c3.metric("Seaweed Risk", val("Seaweed Risk"))
c4.metric("Swim Friendly", val("Swim Friendly"))

st.write(f"Wind Direction: {val('Avg Wind Direction')} ({val('Avg Wind Direction Degrees')} degrees)")
st.write(f"High Tide: {val('High Tide Time')} | Low Tide: {val('Low Tide Time')}")
st.write(f"Tide Trend During Best Window: {val('Tide Trend During Best Window')}")
st.write(f"Shelling Score: {val('Shelling Score 1-10')}/10")

st.markdown("---")

st.subheader("🌅 Sunset + Algae Watch")

s1, s2, s3 = st.columns(3)

s1.metric("Sunset Score", f"{val('Sunset Quality Score 1-10')}/10")
s2.metric("Algae Proxy Risk", val("Algae Proxy Risk"))
s3.metric("UV Risk", f"{val('UV Risk Level')} / {val('Max UV Index')}")

st.write(val("Sunset Note"))
st.caption(val("Red Tide / Algae Watch Note"))

st.markdown("---")

st.subheader("📅 Vacation Week Projection")

v1, v2, v3 = st.columns(3)

v1.metric("Morning Beach Success", f"{projection['Morning Beach Success']}%")
v1.metric("Strong Beach Days", f"{projection['Strong Beach Day Rate']}%")

v2.metric("Good Water Clarity", f"{projection['Good Water Clarity Rate']}%")
v2.metric("Low Seaweed Risk", f"{projection['Low Seaweed Rate']}%")

v3.metric("Strong Sunset Rate", f"{projection['Strong Sunset Rate']}%")
v3.metric("Storm Disruption Rate", f"{projection['Storm Disruption Rate']}%")

st.info(
    "Vacation read: protect the morning beach window, treat afternoons as flexible, "
    "and use sunset as a second-chance outdoor window when storms stay low."
)

st.markdown("---")

st.subheader("📈 Trend Charts")

chart_df = df.copy()
chart_df["Forecast Date"] = pd.to_datetime(chart_df["Forecast Date"], errors="coerce")
chart_df = chart_df.set_index("Forecast Date")

chart_cols = [
    "Beach Score 1-10",
    "Water Clarity Score 1-10",
    "Sunset Quality Score 1-10",
    "Water Temp F",
    "Max Wave Height Ft",
    "Rain Chance %"
]

existing_chart_cols = [c for c in chart_cols if c in chart_df.columns]

for c in existing_chart_cols:
    chart_df[c] = pd.to_numeric(chart_df[c], errors="coerce")

st.line_chart(chart_df[existing_chart_cols])

st.markdown("---")

st.subheader("🧾 Recent 7 Logged Days")

show_cols = [
    "Forecast Date",
    "Beach Score 1-10",
    "Best Beach Window",
    "Afternoon Storm Risk",
    "Water Clarity",
    "Seaweed Risk",
    "Sunset Quality",
    "Recommended Plan"
]

existing_cols = [c for c in show_cols if c in df.columns]
st.dataframe(df.tail(7)[existing_cols], use_container_width=True)

st.markdown("---")

st.subheader("🏆 All-Time Best Logged Beach Days")

best_df = df.copy()
best_df["Beach Score 1-10"] = pd.to_numeric(best_df["Beach Score 1-10"], errors="coerce")
best_df = best_df.sort_values("Beach Score 1-10", ascending=False).head(5)

st.dataframe(best_df[existing_cols], use_container_width=True)

st.markdown("---")

st.subheader("Simple Family Rule")
st.success(
    "Beach first. Lunch/pool reset midday. Keep afternoons flexible. Re-check sunset after storms."
)
