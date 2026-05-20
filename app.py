"""
India Clinical Trials Intelligence Dashboard
Professional healthcare analytics platform for Indian clinical trials.
"""

import streamlit as st
import pandas as pd
import numpy as np
from src.config import (
    APP_TITLE, APP_ICON, SIDEBAR_OPTIONS, DASHBOARD_DESCRIPTION,
    SPONSOR_INTELLIGENCE_DESCRIPTION, THERAPEUTIC_ANALYSIS_DESCRIPTION,
    GEOGRAPHIC_ANALYSIS_DESCRIPTION, TRIAL_EXPLORER_DESCRIPTION,
    THERAPEUTIC_AREAS, TRIAL_PHASES, RECRUITMENT_STATUSES, INDIAN_STATES
)
from src.data_loader import (
    load_clinical_trials_data, get_unique_values, get_data_summary,
    apply_filters, validate_and_log_data, clear_data_cache
)
from src.visualizations import (
    plot_trials_by_therapeutic_area, plot_trial_growth_by_year,
    plot_top_sponsors, plot_phase_distribution, plot_recruitment_status,
    plot_geographic_distribution, plot_sponsor_by_therapeutic_area,
    plot_enrollment_by_phase
)


# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data (cached for performance)
df, metadata = load_clinical_trials_data()

# Validate data
if not validate_and_log_data(df, metadata):
    # Show error state
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
    st.title(f"{APP_ICON} {APP_TITLE}")
    
    st.error("⚠️ Error Loading Data", icon="🚨")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Error Details")
        if metadata.get("error"):
            st.write(f"**Error:** {metadata['error']}")
        if not metadata.get("file_exists"):
            st.write("📁 **Issue:** Data file not found at `data/processed/india_trials_clean.csv`")
            st.write("**Solution:** Run the data ingestion and cleaning pipeline first")
        if metadata.get("is_empty"):
            st.write("📊 **Issue:** Data file is empty")
            st.write("**Solution:** Ensure the cleaning pipeline has processed data")
    
    with col2:
        st.subheader("Quick Links")
        st.markdown("""
        1. **Run API Ingestion:**
           ```bash
           python -m src.ingestion.clinical_trials_api
           ```
        2. **Run Data Cleaning:**
           ```bash
           python -m src.cleaning.clean_trials
           ```
        3. **Refresh This Dashboard:**
           - Click button below to reload
        """)
        if st.button("🔄 Retry Loading Data"):
            clear_data_cache()
            st.rerun()
    
    st.stop()

# Initialize session state for filters
if "filters" not in st.session_state:
    st.session_state.filters = {
        "therapeutic_areas": [],
        "phases": [],
        "statuses": [],
        "sponsor": "All Sponsors",
        "states": [],
        "year_range": (2020, 2027)
    }

# Get summary statistics for full dataset
stats = get_data_summary(df, metadata)




def render_overview_dashboard():
    """Render the main overview dashboard."""
    st.header("📊 Overview Dashboard")
    st.markdown(DASHBOARD_DESCRIPTION)
    st.divider()
    
    # Apply filters to data
    filtered_df = apply_filters(df, st.session_state.filters)
    filtered_stats = get_data_summary(filtered_df, metadata)
    
    # KPI Metrics
    st.subheader("Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        delta_text = f"{(filtered_stats['recruiting_trials']/filtered_stats['total_trials']*100):.1f}% active" if filtered_stats['total_trials'] > 0 else "0 trials"
        st.metric(
            label="Total Active Trials",
            value=filtered_stats['active_trials'],
            delta=delta_text
        )
    
    with col2:
        st.metric(
            label="Active Sponsors",
            value=filtered_stats['total_sponsors'],
            delta="Currently recruiting"
        )
    
    with col3:
        st.metric(
            label="Recruiting Trials",
            value=filtered_stats['recruiting_trials'],
            delta=f"of {filtered_stats['total_trials']} total"
        )
    
    with col4:
        st.metric(
            label="Avg Trial Duration",
            value=f"{filtered_stats['avg_duration_days']} days",
            delta="~1.9 years"
        )
    
    with col5:
        st.metric(
            label="Most Active Area",
            value=filtered_stats['most_active_area'] if filtered_stats['most_active_area'] != "N/A" else "—",
            delta=f"Top therapeutic category"
        )
    
    st.divider()
    
    # Main charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(plot_trials_by_therapeutic_area(filtered_df), use_container_width=True)
    
    with col2:
        st.plotly_chart(plot_trial_growth_by_year(filtered_df), use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(plot_phase_distribution(filtered_df), use_container_width=True)
    
    with col2:
        st.plotly_chart(plot_recruitment_status(filtered_df), use_container_width=True)


def render_sponsor_intelligence():
    """Render sponsor intelligence and analysis page."""
    st.header("🏢 Sponsor Intelligence")
    st.markdown(SPONSOR_INTELLIGENCE_DESCRIPTION)
    st.divider()
    
    # Apply filters
    filtered_df = apply_filters(df, st.session_state.filters)
    
    if len(filtered_df) == 0:
        st.warning("No trials match the selected filters.")
        return
    
    # Top sponsors metrics
    st.subheader("Sponsor Portfolio Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    top_sponsor = filtered_df["sponsor"].value_counts().index[0] if len(filtered_df) > 0 else "N/A"
    top_sponsor_count = filtered_df["sponsor"].value_counts().values[0] if len(filtered_df) > 0 else 0
    
    with col1:
        st.metric(
            label="Leading Sponsor",
            value=top_sponsor[:20] if len(str(top_sponsor)) > 20 else top_sponsor,
            delta=f"{top_sponsor_count} trials"
        )
    
    avg_trials_per_sponsor = len(filtered_df) / filtered_df["sponsor"].nunique() if filtered_df["sponsor"].nunique() > 0 else 0
    with col2:
        st.metric(
            label="Avg Trials per Sponsor",
            value=f"{avg_trials_per_sponsor:.1f}",
            delta="Portfolio size"
        )
    
    sponsor_diversity = filtered_df.groupby("sponsor")["therapeutic_area"].nunique().mean() if filtered_df["sponsor"].nunique() > 0 else 0
    with col3:
        st.metric(
            label="Avg Areas per Sponsor",
            value=f"{sponsor_diversity:.1f}",
            delta="Therapeutic focus"
        )
    
    total_enrollment = filtered_df["enrollment_count"].sum() if "enrollment_count" in filtered_df.columns else 0
    with col4:
        st.metric(
            label="Total Enrollment",
            value=f"{int(total_enrollment):,}",
            delta="Across all trials"
        )
    
    st.divider()
    
    # Sponsor visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(plot_top_sponsors(filtered_df, top_n=10), use_container_width=True)
    
    with col2:
        st.plotly_chart(plot_enrollment_by_phase(filtered_df), use_container_width=True)
    
    st.plotly_chart(plot_sponsor_by_therapeutic_area(filtered_df), use_container_width=True)
    
    # Sponsor filter and table
    st.divider()
    st.subheader("Detailed Sponsor Information")
    
    sponsors = sorted(filtered_df["sponsor"].unique())
    if len(sponsors) > 0:
        selected_sponsor = st.selectbox(
            "Select a sponsor to view details:",
            sponsors
        )
        
        sponsor_df = filtered_df[filtered_df["sponsor"] == selected_sponsor].copy()
        sponsor_df_display = sponsor_df.copy()
        sponsor_df_display["start_date"] = pd.to_datetime(sponsor_df_display["start_date"]).dt.date
        sponsor_df_display["completion_date"] = pd.to_datetime(sponsor_df_display["completion_date"]).dt.date
        
        st.metric(
            label=f"{selected_sponsor} - Trial Count",
            value=len(sponsor_df)
        )
        
        display_cols = ["nct_id", "therapeutic_area", "phase", "recruitment_status", "city", "enrollment_count"]
        display_cols = [col for col in display_cols if col in sponsor_df_display.columns]
        st.dataframe(sponsor_df_display[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No sponsors found matching the selected filters.")


def render_therapeutic_area_analysis():
    """Render therapeutic area analysis page."""
    st.header("🔬 Therapeutic Area Analysis")
    st.markdown(THERAPEUTIC_ANALYSIS_DESCRIPTION)
    st.divider()
    
    # Apply filters
    filtered_df = apply_filters(df, st.session_state.filters)
    
    if len(filtered_df) == 0:
        st.warning("No trials match the selected filters.")
        return
    
    # Therapeutic area metrics
    st.subheader("Therapeutic Area Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    areas = filtered_df["therapeutic_area"].unique()
    with col1:
        st.metric(
            label="Total Therapeutic Areas",
            value=len(areas),
            delta="Disease categories"
        )
    
    most_active_area = filtered_df["therapeutic_area"].value_counts().index[0] if len(filtered_df) > 0 else "N/A"
    with col2:
        st.metric(
            label="Most Active Area",
            value=most_active_area,
            delta=f"{len(filtered_df[filtered_df['therapeutic_area'] == most_active_area])} trials"
        )
    
    recruiting_trials = filtered_df[filtered_df["recruitment_status"] == "Recruiting"]
    most_recruiting_area = recruiting_trials["therapeutic_area"].value_counts().index[0] if len(recruiting_trials) > 0 else "N/A"
    with col3:
        st.metric(
            label="Most Recruiting Area",
            value=most_recruiting_area,
            delta="Active recruitment"
        )
    
    avg_enrollment = filtered_df.groupby("therapeutic_area")["enrollment_count"].mean().max() if "enrollment_count" in filtered_df.columns and len(filtered_df) > 0 else 0
    with col4:
        st.metric(
            label="Highest Avg Enrollment",
            value=f"{int(avg_enrollment)}",
            delta="Participants"
        )
    
    st.divider()
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(plot_trials_by_therapeutic_area(filtered_df), use_container_width=True)
    
    with col2:
        st.plotly_chart(plot_recruitment_status(filtered_df), use_container_width=True)
    
    # Area-specific analysis
    st.divider()
    st.subheader("Detailed Area Analysis")
    
    areas_list = sorted(filtered_df["therapeutic_area"].unique())
    if len(areas_list) > 0:
        selected_area = st.selectbox(
            "Select a therapeutic area:",
            areas_list
        )
        
        area_df = filtered_df[filtered_df["therapeutic_area"] == selected_area]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Trials", len(area_df))
        
        with col2:
            st.metric("Sponsors", area_df["sponsor"].nunique())
        
        with col3:
            avg_enroll = area_df["enrollment_count"].mean() if "enrollment_count" in area_df.columns else 0
            st.metric("Avg Enrollment", f"{int(avg_enroll)}")
        
        with col4:
            phases = area_df["phase"].value_counts().index[0] if len(area_df) > 0 else "N/A"
            st.metric("Most Common Phase", phases)
        
        # Phase distribution for selected area
        phase_dist = area_df["phase"].value_counts()
        if len(phase_dist) > 0:
            import plotly.graph_objects as go
            fig = go.Figure(data=[
                go.Bar(x=phase_dist.index, y=phase_dist.values, marker_color="#6366F1")
            ])
            fig.update_layout(
                title=f"Phase Distribution in {selected_area}",
                xaxis_title="Phase",
                yaxis_title="Number of Trials",
                showlegend=False,
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No therapeutic areas found matching the selected filters.")


def render_geographic_analysis():
    """Render geographic distribution analysis page."""
    st.header("🗺️ Geographic Analysis")
    st.markdown(GEOGRAPHIC_ANALYSIS_DESCRIPTION)
    st.divider()
    
    # Apply filters
    filtered_df = apply_filters(df, st.session_state.filters)
    
    if len(filtered_df) == 0:
        st.warning("No trials match the selected filters.")
        return
    
    # Geographic metrics
    st.subheader("Geographic Distribution")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="States with Trials",
            value=filtered_df["state"].nunique(),
            delta="Geographic spread"
        )
    
    with col2:
        st.metric(
            label="Cities with Trials",
            value=filtered_df["city"].nunique(),
            delta="Research centers"
        )
    
    top_state = filtered_df["state"].value_counts().index[0] if len(filtered_df) > 0 else "N/A"
    with col3:
        st.metric(
            label="Most Active State",
            value=top_state,
            delta=f"{len(filtered_df[filtered_df['state'] == top_state])} trials"
        )
    
    top_city = filtered_df["city"].value_counts().index[0] if len(filtered_df) > 0 else "N/A"
    with col4:
        st.metric(
            label="Top Research City",
            value=top_city,
            delta=f"{len(filtered_df[filtered_df['city'] == top_city])} trials"
        )
    
    st.divider()
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(plot_geographic_distribution(filtered_df, top_n=10), use_container_width=True)
    
    with col2:
        # City distribution
        city_counts = filtered_df["city"].value_counts().head(10)
        import plotly.graph_objects as go
        fig = go.Figure(data=[
            go.Bar(
                y=city_counts.index,
                x=city_counts.values,
                orientation="h",
                marker_color="#10B981",
                text=city_counts.values,
                textposition="auto"
            )
        ])
        fig.update_layout(
            title="Top 10 Cities by Trial Count",
            xaxis_title="Number of Trials",
            yaxis_title="City",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # State-wise filter
    st.divider()
    st.subheader("State-wise Trial Details")
    
    states_list = sorted(filtered_df["state"].unique())
    if len(states_list) > 0:
        selected_state = st.selectbox(
            "Select a state:",
            states_list
        )
        
        state_df = filtered_df[filtered_df["state"] == selected_state].copy()
        state_df_display = state_df.copy()
        state_df_display["start_date"] = pd.to_datetime(state_df_display["start_date"]).dt.date
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Trials", len(state_df))
        
        with col2:
            st.metric("Cities", state_df["city"].nunique())
        
        with col3:
            total_enroll = state_df["enrollment_count"].sum() if "enrollment_count" in state_df.columns else 0
            st.metric("Total Enrollment", f"{int(total_enroll):,}")
        
        display_cols = ["nct_id", "sponsor", "city", "therapeutic_area", "phase", "enrollment_count"]
        display_cols = [col for col in display_cols if col in state_df_display.columns]
        st.dataframe(state_df_display[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No states found matching the selected filters.")


def render_trial_explorer():
    """Render interactive trial explorer page."""
    st.header("🔍 Trial Explorer")
    st.markdown(TRIAL_EXPLORER_DESCRIPTION)
    st.divider()
    
    # Local filters for this page
    st.subheader("Advanced Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        phases = sorted(df["phase"].unique().dropna())
        phase_filter = st.multiselect(
            "Trial Phase",
            phases,
            default=phases
        )
    
    with col2:
        statuses = sorted(df["recruitment_status"].unique().dropna())
        status_filter = st.multiselect(
            "Recruitment Status",
            statuses,
            default=[s for s in statuses if s in ["Recruiting", "Active, not recruiting"]]
        )
    
    with col3:
        areas = sorted(df["therapeutic_area"].unique().dropna())
        area_filter = st.multiselect(
            "Therapeutic Area",
            areas,
            default=areas
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_enroll = int(df["enrollment_count"].min()) if "enrollment_count" in df.columns else 0
        max_enroll = int(df["enrollment_count"].max()) if "enrollment_count" in df.columns else 1000
        enrollment_range = st.slider(
            "Enrollment Range",
            min_enroll,
            max_enroll,
            (min_enroll, max_enroll)
        )
    
    with col2:
        sponsors = sorted(df["sponsor"].unique().dropna())
        sponsor_filter = st.selectbox(
            "Sponsor (optional)",
            ["All Sponsors"] + sponsors,
            index=0
        )
    
    # Apply filters
    filtered_df = df[
        (df["phase"].isin(phase_filter)) &
        (df["recruitment_status"].isin(status_filter)) &
        (df["therapeutic_area"].isin(area_filter)) &
        (df["enrollment_count"] >= enrollment_range[0]) &
        (df["enrollment_count"] <= enrollment_range[1])
    ]
    
    if sponsor_filter != "All Sponsors":
        filtered_df = filtered_df[filtered_df["sponsor"] == sponsor_filter]
    
    st.divider()
    
    # Results summary
    st.subheader(f"Results: {len(filtered_df)} trials found")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trials", len(filtered_df))
    
    with col2:
        recruiting = (filtered_df["recruitment_status"] == "Recruiting").sum()
        st.metric("Recruiting", recruiting)
    
    with col3:
        total_enroll = filtered_df["enrollment_count"].sum() if "enrollment_count" in filtered_df.columns else 0
        st.metric("Total Enrollment", f"{int(total_enroll):,}")
    
    with col4:
        avg_enroll = filtered_df["enrollment_count"].mean() if "enrollment_count" in filtered_df.columns and len(filtered_df) > 0 else 0
        st.metric("Avg Trial Size", f"{int(avg_enroll)}")
    
    # Display filtered data
    st.divider()
    st.subheader("Trial Details")
    
    if len(filtered_df) > 0:
        display_df = filtered_df.copy()
        display_df["start_date"] = pd.to_datetime(display_df["start_date"]).dt.date
        display_df["completion_date"] = pd.to_datetime(display_df["completion_date"]).dt.date
        
        display_cols = [
            "nct_id", "sponsor", "therapeutic_area", "phase",
            "recruitment_status", "city", "state", "enrollment_count", "start_date"
        ]
        
        display_cols = [col for col in display_cols if col in display_df.columns]
        
        st.dataframe(
            display_df[display_cols],
            use_container_width=True,
            hide_index=True
        )
        
        # Export option
        csv = display_df[display_cols].to_csv(index=False)
        st.download_button(
            label="📥 Download Trial Data (CSV)",
            data=csv,
            file_name="clinical_trials_export.csv",
            mime="text/csv"
        )
    else:
        st.info("No trials match the selected filters.")


def main():
    """Main application entry point."""
    # Header
    st.title(f"{APP_ICON} {APP_TITLE}")
    
    # Sidebar navigation and filters
    with st.sidebar:
        st.header("Navigation & Controls")
        page = st.radio(
            "Select a page:",
            SIDEBAR_OPTIONS,
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Data refresh button
        st.subheader("📊 Data Management")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refresh Data", use_container_width=True):
                clear_data_cache()
                st.rerun()
        
        with col2:
            if st.button("ℹ️ Data Info", use_container_width=True):
                st.session_state.show_data_info = not st.session_state.get("show_data_info", False)
        
        # Show data info if requested
        if st.session_state.get("show_data_info"):
            st.info(
                f"**Dataset Status:**\n"
                f"• Records: {metadata['record_count']}\n"
                f"• Last Updated: {metadata.get('last_updated_timestamp', 'N/A')}\n"
                f"• File: data/processed/india_trials_clean.csv"
            )
        
        st.divider()
        
        # Global filters
        st.subheader("🔍 Global Filters")
        st.caption("Apply filters to all pages")
        
        # Therapeutic area filter
        areas = get_unique_values(df, "therapeutic_area")
        st.session_state.filters["therapeutic_areas"] = st.multiselect(
            "Therapeutic Areas",
            areas,
            default=st.session_state.filters.get("therapeutic_areas", []),
            key="sidebar_therapeutic"
        )
        
        # Phase filter
        phases = get_unique_values(df, "phase")
        st.session_state.filters["phases"] = st.multiselect(
            "Trial Phases",
            phases,
            default=st.session_state.filters.get("phases", []),
            key="sidebar_phases"
        )
        
        # Recruitment status filter
        statuses = get_unique_values(df, "recruitment_status")
        st.session_state.filters["statuses"] = st.multiselect(
            "Recruitment Status",
            statuses,
            default=st.session_state.filters.get("statuses", []),
            key="sidebar_statuses"
        )
        
        # Sponsor filter
        sponsors = ["All Sponsors"] + get_unique_values(df, "sponsor")
        st.session_state.filters["sponsor"] = st.selectbox(
            "Sponsor",
            sponsors,
            index=0 if st.session_state.filters.get("sponsor") == "All Sponsors" else (
                sponsors.index(st.session_state.filters.get("sponsor", "All Sponsors"))
                if st.session_state.filters.get("sponsor") in sponsors else 0
            ),
            key="sidebar_sponsor"
        )
        
        # State filter
        states = get_unique_values(df, "state")
        st.session_state.filters["states"] = st.multiselect(
            "States",
            states,
            default=st.session_state.filters.get("states", []),
            key="sidebar_states"
        )
        
        # Year range filter
        years = sorted(df["start_year"].dropna().unique())
        if len(years) > 0:
            min_year = int(years[0]) if len(years) > 0 else 2020
            max_year = int(years[-1]) if len(years) > 0 else 2027
            st.session_state.filters["year_range"] = st.slider(
                "Trial Start Year",
                min_year,
                max_year,
                (min_year, max_year),
                key="sidebar_year"
            )
        
        # Reset filters button
        if st.button("🔄 Reset All Filters", use_container_width=True):
            st.session_state.filters = {
                "therapeutic_areas": [],
                "phases": [],
                "statuses": [],
                "sponsor": "All Sponsors",
                "states": [],
                "year_range": (2020, 2027)
            }
            st.rerun()
        
        st.divider()
        
        # Dashboard info
        st.markdown("### Dashboard Info")
        st.info(
            "Real-time insights into Indian clinical trials. "
            "Monitor trial status, sponsor activity, and recruitment metrics "
            "across therapeutic areas and geographic regions."
        )
        
        st.divider()
        
        # Timestamp and metadata
        st.markdown("### Dataset Information")
        st.caption(
            f"**Last Updated:** {metadata.get('last_updated_timestamp', 'N/A')}\n"
            f"**Total Records:** {metadata['record_count']}\n"
            f"**File:** india_trials_clean.csv"
        )
        
        st.divider()
        
        st.markdown("### About")
        st.caption(
            "India Clinical Trials Intelligence Dashboard v2.1 | "
            "Built with Streamlit, Plotly & Real Clinical Data"
        )
    
    # Route to selected page
    if page == "Overview Dashboard":
        render_overview_dashboard()
    elif page == "Sponsor Intelligence":
        render_sponsor_intelligence()
    elif page == "Therapeutic Area Analysis":
        render_therapeutic_area_analysis()
    elif page == "Geographic Analysis":
        render_geographic_analysis()
    elif page == "Trial Explorer":
        render_trial_explorer()


if __name__ == "__main__":
    main()
