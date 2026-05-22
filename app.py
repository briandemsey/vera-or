"""
VERA-OR: Verification Engine for Results & Accountability - Oregon
Type 4 Dyslexia Screening using ELPA and OSAS Assessment Data

H-EDU.Solutions | https://h-edu.solutions
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_# Oregon colors
OR_BLUE = "#002776"  # Oregon blue
OR_GOLD = "#FFC72C"  # Oregon gold/yellow
OR_GREEN = "#154734"  # Forest green

# ============================================================================
# SAMPLE DATA - Oregon Districts
# ============================================================================

def load_districts():
    """Load Oregon district data."""
    districts_data = [
        ("1J-PPS", "Portland Public Schools", 45000, 9000, 20.0, 82.5),
        ("24J", "Salem-Keizer School District", 40000, 10000, 25.0, 78.3),
        ("48J", "Beaverton School District", 38000, 6840, 18.0, 88.1),
        ("1J-HIL", "Hillsboro School District", 20000, 5000, 25.0, 81.2),
        ("4J", "Eugene School District 4J", 16000, 1920, 12.0, 85.4),
        ("23J", "Tigard-Tualatin School District", 12000, 2160, 18.0, 86.7),
        ("549C", "Medford School District", 13000, 2340, 18.0, 79.8),
        ("103", "Woodburn School District", 5500, 2750, 50.0, 74.2),
        ("7", "Reynolds School District", 11000, 3300, 30.0, 72.5),
        ("10J", "David Douglas School District", 10500, 3675, 35.0, 75.8),
    ]

    df = pd.DataFrame(districts_data, columns=[
        'district_id', 'district_name', 'total_students',
        'ell_count', 'ell_percent', 'graduation_rate'
    ])
    return df

def load_elpa_data():
    """Load sample ELPA (English Language Proficiency Assessment) data."""
    elpa_data = []

    districts = [
        ("1J-PPS", "Portland Public Schools"),
        ("24J", "Salem-Keizer School District"),
        ("48J", "Beaverton School District"),
        ("1J-HIL", "Hillsboro School District"),
        ("4J", "Eugene School District 4J"),
        ("23J", "Tigard-Tualatin School District"),
        ("549C", "Medford School District"),
        ("103", "Woodburn School District"),
        ("7", "Reynolds School District"),
        ("10J", "David Douglas School District"),
    ]

    for district_id, district_name in districts:
        for grade in range(3, 9):
            for year in [2024, 2025]:
                # Generate realistic ELPA scores (1-5 scale converted to 100-500)
                base_speaking = 320 + (grade * 5)
                base_writing = 280 + (grade * 4)

                # Add district-specific variation
                if district_id == "103":  # Woodburn - highest EL%, larger delta
                    speaking_adj = 40
                    writing_adj = -10
                elif district_id == "10J":  # David Douglas
                    speaking_adj = 35
                    writing_adj = -5
                elif district_id == "7":  # Reynolds
                    speaking_adj = 30
                    writing_adj = 0
                elif district_id == "24J":  # Salem-Keizer
                    speaking_adj = 25
                    writing_adj = 5
                else:
                    speaking_adj = 15
                    writing_adj = 10

                elpa_data.append({
                    'district_id': district_id,
                    'district_name': district_name,
                    'grade': grade,
                    'year': year,
                    'total_tested': 150 + (grade * 10),
                    'listening_avg': base_speaking + speaking_adj - 5,
                    'speaking_avg': base_speaking + speaking_adj,
                    'reading_avg': base_writing + writing_adj + 10,
                    'writing_avg': base_writing + writing_adj,
                    'composite_avg': (base_speaking + speaking_adj + base_writing + writing_adj) / 2
                })

    return pd.DataFrame(elpa_data)

def load_osas_data():
    """Load sample OSAS (Oregon Statewide Assessment System) data."""
    osas_data = []

    districts = [
        ("1J-PPS", "Portland Public Schools"),
        ("24J", "Salem-Keizer School District"),
        ("48J", "Beaverton School District"),
        ("1J-HIL", "Hillsboro School District"),
        ("4J", "Eugene School District 4J"),
        ("23J", "Tigard-Tualatin School District"),
        ("549C", "Medford School District"),
        ("103", "Woodburn School District"),
        ("7", "Reynolds School District"),
        ("10J", "David Douglas School District"),
    ]

    for district_id, district_name in districts:
        for grade in range(3, 9):
            for year in [2024, 2025]:
                for subject in ['ELA', 'Math']:
                    # Generate realistic OSAS proficiency distributions
                    if district_id in ["48J", "4J", "23J"]:  # Higher performing
                        level_4 = 25 + (grade * 0.5)
                        level_3 = 35 + (grade * 0.3)
                        level_2 = 25 - (grade * 0.3)
                        level_1 = 15 - (grade * 0.5)
                    elif district_id in ["103", "7", "10J"]:  # Lower performing
                        level_4 = 10 + (grade * 0.3)
                        level_3 = 25 + (grade * 0.2)
                        level_2 = 35 - (grade * 0.2)
                        level_1 = 30 - (grade * 0.3)
                    else:  # Average
                        level_4 = 18 + (grade * 0.4)
                        level_3 = 30 + (grade * 0.2)
                        level_2 = 30 - (grade * 0.2)
                        level_1 = 22 - (grade * 0.4)

                    osas_data.append({
                        'district_id': district_id,
                        'district_name': district_name,
                        'grade': grade,
                        'subject': subject,
                        'year': year,
                        'total_tested': 500 + (grade * 20),
                        'level_1_pct': max(5, level_1),
                        'level_2_pct': max(10, level_2),
                        'level_3_pct': min(50, level_3),
                        'level_4_pct': min(40, level_4),
                        'mean_scale_score': 2450 + (level_3 + level_4) * 3
                    })

    return pd.DataFrame(osas_data)

# ============================================================================
# AUTHENTICATION
# ============================================================================

# ============================================================================
# TYPE 4 DETECTION
# ============================================================================

def compute_type4_analysis(elpa_df, district_id, grade, year):
    """
    Compute Type 4 (oral-written delta) analysis for a district.

    Type 4 candidates show strong oral skills but weak written skills.
    Delta = Speaking Score - Writing Score
    Flag threshold: Delta > 8 points (on normalized scale)
    """
    filtered = elpa_df[
        (elpa_df['district_id'] == district_id) &
        (elpa_df['grade'] == grade) &
        (elpa_df['year'] == year)
    ]

    if filtered.empty:
        return None

    row = filtered.iloc[0]

    # Calculate delta (Speaking - Writing)
    speaking = row['speaking_avg']
    writing = row['writing_avg']
    delta = speaking - writing

    # Normalize to 0-100 scale for threshold comparison
    delta_normalized = delta / 5  # Approximate normalization

    # Flag if delta exceeds threshold
    flagged = delta_normalized > 8

    return {
        'district_id': district_id,
        'district_name': row['district_name'],
        'grade': grade,
        'year': year,
        'speaking_avg': speaking,
        'writing_avg': writing,
        'delta': delta,
        'delta_normalized': delta_normalized,
        'flagged': flagged,
        'total_tested': row['total_tested'],
        'estimated_flagged': int(row['total_tested'] * 0.15) if flagged else int(row['total_tested'] * 0.05)
    }

# ============================================================================
# DASHBOARD PAGES
# ============================================================================

def render_overview(districts_df, elpa_df, osas_df):
    """Render the overview dashboard."""
    st.header("Oregon Education Overview")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Districts", len(districts_df))
    with col2:
        st.metric("Total Students", f"{districts_df['total_students'].sum():,}")
    with col3:
        st.metric("English Learners", f"{districts_df['ell_count'].sum():,}")
    with col4:
        avg_grad = districts_df['graduation_rate'].mean()
        st.metric("Avg Graduation Rate", f"{avg_grad:.1f}%")

    st.divider()

    # District overview table
    st.subheader("Pilot Districts")

    display_df = districts_df.copy()
    display_df['ell_percent'] = display_df['ell_percent'].apply(lambda x: f"{x:.1f}%")
    display_df['graduation_rate'] = display_df['graduation_rate'].apply(lambda x: f"{x:.1f}%")
    display_df.columns = ['District ID', 'District Name', 'Total Students', 'EL Count', 'EL %', 'Grad Rate']

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # EL Population chart
    st.subheader("English Learner Population by District")

    fig = px.bar(
        districts_df.sort_values('ell_count', ascending=True),
        x='ell_count',
        y='district_name',
        orientation='h',
        color='ell_percent',
        color_continuous_scale=[[0, OR_GOLD], [1, OR_BLUE]],
        labels={'ell_count': 'English Learners', 'district_name': 'District', 'ell_percent': 'EL %'}
    )
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def render_elpa_analysis(elpa_df, districts_df):
    """Render ELPA assessment analysis."""
    st.header("ELPA Assessment Analysis")

    st.markdown("""
    The **English Language Proficiency Assessment (ELPA)** measures English learners'
    proficiency across four domains: Listening, Speaking, Reading, and Writing.
    """)

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        district = st.selectbox(
            "Select District",
            options=districts_df['district_name'].tolist(),
            key="elpa_district"
        )

    with col2:
        grade = st.selectbox("Select Grade", options=list(range(3, 9)), key="elpa_grade")

    with col3:
        year = st.selectbox("Select Year", options=[2025, 2024], key="elpa_year")

    # Get district ID
    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]

    # Filter data
    filtered = elpa_df[
        (elpa_df['district_id'] == district_id) &
        (elpa_df['grade'] == grade) &
        (elpa_df['year'] == year)
    ]

    if not filtered.empty:
        row = filtered.iloc[0]

        st.divider()

        # Domain scores
        st.subheader("ELPA Domain Scores")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Listening", f"{row['listening_avg']:.0f}")
        with col2:
            st.metric("Speaking", f"{row['speaking_avg']:.0f}")
        with col3:
            st.metric("Reading", f"{row['reading_avg']:.0f}")
        with col4:
            st.metric("Writing", f"{row['writing_avg']:.0f}")

        # Domain comparison chart
        domains = ['Listening', 'Speaking', 'Reading', 'Writing']
        scores = [row['listening_avg'], row['speaking_avg'], row['reading_avg'], row['writing_avg']]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=domains,
            y=scores,
            marker_color=[OR_BLUE, OR_GREEN, OR_GOLD, OR_BLUE],
            text=[f"{s:.0f}" for s in scores],
            textposition='outside'
        ))
        fig.update_layout(
            title=f"ELPA Domain Scores - {district} - Grade {grade} ({year})",
            yaxis_title="Scale Score",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Oral vs Written gap highlight
        oral_avg = (row['listening_avg'] + row['speaking_avg']) / 2
        written_avg = (row['reading_avg'] + row['writing_avg']) / 2
        gap = oral_avg - written_avg

        st.subheader("Oral vs Written Gap")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Oral Average", f"{oral_avg:.0f}", help="(Listening + Speaking) / 2")
        with col2:
            st.metric("Written Average", f"{written_avg:.0f}", help="(Reading + Writing) / 2")
        with col3:
            delta_color = "normal" if gap < 20 else "inverse"
            st.metric("Gap", f"{gap:+.0f}", delta=f"{'Flag' if gap > 25 else 'OK'}", delta_color=delta_color)

def render_type4_detection(elpa_df, districts_df):
    """Render Type 4 detection analysis."""
    st.header("Type 4 Detection")

    st.markdown("""
    **Type 4 dyslexia candidates** demonstrate strong oral communication abilities but
    significant challenges with written expression. VERA-OR identifies these students by
    analyzing the delta between ELPA Speaking and Writing domain scores.

    **Flag Threshold:** Speaking - Writing delta > 8 points (normalized scale)
    """)

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        district = st.selectbox(
            "Select District",
            options=districts_df['district_name'].tolist(),
            key="type4_district"
        )

    with col2:
        grade = st.selectbox("Select Grade", options=list(range(3, 9)), key="type4_grade")

    with col3:
        year = st.selectbox("Select Year", options=[2025, 2024], key="type4_year")

    # Get district ID
    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]

    # Run analysis
    result = compute_type4_analysis(elpa_df, district_id, grade, year)

    if result:
        st.divider()

        # Results
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Speaking Score", f"{result['speaking_avg']:.0f}")
        with col2:
            st.metric("Writing Score", f"{result['writing_avg']:.0f}")
        with col3:
            st.metric("Delta", f"{result['delta']:+.0f}")
        with col4:
            status = "🚨 FLAGGED" if result['flagged'] else "✅ OK"
            st.metric("Status", status)

        # Visual delta display
        st.subheader("Oral-Written Delta Analysis")

        fig = go.Figure()

        # Speaking bar
        fig.add_trace(go.Bar(
            name='Speaking',
            x=['Score'],
            y=[result['speaking_avg']],
            marker_color=OR_GREEN,
            text=[f"{result['speaking_avg']:.0f}"],
            textposition='outside'
        ))

        # Writing bar
        fig.add_trace(go.Bar(
            name='Writing',
            x=['Score'],
            y=[result['writing_avg']],
            marker_color=OR_BLUE,
            text=[f"{result['writing_avg']:.0f}"],
            textposition='outside'
        ))

        fig.update_layout(
            title=f"Speaking vs Writing - {district} - Grade {grade}",
            barmode='group',
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        if result['flagged']:
            st.error(f"""
            **Type 4 Flag Triggered**

            This grade level shows a significant oral-written gap (delta: {result['delta']:+.0f}).

            - **Estimated students affected:** {result['estimated_flagged']} of {result['total_tested']} tested
            - **Recommended action:** Individual student-level screening for Type 4 dyslexia
            - **Next steps:** Cross-reference with OSAS ELA writing performance
            """)
        else:
            st.success(f"""
            **No Type 4 Flag**

            The oral-written gap for this grade level is within normal range (delta: {result['delta']:+.0f}).

            - **Students tested:** {result['total_tested']}
            - **Continue monitoring:** Regular ELPA domain analysis recommended
            """)

        # All grades comparison for district
        st.subheader(f"All Grades - {district} ({year})")

        all_grades_data = []
        for g in range(3, 9):
            r = compute_type4_analysis(elpa_df, district_id, g, year)
            if r:
                all_grades_data.append(r)

        if all_grades_data:
            grades_df = pd.DataFrame(all_grades_data)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=grades_df['grade'],
                y=grades_df['speaking_avg'],
                name='Speaking',
                mode='lines+markers',
                line=dict(color=OR_GREEN, width=3),
                marker=dict(size=10)
            ))
            fig.add_trace(go.Scatter(
                x=grades_df['grade'],
                y=grades_df['writing_avg'],
                name='Writing',
                mode='lines+markers',
                line=dict(color=OR_BLUE, width=3),
                marker=dict(size=10)
            ))

            fig.update_layout(
                title="Speaking vs Writing Across Grades",
                xaxis_title="Grade",
                yaxis_title="Scale Score",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

def render_osas_analysis(osas_df, districts_df):
    """Render OSAS assessment analysis."""
    st.header("OSAS Assessment Analysis")

    st.markdown("""
    The **Oregon Statewide Assessment System (OSAS)** uses Smarter Balanced assessments
    to measure student achievement in English Language Arts and Mathematics.
    """)

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        district = st.selectbox(
            "Select District",
            options=districts_df['district_name'].tolist(),
            key="osas_district"
        )

    with col2:
        grade = st.selectbox("Select Grade", options=list(range(3, 9)), key="osas_grade")

    with col3:
        subject = st.selectbox("Select Subject", options=['ELA', 'Math'], key="osas_subject")

    with col4:
        year = st.selectbox("Select Year", options=[2025, 2024], key="osas_year")

    # Get district ID
    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]

    # Filter data
    filtered = osas_df[
        (osas_df['district_id'] == district_id) &
        (osas_df['grade'] == grade) &
        (osas_df['subject'] == subject) &
        (osas_df['year'] == year)
    ]

    if not filtered.empty:
        row = filtered.iloc[0]

        st.divider()

        # Proficiency levels
        st.subheader("Proficiency Distribution")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Level 1", f"{row['level_1_pct']:.1f}%", help="Does Not Yet Meet")
        with col2:
            st.metric("Level 2", f"{row['level_2_pct']:.1f}%", help="Nearly Meets")
        with col3:
            st.metric("Level 3", f"{row['level_3_pct']:.1f}%", help="Meets")
        with col4:
            st.metric("Level 4", f"{row['level_4_pct']:.1f}%", help="Exceeds")

        # Proficiency chart
        levels = ['Level 1\n(Does Not Yet Meet)', 'Level 2\n(Nearly Meets)',
                  'Level 3\n(Meets)', 'Level 4\n(Exceeds)']
        values = [row['level_1_pct'], row['level_2_pct'], row['level_3_pct'], row['level_4_pct']]
        colors = ['#d32f2f', '#f57c00', OR_GOLD, OR_GREEN]

        fig = go.Figure(data=[
            go.Bar(x=levels, y=values, marker_color=colors, text=[f"{v:.1f}%" for v in values], textposition='outside')
        ])
        fig.update_layout(
            title=f"OSAS {subject} Proficiency - {district} - Grade {grade} ({year})",
            yaxis_title="Percentage",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Proficient rate
        proficient_rate = row['level_3_pct'] + row['level_4_pct']
        st.metric(
            "Proficiency Rate (Level 3+4)",
            f"{proficient_rate:.1f}%",
            help="Percentage of students meeting or exceeding standards"
        )

def render_export(elpa_df, osas_df, districts_df):
    """Render data export page."""
    st.header("Export Data")

    st.markdown("Download assessment data for further analysis.")

    # District filter
    district = st.selectbox(
        "Select District (or All)",
        options=["All Districts"] + districts_df['district_name'].tolist()
    )

    year = st.selectbox("Select Year", options=[2025, 2024])

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("ELPA Data")
        if district == "All Districts":
            export_elpa = elpa_df[elpa_df['year'] == year]
        else:
            district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
            export_elpa = elpa_df[(elpa_df['district_id'] == district_id) & (elpa_df['year'] == year)]

        st.dataframe(export_elpa, use_container_width=True, hide_index=True)

        csv_elpa = export_elpa.to_csv(index=False)
        st.download_button(
            "Download ELPA CSV",
            csv_elpa,
            f"vera_or_elpa_{year}.csv",
            "text/csv",
            use_container_width=True
        )

    with col2:
        st.subheader("OSAS Data")
        if district == "All Districts":
            export_osas = osas_df[osas_df['year'] == year]
        else:
            district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
            export_osas = osas_df[(osas_df['district_id'] == district_id) & (osas_df['year'] == year)]

        st.dataframe(export_osas, use_container_width=True, hide_index=True)

        csv_osas = export_osas.to_csv(index=False)
        st.download_button(
            "Download OSAS CSV",
            csv_osas,
            f"vera_or_osas_{year}.csv",
            "text/csv",
            use_container_width=True
        )

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.set_page_config(
        page_title="VERA-OR | Oregon Type 4 Detection",
        page_icon="🌲",
        layout="wide"
    )

    # Custom CSS
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: #fafafa;
        }}
        .block-container {{
            padding-top: 2rem;
        }}
        h1, h2, h3 {{
            color: {OR_BLUE};
        }}
        .stButton > button {{
            background-color: {OR_BLUE};
            color: white;
        }}
        .stButton > button:hover {{
            background-color: {OR_GREEN};
            color: white;
        }}
    </style>
    """, unsafe_allow_html=True)

    # Authentication
    # Load data
    districts_df = load_districts()
    elpa_df = load_elpa_data()
    osas_df = load_osas_data()

    # Sidebar
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: {OR_BLUE}; margin: 0;">VERA-OR</h2>
        <p style="color: #666; font-size: 0.85rem; margin-top: 5px;">Oregon Implementation</p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigation",
        ["Overview", "ELPA Analysis", "Type 4 Detection", "OSAS Analysis", "Export Data"]
    )

    st.sidebar.divider()

    st.sidebar.markdown("""
    **Data Sources:**
    - ELPA (English Language Proficiency)
    - OSAS (Oregon Statewide Assessment)

    **Type 4 Detection:**
    - Speaking vs Writing delta
    - Flag threshold: > 8 points

    ---

    [H-EDU.Solutions](https://h-edu.solutions)
    """)

    # Render selected page
    if page == "Overview":
        render_overview(districts_df, elpa_df, osas_df)
    elif page == "ELPA Analysis":
        render_elpa_analysis(elpa_df, districts_df)
    elif page == "Type 4 Detection":
        render_type4_detection(elpa_df, districts_df)
    elif page == "OSAS Analysis":
        render_osas_analysis(osas_df, districts_df)
    elif page == "Export Data":
        render_export(elpa_df, osas_df, districts_df)

if __name__ == "__main__":
    main()
