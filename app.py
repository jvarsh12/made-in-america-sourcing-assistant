import streamlit as st
import pandas as pd
import re
from rapidfuzz import fuzz
from geopy.distance import geodesic
import pgeocode
import base64
import folium
from streamlit_folium import st_folium
from collections import defaultdict

# the first Streamlit command
st.set_page_config(page_title="Buy American", layout="wide", initial_sidebar_state="collapsed")  # :contentReference[oaicite:4]{index=4}


def image_to_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def matched_terms(query, text):
    query_tokens = set(query.lower().split())
    text_tokens = set(text.lower().replace(",", " ").split())
    return sorted(query_tokens.intersection(text_tokens))


def fuzzy_relevance(query, text):
    return fuzz.token_set_ratio(query, text) / 100


@st.cache_data
def load_data():
    df = pd.read_csv("westmoreland_seed_suppliers.csv", dtype={"zip": str})
    df["zip"] = df["zip"].str.replace(r"\.0$", "", regex=True).str.zfill(5)
    return df



# -----------------------------
# ZIP geocoder
# -----------------------------
zip_geocoder = pgeocode.Nominatim("us")


@st.cache_data
def zip_to_latlon(zip_code):
    if pd.isna(zip_code):
        return None, None
    location = zip_geocoder.query_postal_code(str(zip_code))
    if pd.isna(location.latitude) or pd.isna(location.longitude):
        return None, None
    return location.latitude, location.longitude


def distance_miles_and_score(buyer_lat, buyer_lon, supplier_zip):
    if buyer_lat is None or buyer_lon is None:
        return None, 0

    sup_lat, sup_lon = zip_to_latlon(supplier_zip)
    if sup_lat is None or sup_lon is None:
        return None, 0

    miles = geodesic((buyer_lat, buyer_lon), (sup_lat, sup_lon)).miles
    score = max(0, 1 - miles / 100)  # keep your current rule
    return miles, score


def _clean_text(x) -> str:
    if x is None:
        return ""
    s = str(x).strip()
    return "" if s.lower() in {"nan", "none"} else s


# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
/* Tighten the top padding a bit */

/* Header typography */
.gov-title {
  font-size: 2.6rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.05;
  margin-bottom: 0.25rem;
  color: #0F172A;
}
.gov-subtitle {
  font-size: 1.05rem;
  color: #334155;
  margin-top: 0.25rem;
}

/* Portraits */
.circle-img {
  width: 125px;
  height: 125px;
  border-radius: 50%;
  border: 5px solid #0B3D91;          /* navy ring */
  outline: 4px solid #FFFFFF;         /* white separation ring */
  object-fit: cover;
  box-shadow: 0px 6px 18px rgba(15, 23, 42, 0.15);
}
.center { text-align: center; }

/* Name labels under portraits */
.portrait-label {
  display: block;
  margin-top: 0.45rem;
  font-size: 0.85rem;
  color: #334155;
  font-weight: 600;
}

/* Slogan under both portraits */
.slogan {
  margin-top: 0.75rem;
  padding: 0.55rem 0.95rem;
  border: 1px solid #D7DEE9;
  background: #F3F6FA;
  border-radius: 0.75rem;
  color: #0F172A;
  font-weight: 700;
  font-size: 0.95rem;

  /* ✅ make it responsive when the sidebar changes layout */
  display: inline-block;     /* shrink-wrap to content */
  max-width: 100%;           /* never overflow parent column */
  box-sizing: border-box;
  white-space: normal;       /* allow wrap if needed */
  text-align: center;
  overflow-wrap: anywhere;   /* safe wrap for long words */
}

/* Optional: make Streamlit "info" box feel more enterprise */
div[data-testid="stAlert"] {
  border-radius: 0.75rem;
}
            
/* --- Policy expander polish --- */
div[data-testid="stExpander"] summary {
  background: #F3F6FA;
  border: 1px solid #D7DEE9;
  border-radius: 0.75rem;
  padding: 0.8rem 1rem;
}

/* expander open content area */
div[data-testid="stExpanderDetails"] {
  margin-top: 0.6rem;
}

/* --- Policy cards --- */
.policy-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
}
@media (min-width: 900px) {
  .policy-grid { grid-template-columns: 1fr 1fr 1fr; }
}

.policy-card {
  border: 1px solid #D7DEE9;
  background: #FFFFFF;
  border-radius: 0.75rem;
  padding: 0.9rem 1rem;
  box-shadow: 0px 6px 18px rgba(15, 23, 42, 0.06);
}

.policy-h {
  font-weight: 800;
  color: #0B3D91;
  margin-bottom: 0.35rem;
  display: flex;
  gap: 0.4rem;
  align-items: center;
}

.policy-b {
  color: #334155;
  font-size: 0.95rem;
  line-height: 1.35;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------
# Header layout
# -----------------------------
trump_img = image_to_base64("assets/trump.jpg")
melania_img = image_to_base64("assets/melania.png")

left_col, right_col = st.columns([3, 1])

with left_col:
    st.markdown('<div class="gov-title">🔧 Made-in-America Sourcing Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="gov-subtitle">AI-powered matching + distance ranking to help small businesses discover nearby U.S. manufacturers.</div>', unsafe_allow_html=True)


with right_col:
    img_col1, img_col2 = st.columns(2)

    with img_col1:
        st.markdown(
            f"""
            <div class="center">
                <img src="data:image/jpeg;base64,{trump_img}" class="circle-img">
                <span class="portrait-label">President Donald J. Trump</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with img_col2:
        st.markdown(
            f"""
            <div class="center">
                <img src="data:image/png;base64,{melania_img}" class="circle-img">
                <span class="portrait-label">First Lady Melania Trump</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        '<div class="center"><div class="slogan">Build American Manufacturing Jobs.</div></div>',
        unsafe_allow_html=True
    )

    

st.divider()


with st.expander("US Community Impact & Policy Alignment", expanded=False):
    st.markdown(
        """
        <div class="policy-grid">
          <div class="policy-card">
            <div class="policy-h">🧩 Problem</div>
            <div class="policy-b">
              Small businesses often rely on distant or overseas suppliers because they lack visibility into nearby American manufacturers.
            </div>
          </div>

          <div class="policy-card">
            <div class="policy-h">⚙️ Our Solution</div>
            <div class="policy-b">
              AI-powered matching + distance ranking helps quickly identify nearby U.S. manufacturers to source faster and reduce shipping delays.
            </div>
          </div>

          <div class="policy-card">
            <div class="policy-h">🇺🇸 Impact</div>
            <div class="policy-b">
              • Encourages Buy American purchasing<br>
              • Strengthens local supply chains<br>
              • Supports domestic manufacturing jobs
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# Sidebar inputs (cleaner main page)  :contentReference[oaicite:6]{index=6
# -----------------------------
with st.sidebar:
    st.header("Search")
    query = st.text_input(
        "Describe what you need",
        placeholder="e.g., CNC aluminum turning, stainless spacer, grinding service",
    )
    buyer_zip = st.text_input("Buyer ZIP code", value="15601")
    st.caption("Tip: Try keywords like machining, turning, milling, grinding, casting.")
    
    # Jump link to bring user to the Results/Map/Highlights section
    st.markdown("⬇️ [Jump to Results](#results)")

buyer_lat, buyer_lon = zip_to_latlon(buyer_zip)

# -----------------------------
# Data
# -----------------------------
df = load_data()

# -----------------------------
# Main logic
# -----------------------------
results = None
if query:
    distance_miles = []
    relevance_scores = []
    distance_scores = []
    final_scores = []
    matched_explanations = []

    for _, row in df.iterrows():
        searchable_text = (
            str(row.get("capability_tags", "")) + " " +
            str(row.get("process_tags", "")) + " " +
            str(row.get("material_tags", ""))
        ).lower()

        matches = matched_terms(query, searchable_text)
        rel = fuzzy_relevance(query.lower(), searchable_text)
        miles, dist_score = distance_miles_and_score(buyer_lat, buyer_lon, row.get("zip"))

        final = (0.7 * rel) + (0.3 * dist_score)

        distance_miles.append(miles)
        relevance_scores.append(rel)
        distance_scores.append(dist_score)
        final_scores.append(final)
        matched_explanations.append(", ".join(matches[:5]))

    df["relevance_score"] = relevance_scores
    df["distance_miles"] = pd.Series(distance_miles).round(1)
    df["distance_score"] = distance_scores
    df["final_score"] = final_scores
    df["matched_on"] = matched_explanations

    results = (
        df[df["final_score"] > 0]
        .sort_values(by=["final_score", "distance_miles"], ascending=[False, True])
        .head(5)
        .reset_index(drop=True)
    )

# -----------------------------
# Tabs: Results / Map / Highlights  :contentReference[oaicite:7]{index=7}
# -----------------------------
# Anchor target for jump link
st.markdown('<div id="results"></div>', unsafe_allow_html=True)

tab_results, tab_map, tab_highlights = st.tabs(["🏆 Results", "🗺️ Map", "🏭 Highlights"])

with tab_results:
    # st.subheader("Top 5 Local Matches")
    st.markdown("## Top 5 Local Matches")

    if results is None or results.empty:
        st.info("Enter a need in the sidebar to see results.")
    else:
        best = results.iloc[0]
        best = results.iloc[0]
        closest = results["distance_miles"].min()

        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.caption("Top supplier")
            st.markdown(f"**{best['supplier_name']}**")
        with c2:
            st.caption("Best score")
            st.markdown(f"**{best['final_score']:.2f}**")
        with c3:
            st.caption("Closest (miles)")
            st.markdown(f"**{closest:.1f}**")

        st.dataframe(
            results[[
                "supplier_name","city","state","zip",
                "capability_tags","process_tags",
                "distance_miles","relevance_score","final_score","website"
            ]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "supplier_name": st.column_config.TextColumn("Supplier"),
                "capability_tags": st.column_config.TextColumn("Capabilities"),
                "process_tags": st.column_config.TextColumn("Processes"),
                "distance_miles": st.column_config.NumberColumn("Distance (miles)", format="%.1f"),
                "relevance_score": st.column_config.NumberColumn("Relevance", format="%.2f"),
                "final_score": st.column_config.NumberColumn("Overall score", format="%.2f"),

                # show domain only, still clickable
                "website": st.column_config.LinkColumn(
                    "Website",
                    display_text=r"https?://(?:www\.)?([^/]+)"
                ),

                "zip": st.column_config.TextColumn("ZIP"),
                "city": st.column_config.TextColumn("City"),
                "state": st.column_config.TextColumn("State"),
            },
            column_order=[
                "supplier_name","city","state","zip",
                "capability_tags","process_tags",
                "distance_miles","relevance_score","final_score","website"
            ],
        )
      
with tab_map:
    st.subheader("Supplier Locations (Top 5 Matches)")

    if results is None or results.empty:
        st.info("Search first to view the map.")
    elif buyer_lat is None or buyer_lon is None:
        st.info("Buyer location not available for map display.")
    else:
        m = folium.Map(location=[buyer_lat, buyer_lon], tiles="CartoDB positron", zoom_start=9)
        bounds = []

        folium.Marker(
            [buyer_lat, buyer_lon],
            tooltip="Buyer Location",
            icon=folium.Icon(color="blue", icon="home"),
        ).add_to(m)
        bounds.append([buyer_lat, buyer_lon])

        zip_counts = defaultdict(int)

        for _, row in results.iterrows():
            sup_lat, sup_lon = zip_to_latlon(row["zip"])
            if sup_lat is None or sup_lon is None:
                continue

            count = zip_counts[row["zip"]]
            zip_counts[row["zip"]] += 1

            offset = 0.002 * count  # small jitter so same-ZIP suppliers don’t overlap
            adj_lat = sup_lat + offset
            adj_lon = sup_lon + offset

            folium.CircleMarker(
                location=[adj_lat, adj_lon],
                radius=7,
                color="red",
                fill=True,
                fill_color="red",
                fill_opacity=0.85,
                tooltip=f"{row['supplier_name']} ({row['distance_miles']} miles)",
            ).add_to(m)

            bounds.append([adj_lat, adj_lon])

        if len(bounds) > 1:
            m.fit_bounds(bounds, padding=(80, 80), max_zoom=11)  # try 10–12

        st_folium(m, width=1500, height=600)

with tab_highlights:
    st.subheader("Supplier highlights (Top 5)")

    if results is None or results.empty:
        st.info("Search first to view supplier highlights.")
    else:
        for _, row in results.iterrows():
            supplier_name = _clean_text(row.get("supplier_name"))
            miles = row.get("distance_miles")
            miles_str = f"{miles} miles" if miles is not None else "Distance n/a"

            short_desc = _clean_text(row.get("Short Description"))  # must match CSV exactly
            matched_on = _clean_text(row.get("matched_on"))
            website = _clean_text(row.get("website"))
            phone = _clean_text(row.get("phone"))
            email = _clean_text(row.get("email"))

            with st.expander(f"{supplier_name} — {miles_str}", expanded=False):
                if short_desc:
                    st.write(short_desc)
                else:
                    st.caption("No short description added yet.")

                if matched_on:
                    st.markdown(f"**Matched on:** {matched_on}")

                if website:
                    st.markdown(f"🔗 Website: {website}")
                if phone:
                    st.markdown(f"📞 Phone: {phone}")
                if email:
                    st.markdown(f"✉️ Email: {email}")

