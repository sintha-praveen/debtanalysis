import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

# 1. Database Connection
engine = create_engine(
    "postgresql+psycopg2://postgres:admin@localhost:5432/international_debt_db"
)

st.set_page_config(page_title="International Debt Analytics", layout="wide")
st.title("🌐 International Debt Analytics Dashboard")
st.caption("World Bank External Debt Analysis & Decision-Support System")

# 2. Executive Metrics Bar
kpi_query = """
    SELECT 
        ROUND((SUM(d."Debt_Value_USD") / 1e12)::numeric, 2) AS total_debt_trillion,
        (SELECT COUNT(*) FROM countries) AS total_countries,
        (SELECT COUNT(*) FROM indicators) AS total_indicators
    FROM debt_data d;
"""
kpi_df = pd.read_sql(kpi_query, engine)

col1, col2, col3 = st.columns(3)
col1.metric("Total Global Debt Recorded", f"${kpi_df['total_debt_trillion'][0]} Trillion")
col2.metric("Sovereign Nations Analyzed", f"{kpi_df['total_countries'][0]}")
col3.metric("Monitored Debt Indicators", f"{kpi_df['total_indicators'][0]}")

st.divider()

# Create Tabs
tab_global, tab_country = st.tabs(["🌍 Global Overview", "🔍 Country Deep Dive"])

# =========================================================
# TAB 1: GLOBAL OVERVIEW
# =========================================================
with tab_global:
    st.subheader("Global Debt Distribution & Rankings")
    
    col_top, col_low = st.columns(2)
    with col_top:
        st.markdown("**Top 10 Most Indebted Countries**")
        top_query = """
            SELECT "Country", ROUND((SUM("Debt_Value_USD") / 1e9)::numeric, 2) AS debt_billion
            FROM debt_data
            GROUP BY "Country"
            ORDER BY debt_billion DESC
            LIMIT 10;
        """
        top_df = pd.read_sql(top_query, engine)
        fig_top = px.bar(top_df, x="debt_billion", y="Country", orientation="h",
                         labels={"debt_billion": "Debt (Billion USD)"})
        fig_top.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_top, use_container_width=True)

    with col_low:
        st.markdown("**Top 10 Lowest Indebted Countries**")
        low_query = """
            SELECT "Country", ROUND((SUM("Debt_Value_USD") / 1e6)::numeric, 2) AS debt_million
            FROM debt_data
            GROUP BY "Country"
            HAVING SUM("Debt_Value_USD") > 0
            ORDER BY debt_million ASC
            LIMIT 10;
        """
        low_df = pd.read_sql(low_query, engine)
        fig_low = px.bar(low_df, x="debt_million", y="Country", orientation="h",
                         labels={"debt_million": "Debt (Million USD)"})
        fig_low.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_low, use_container_width=True)

    st.subheader("Regional Breakdown")
    reg_query = """
        SELECT COALESCE("Region", 'Unclassified') AS region, 
               ROUND((SUM("Debt_Value_USD") / 1e9)::numeric, 2) AS debt_billion
        FROM debt_data
        GROUP BY "Region"
        ORDER BY debt_billion DESC;
    """
    reg_df = pd.read_sql(reg_query, engine)
    fig_pie = px.pie(reg_df, names="region", values="debt_billion", hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

# =========================================================
# TAB 2: COUNTRY DEEP DIVE (User selects/enters country)
# =========================================================
with tab_country:
    st.subheader("Sovereign Country Profile")
    
    # Load list of countries for dropdown / autocomplete search
    country_list = pd.read_sql(
        'SELECT DISTINCT "Country" FROM debt_data ORDER BY "Country";', engine
    )["Country"].tolist()
    
    selected_country = st.selectbox(
        "Type or select a country to examine:", country_list, index=0
    )
    
    if selected_country:
        # Country Specific KPI Metrics
        c_kpi_query = f"""
            SELECT 
                ROUND((SUM("Debt_Value_USD") / 1e9)::numeric, 2) AS country_debt_billion,
                COUNT(DISTINCT "Series Code") AS indicators_used,
                MIN("Year") AS start_year,
                MAX("Year") AS end_year
            FROM debt_data
            WHERE "Country" = '{selected_country}';
        """
        c_kpi_df = pd.read_sql(c_kpi_query, engine)
        
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Total Debt ({selected_country})", f"${c_kpi_df['country_debt_billion'][0]:,.2f} Billion")
        m2.metric("Active Indicators", f"{c_kpi_df['indicators_used'][0]}")
        m3.metric("Time Period Recorded", f"{c_kpi_df['start_year'][0]} – {c_kpi_df['end_year'][0]}")
        
        st.divider()

        # Yearly Debt Trend for Selected Country
        st.markdown(f"### 📈 Debt Trajectory Over Time: {selected_country}")
        country_trend_query = f"""
            SELECT "Year", ROUND((SUM("Debt_Value_USD") / 1e9)::numeric, 2) AS debt_billion
            FROM debt_data
            WHERE "Country" = '{selected_country}'
            GROUP BY "Year"
            ORDER BY "Year";
        """
        trend_df = pd.read_sql(country_trend_query, engine)
        fig_country_trend = px.line(
            trend_df, x="Year", y="debt_billion", markers=True,
            labels={"Year": "Year", "debt_billion": "Debt (Billion USD)"}
        )
        st.plotly_chart(fig_country_trend, use_container_width=True)

        # Top Debt Categories / Indicators for this specific country
        st.markdown(f"### 📊 Top 5 Debt Indicators for {selected_country}")
        top_ind_query = f"""
            SELECT "Indicator", ROUND((SUM("Debt_Value_USD") / 1e9)::numeric, 2) AS total_billion
            FROM debt_data
            WHERE "Country" = '{selected_country}'
            GROUP BY "Indicator"
            ORDER BY total_billion DESC
            LIMIT 5;
        """
        ind_df = pd.read_sql(top_ind_query, engine)
        fig_ind = px.bar(
            ind_df, x="total_billion", y="Indicator", orientation="h",
            labels={"total_billion": "Amount (Billion USD)", "Indicator": "Indicator"}
        )
        fig_ind.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_ind, use_container_width=True)