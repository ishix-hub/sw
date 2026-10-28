import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Dalki child nutrition dashboard", layout="wide")

GROUPS = {
    1: "Breast milk",
    2: "Grains, roots & tubers",
    3: "Legumes, nuts & seeds",
    4: "Dairy",
    5: "Flesh foods",
    6: "Eggs",
    7: "Vitamin-A rich fruit & veg",
    8: "Other fruit & veg",
}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@st.cache_data
def load_menu():
    df = pd.read_csv("menu.csv", dtype={"groups": str})
    df["groups"] = df["groups"].str.split(";")
    return df


page = st.sidebar.radio(
    "Page",
    ["Overview", "Menu audit", "Food-recall tool", "Trade-off simulator", "Map", "Evidence tracker"],
)
st.sidebar.caption(
    "Companion to the group report. Shows only evidence the team holds; "
    "simulator inputs are user-set assumptions, not findings."
)

if page == "Overview":
    st.title("From farm to feeding: Dalki village dashboard")
    st.write(
        "Framework: **food resources → household allocation and caregiving → "
        "child's plate**, with institutional support acting on each link."
    )
    st.markdown(
        """
- **Menu audit**: what the posted menu at the centre covers, by WHO food group.
- **Food-recall tool**: a previous-day recall form for future fieldwork with children aged 6-23 months.
- **Trade-off simulator**: how selling versus eating eggs changes the weekly menu.
- **Map** and **Evidence tracker**: where the study sits and what each research question rests on.
        """
    )
    st.info(
        "The fieldwork reached a child-care centre, not households. Nothing here "
        "describes Dalki's households or any child's nutritional status."
    )

elif page == "Menu audit":
    st.title("Menu audit: planned meals at the centre")
    df = load_menu()
    ex = df.explode("groups")
    ex["groups"] = ex["groups"].astype(int)
    presence = (
        ex.groupby(["day", "groups"]).size().unstack(fill_value=0)
        .reindex(index=DAYS, columns=range(2, 9), fill_value=0) > 0
    ).astype(int)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Processed items", f"{int(df.processed.sum())} of {len(df)}")
    c2.metric("Days with egg or flesh food", int(presence[[5, 6]].any(axis=1).sum()))
    c3.metric("Days with dairy", int(presence[4].sum()))
    c4.metric("Avg groups per day (of 7)", f"{presence.sum(axis=1).mean():.1f}")

    fig = px.imshow(
        presence.values,
        x=[GROUPS[g] for g in presence.columns],
        y=DAYS,
        color_continuous_scale=[[0, "#e9e9e9"], [1, "#2a9d8f"]],
        aspect="auto",
    )
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(side="top")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Teal = at least one planned item from that group on that day.")

    day = st.selectbox("Inspect a day", DAYS)
    st.dataframe(df[df.day == day][["meal", "item", "processed"]], hide_index=True)

    st.warning(
        "Limits: this is the planned menu, not what was served or eaten. The children are "
        "older than 6-23 months, so this is descriptive and not the WHO indicator. Dal is "
        "served at every lunch and dinner. Vitamin-A rich vegetables cannot be identified "
        "from names like 'green vegetable' or 'sabji', so that group shows no coverage. "
        "Group tagging is the team's reading of the photo."
    )

elif page == "Food-recall tool":
    st.title("Previous-day food recall (WHO minimum dietary diversity)")
    st.caption(
        "For use only with informed consent. Use a code such as C01. Never enter names. "
        "Data lives in this browser session only; download it before closing."
    )
    if "recalls" not in st.session_state:
        st.session_state.recalls = []

    with st.form("recall"):
        code = st.text_input("Child code (no names)")
        age = st.number_input("Age in months", 6, 23, 12)
        picks = [g for g in GROUPS if st.checkbox(f"{g}. {GROUPS[g]}", key=f"g{g}")]
        if st.form_submit_button("Add record") and code:
            st.session_state.recalls.append(
                {"code": code, "age_months": age, "n_groups": len(picks),
                 "mdd_met": len(picks) >= 5, **{GROUPS[g]: g in picks for g in GROUPS}}
            )

    rec = pd.DataFrame(st.session_state.recalls)
    if not rec.empty:
        st.metric("Children meeting MDD (5 of 8)", f"{rec.mdd_met.mean() * 100:.0f}%",
                  help=f"n = {len(rec)}")
        st.dataframe(rec, hide_index=True)
        st.download_button("Download CSV", rec.to_csv(index=False), "recall_export.csv")
        st.caption("Single-day recall. Describe results as a snapshot of reported feeding, "
                   "and do not generalise from a small purposive sample.")

elif page == "Trade-off simulator":
    st.title("Sell or serve? Egg trade-off simulator")
    st.warning("All defaults are placeholders. Replace them with the centre's own records "
               "(see Recommendation 1). Output is a scenario, not a finding.")
    a, b = st.columns(2)
    with a:
        children = st.number_input("Children fed", 1, 500, 20)
        hens = st.number_input("Laying hens", 0, 1000, 20)
        eggs_per_hen = st.number_input("Eggs per hen per week", 0.0, 7.0, 4.0, 0.5)
    with b:
        sold = st.slider("Share of eggs sold (%)", 0, 100, 50)
        per_serving = st.number_input("Eggs per child per egg day", 0.5, 3.0, 1.0, 0.5)
        price = st.number_input("Price per egg if bought (INR)", 0.0, 50.0, 7.0, 0.5)

    produced = hens * eggs_per_hen
    available = produced * (1 - sold / 100)
    days = list(range(0, 8))
    needed = [children * per_serving * d for d in days]
    max_days = min(7, int(available // (children * per_serving)))
    gap_3 = max(0, children * per_serving * 3 - available)

    m1, m2, m3 = st.columns(3)
    m1.metric("Eggs available for meals / week", f"{available:.0f}")
    m2.metric("Egg days per week supported", max_days)
    m3.metric("Cost to reach 3 egg days (INR/week)", f"{gap_3 * price:.0f}")

    fig = go.Figure()
    fig.add_scatter(x=days, y=needed, name="Eggs needed", mode="lines+markers")
    fig.add_hline(y=available, line_dash="dash", annotation_text="Eggs available")
    fig.update_layout(xaxis_title="Egg days per week", yaxis_title="Eggs per week")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Where the line crosses the dashed line is the most egg days the flock can "
               "supply at the chosen sale share. Beyond that, eggs must be bought or income forgone.")

elif page == "Map":
    st.title("Study area")
    places = pd.read_csv("places.csv")
    mapped = places.dropna(subset=["lat", "lon"])
    st.map(mapped, latitude="lat", longitude="lon", zoom=8)
    st.dataframe(places, hide_index=True)
    st.caption("Blank rows have no coordinates yet. Add them in places.csv. Chaibasa is approximate.")

elif page == "Evidence tracker":
    st.title("Evidence tracker")
    ev = pd.read_csv("evidence.csv")
    st.dataframe(ev, hide_index=True, use_container_width=True)
    st.caption("Mirrors the report's limits: evidence is institutional, from older children, and largely self-reported.")
