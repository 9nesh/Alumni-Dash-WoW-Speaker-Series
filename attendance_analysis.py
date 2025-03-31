import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import io
import base64
from utils import generate_insights, get_session_colors, create_download_link

def run_attendance_analysis(all_sheets):
    """
    Run all attendance and engagement analyses
    """
    st.markdown("<h2 class='sub-header'>Attendance & Engagement Analysis</h2>", unsafe_allow_html=True)
    
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Cross-Session Attendance", "Attendance by Constituency", 
        "Greek Affiliation", "Graduation Decade", "Engagement Score",
        "Geographic Distribution", "Major Field Study"
    ])
    
    with tab1:
        attendance_overlap_analysis(all_sheets)
    
    with tab2:
        attendance_by_constituency(all_sheets)
    
    with tab3:
        greek_affiliation_analysis(all_sheets)
    
    with tab4:
        attendance_by_decade(all_sheets)
    
    with tab5:
        engagement_score_analysis(all_sheets)
    
    with tab6:
        geographic_distribution(all_sheets)
    
    with tab7:
        major_field_correlation(all_sheets)

def attendance_overlap_analysis(all_sheets):
    """Implement Cross-Session Attendance Patterns analysis"""
    st.markdown("<h3 class='section-header'>Cross-Session Attendance Patterns</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis identifies individuals who attended multiple speaker sessions and analyzes 
    which combinations of sessions were most common.
    """)
    
    # Create sets of attendees for each session
    attendee_sets = {}
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() != 'sheet7':  # Skip empty sheet
            attendee_sets[sheet_name] = set(df['ID'].astype(str))
    
    # Calculate overlap metrics
    total_unique = set().union(*attendee_sets.values()) if attendee_sets else set()
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    
    # Calculate total attendees (may include duplicates)
    total_attendees = sum(len(attendee_set) for attendee_set in attendee_sets.values())
    
    # Calculate the number of people who attended multiple sessions
    multi_session_attendees = total_attendees - len(total_unique)
    
    # Calculate percentage of repeat attendees
    repeat_percentage = (multi_session_attendees / len(total_unique) * 100) if len(total_unique) > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{len(total_unique)}</div>
            <div class='metric-label'>Unique Attendees</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{multi_session_attendees}</div>
            <div class='metric-label'>Multi-Session Attendees</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{repeat_percentage:.1f}%</div>
            <div class='metric-label'>Repeat Attendance Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ------------------- Overlap Matrix -------------------
    st.subheader("Session Attendance Overlap")
    
    # Create overlap matrix
    overlap_data = []
    session_names = list(attendee_sets.keys())
    
    for session1 in session_names:
        row = []
        for session2 in session_names:
            if session1 == session2:
                overlap = len(attendee_sets[session1])
            else:
                overlap = len(attendee_sets[session1].intersection(attendee_sets[session2]))
            row.append(overlap)
        overlap_data.append(row)
    
    # Create heatmap with plotly
    fig = px.imshow(
        overlap_data,
        x=session_names,
        y=session_names,
        color_continuous_scale='blues',
        labels=dict(x="Session", y="Session", color="Attendees"),
        title="Session Attendance Overlap Matrix"
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Attendance Patterns -------------------
    st.subheader("Multi-Session Attendance Patterns")
    
    # Get attendees who attended multiple sessions
    attendance_count = {}
    for attendee in total_unique:
        attendance_count[attendee] = 0
        for session in attendee_sets:
            if attendee in attendee_sets[session]:
                attendance_count[attendee] += 1
    
    # Count attendees by number of sessions attended
    sessions_attended = {}
    for attendee, count in attendance_count.items():
        if count not in sessions_attended:
            sessions_attended[count] = 0
        sessions_attended[count] += 1
    
    # Convert to DataFrame for charting
    patterns_df = pd.DataFrame([
        {"Sessions Attended": k, "Attendee Count": v} 
        for k, v in sorted(sessions_attended.items())
    ])
    
    # Create bar chart
    fig = px.bar(
        patterns_df,
        x="Sessions Attended",
        y="Attendee Count",
        color="Attendee Count",
        color_continuous_scale='blues',
        title="Number of Attendees by Sessions Attended"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Top Session Combinations -------------------
    st.subheader("Top Session Combinations")
    
    # Find all combinations of sessions that people attended
    session_combinations = []
    for attendee in total_unique:
        attended_sessions = []
        for session in session_names:
            if attendee in attendee_sets[session]:
                attended_sessions.append(session)
        
        if len(attended_sessions) > 1:  # Only interested in combinations
            session_combinations.append(tuple(sorted(attended_sessions)))
    
    # Count frequency of each combination
    from collections import Counter
    combination_counts = Counter(session_combinations)
    
    # Convert to DataFrame
    top_combos = pd.DataFrame([
        {"Combination": " + ".join(combo), "Count": count, "Sessions": len(combo)}
        for combo, count in combination_counts.most_common(10)  # Top 10 combinations
    ])
    
    if not top_combos.empty:
        # Create bar chart for top combinations
        fig = px.bar(
            top_combos,
            x="Count",
            y="Combination",
            color="Sessions",
            color_continuous_scale='blues',
            title="Top 10 Session Combinations",
            orientation='h'
        )
        
        fig.update_layout(
            height=500,
            yaxis={'categoryorder':'total ascending'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No attendees participated in multiple sessions.")
    
    # ------------------- Attendee Overlap Download -------------------
    st.subheader("Download Attendee Overlap Data")
    
    # Create a DataFrame with all attendees and which sessions they attended
    overlap_records = []
    
    for attendee in total_unique:
        record = {"Attendee ID": attendee, "Sessions Attended": 0}
        
        for session in session_names:
            # Add a column for each session with 1 if attended, 0 if not
            record[session] = 1 if attendee in attendee_sets[session] else 0
            if record[session] == 1:
                record["Sessions Attended"] += 1
        
        overlap_records.append(record)
    
    overlap_df = pd.DataFrame(overlap_records)
    
    # Add a filter to only show attendees who went to multiple sessions
    show_multi_only = st.checkbox("Show only multi-session attendees")
    
    if show_multi_only:
        filtered_df = overlap_df[overlap_df["Sessions Attended"] > 1]
    else:
        filtered_df = overlap_df
    
    # Display the DataFrame with pagination
    st.dataframe(filtered_df)
    
    # Create download link
    st.markdown(
        create_download_link(filtered_df, "wow_series_attendance_overlap.csv", "Download Attendee Overlap Data"),
        unsafe_allow_html=True
    )
    
    # ------------------- Insights -------------------
    # Find highest overlap
    highest_overlap_value = 0
    highest_overlap_pair = ("", "")
    
    for i, session1 in enumerate(session_names):
        for j, session2 in enumerate(session_names):
            if i != j:
                overlap = len(attendee_sets[session1].intersection(attendee_sets[session2]))
                if overlap > highest_overlap_value:
                    highest_overlap_value = overlap
                    highest_overlap_pair = (session1, session2)
    
    # Calculate how many people attended all sessions
    all_sessions_attendees = set.intersection(*attendee_sets.values()) if attendee_sets else set()
    all_sessions_count = len(all_sessions_attendees)
    
    # Calculate how many attended only one session
    single_session_count = sum(1 for _, count in attendance_count.items() if count == 1)
    single_session_percentage = (single_session_count / len(total_unique) * 100) if len(total_unique) > 0 else 0
    
    # Generate insights
    insights = {
        "Highest overlap": f"{highest_overlap_pair[0]} and {highest_overlap_pair[1]} share {highest_overlap_value} attendees",
        "Most loyal attendees": f"{all_sessions_count} people attended all {len(session_names)} sessions",
        "Single session attendees": f"{single_session_percentage:.1f}% ({single_session_count} people) only attended one session"
    }
    
    st.markdown(generate_insights(insights), unsafe_allow_html=True)
    
    # ------------------- Recommendations -------------------
    st.subheader("Recommendations")
    
    st.markdown("""
    1. **Target Multi-Session Attendees**: Create special engagement opportunities for the most loyal attendees who participate in multiple sessions.
    
    2. **Combination Marketing**: Promote session combinations that historically have high overlap when marketing future events.
    
    3. **Follow-up Strategy**: Develop different follow-up strategies for single-session versus multi-session attendees.
    
    4. **Cross-Promotion**: Use the overlap data to identify which future sessions to cross-promote to attendees of a specific session.
    """)

def attendance_by_constituency(all_sheets):
    """Analyze attendance by constituency code"""
    st.markdown("<h3 class='section-header'>Attendance by Constituency</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis compares the distribution of constituency codes (alumni, faculty/staff, etc.) 
    across different speaker sessions to identify which sessions attracted which audience segments.
    """)
    
    # Check if constituency data exists
    has_constituency = all(
        'Constituency Code' in df.columns 
        for name, df in all_sheets.items() 
        if name.lower() != 'sheet7'
    )
    
    if not has_constituency:
        st.error("Constituency Code column not found in one or more sheets. Unable to perform analysis.")
        return
    
    # Extract constituency data from each session
    constituency_data = {}
    session_totals = {}
    all_constituencies = set()
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() == 'sheet7':  # Skip empty sheet
            continue
        
        # Count attendees by constituency
        if 'Constituency Code' in df.columns:
            constituency_counts = df['Constituency Code'].fillna('Unknown').value_counts()
            constituency_data[sheet_name] = constituency_counts
            session_totals[sheet_name] = len(df)
            all_constituencies.update(constituency_counts.index)
    
    # Create a standardized DataFrame for plotting
    plot_data = []
    
    for session, counts in constituency_data.items():
        total = session_totals[session]
        for constituency in all_constituencies:
            count = counts.get(constituency, 0)
            percentage = (count / total * 100) if total > 0 else 0
            plot_data.append({
                'Session': session,
                'Constituency': constituency,
                'Count': count,
                'Percentage': percentage
            })
    
    plot_df = pd.DataFrame(plot_data)
    
    # ------------------- Session Composition -------------------
    st.subheader("Session Composition by Constituency")
    
    # Create a stacked bar chart showing percentage breakdown
    fig = px.bar(
        plot_df,
        x='Session',
        y='Percentage',
        color='Constituency',
        title='Constituency Breakdown by Session (%)',
        labels={'Percentage': 'Percentage of Attendees', 'Session': 'Session Name'},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600,
        barmode='stack',
        yaxis_title='Percentage of Attendees (%)',
        legend_title='Constituency'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Constituency Distribution -------------------
    st.subheader("Constituency Distribution Across Sessions")
    
    # Create a grouped bar chart showing absolute counts
    fig = px.bar(
        plot_df,
        x='Constituency',
        y='Count',
        color='Session',
        title='Constituency Distribution Across Sessions (Count)',
        barmode='group',
        labels={'Count': 'Number of Attendees', 'Constituency': 'Constituency Type'},
        color_discrete_map=get_session_colors()
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600,
        yaxis_title='Number of Attendees',
        legend_title='Session'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Relative Constituency Attraction -------------------
    st.subheader("Constituency Attraction Index")
    
    # Calculate a relative attraction index
    # For each constituency, how much more/less likely is it to be in each session compared to overall distribution?
    
    # First, calculate the overall distribution
    overall_counts = plot_df.groupby('Constituency')['Count'].sum()
    overall_total = overall_counts.sum()
    overall_percentages = (overall_counts / overall_total * 100) if overall_total > 0 else 0
    
    # Calculate the attraction index
    attraction_data = []
    
    for session, counts in constituency_data.items():
        session_total = session_totals[session]
        
        for constituency in all_constituencies:
            constituency_count = counts.get(constituency, 0)
            constituency_pct = (constituency_count / session_total * 100) if session_total > 0 else 0
            overall_pct = overall_percentages.get(constituency, 0)
            
            # Attraction index: how much more/less represented is this constituency in this session
            # A value of 1.0 means it's represented at the expected rate
            # >1.0 means over-represented, <1.0 means under-represented
            attraction_index = (constituency_pct / overall_pct) if overall_pct > 0 else 0
            
            attraction_data.append({
                'Session': session,
                'Constituency': constituency,
                'Attraction Index': attraction_index
            })
    
    attraction_df = pd.DataFrame(attraction_data)
    
    # Create a heatmap
    fig = px.imshow(
        attraction_df.pivot(index='Constituency', columns='Session', values='Attraction Index'),
        color_continuous_scale='RdBu_r',
        labels=dict(x="Session", y="Constituency", color="Attraction Index"),
        title="Constituency Attraction Index (>1: Over-represented, <1: Under-represented)",
        range_color=[0, 2]  # 0 to 2 range to make 1.0 the midpoint
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Explanation
    st.markdown("""
    **Understanding the Attraction Index:**
    - **Attraction Index = 1.0**: The constituency is represented at the expected rate
    - **Attraction Index > 1.0**: The constituency is over-represented in this session
    - **Attraction Index < 1.0**: The constituency is under-represented in this session
    - **Example**: An index of 2.0 means this constituency is twice as likely to attend this session compared to the overall average
    """)
    
    # ------------------- Constituency Data Download -------------------
    st.subheader("Constituency Data")
    
    # Pivot and display the data in tabular form
    pivot_df = plot_df.pivot_table(
        index='Constituency',
        columns='Session',
        values='Count',
        aggfunc='sum',
        fill_value=0
    )
    
    # Add totals row and column
    pivot_df['Total'] = pivot_df.sum(axis=1)
    pivot_df.loc['Total'] = pivot_df.sum()
    
    # Display the table
    st.dataframe(pivot_df)
    
    # Create download link
    st.markdown(
        create_download_link(pivot_df.reset_index(), "constituency_data.csv", "Download Constituency Data"),
        unsafe_allow_html=True
    )
    
    # ------------------- Insights -------------------
    # Find most common constituency overall
    most_common = overall_counts.idxmax()
    most_common_percent = (overall_counts[most_common] / overall_total * 100) if overall_total > 0 else 0
    
    # Find session with most diverse constituency mix
    session_diversity = {}
    for session, counts in constituency_data.items():
        # Calculate Shannon diversity index
        proportions = counts / counts.sum()
        diversity = -sum(p * np.log(p) for p in proportions if p > 0)
        session_diversity[session] = diversity
    
    most_diverse_session = max(session_diversity.items(), key=lambda x: x[1])[0] if session_diversity else "None"
    
    # Find session that attracted most unique constituencies
    unique_counts = {session: len(counts) for session, counts in constituency_data.items()}
    most_unique_session = max(unique_counts.items(), key=lambda x: x[1])[0] if unique_counts else "None"
    
    # Find highest attraction index
    if not attraction_df.empty:
        max_attraction = attraction_df.loc[attraction_df['Attraction Index'].idxmax()]
        max_attraction_session = max_attraction['Session']
        max_attraction_constituency = max_attraction['Constituency']
        max_attraction_value = max_attraction['Attraction Index']
    else:
        max_attraction_session = "None"
        max_attraction_constituency = "None"
        max_attraction_value = 0
    
    # Generate insights
    insights = {
        "Primary audience": f"{most_common} made up {most_common_percent:.1f}% of all attendees",
        "Most diverse session": f"{most_diverse_session} had the most balanced constituency mix",
        "Strongest constituency affinity": f"{max_attraction_constituency} was {max_attraction_value:.1f}x more likely to attend {max_attraction_session}"
    }
    
    st.markdown(generate_insights(insights), unsafe_allow_html=True)
    
    # ------------------- Recommendations -------------------
    st.subheader("Recommendations")
    
    st.markdown("""
    1. **Targeted Marketing**: Use constituency affinity data to target specific groups for similar future events.
    
    2. **Content Strategy**: Develop content that appeals to constituencies most interested in each type of session.
    
    3. **Diversification**: For sessions with low diversity, develop strategies to attract a broader audience.
    
    4. **Expansion Opportunities**: Identify constituencies with low overall attendance that could be targeted for growth.
    
    5. **ROI Optimization**: Focus engagement resources on constituencies that show the highest attendance and giving potential.
    """)

def greek_affiliation_analysis(all_sheets):
    """Analyze attendance patterns by Greek affiliation"""
    st.markdown("<h3 class='section-header'>Greek Affiliation Analysis</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis examines whether certain speaker sessions attracted more attendees from specific Greek organizations 
    and if there are patterns in which sororities/fraternities attend which types of events.
    """)
    
    # Check if Greek affiliation data exists
    has_greek = any(
        'Greek Affiliation' in df.columns 
        for name, df in all_sheets.items() 
        if name.lower() != 'sheet7'
    )
    
    if not has_greek:
        st.error("Greek Affiliation column not found in any sheets. Unable to perform analysis.")
        return
    
    # Extract Greek affiliation data from each session
    greek_data = {}
    session_totals = {}
    all_greek_orgs = set()
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() == 'sheet7':  # Skip empty sheet
            continue
        
        # Skip sheets without Greek Affiliation column
        if 'Greek Affiliation' not in df.columns:
            continue
        
        # Count attendees by Greek affiliation
        greek_counts = df['Greek Affiliation'].fillna('Non-Greek').value_counts()
        greek_data[sheet_name] = greek_counts
        session_totals[sheet_name] = len(df)
        all_greek_orgs.update(greek_counts.index)
    
    # If no sessions had Greek data
    if not greek_data:
        st.error("No usable Greek Affiliation data found in any sheets. Unable to perform analysis.")
        return
    
    # ------------------- Greek Affiliation Overview -------------------
    st.subheader("Greek Affiliation Overview")
    
    # Create metrics cards
    col1, col2, col3 = st.columns(3)
    
    # Total Greek-affiliated attendees
    total_attendees = sum(session_totals.values())
    
    # Count total Greek affiliates
    total_greek = 0
    for _, counts in greek_data.items():
        for org, count in counts.items():
            if org != 'Non-Greek':
                total_greek += count
                
    # Calculate Greek percentage
    greek_percentage = (total_greek / total_attendees * 100) if total_attendees > 0 else 0
    
    # Count unique Greek organizations
    unique_orgs = len([org for org in all_greek_orgs if org != 'Non-Greek'])
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{total_greek}</div>
            <div class='metric-label'>Greek-Affiliated Attendees</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{greek_percentage:.1f}%</div>
            <div class='metric-label'>Greek Affiliation Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{unique_orgs}</div>
            <div class='metric-label'>Unique Greek Organizations</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ------------------- Greek vs Non-Greek by Session -------------------
    st.subheader("Greek vs. Non-Greek Attendance by Session")
    
    # Prepare data for Greek vs Non-Greek comparison
    greek_nongreek_data = []
    
    for session, counts in greek_data.items():
        total = session_totals[session]
        
        # Count Greek affiliates
        greek_count = sum(count for org, count in counts.items() if org != 'Non-Greek')
        nongreek_count = counts.get('Non-Greek', 0)
        
        # Add data
        greek_nongreek_data.append({
            'Session': session,
            'Affiliation': 'Greek',
            'Count': greek_count,
            'Percentage': (greek_count / total * 100) if total > 0 else 0
        })
        
        greek_nongreek_data.append({
            'Session': session,
            'Affiliation': 'Non-Greek',
            'Count': nongreek_count,
            'Percentage': (nongreek_count / total * 100) if total > 0 else 0
        })
    
    greek_nongreek_df = pd.DataFrame(greek_nongreek_data)
    
    # Create a stacked bar chart showing the breakdown
    fig = px.bar(
        greek_nongreek_df,
        x='Session',
        y='Percentage',
        color='Affiliation',
        title='Greek vs. Non-Greek Attendance by Session (%)',
        labels={'Percentage': 'Percentage of Attendees', 'Session': 'Session Name'},
        color_discrete_sequence=['#3B82F6', '#D1D5DB']  # Blue for Greek, Gray for Non-Greek
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        barmode='stack',
        yaxis_title='Percentage of Attendees (%)',
        legend_title='Affiliation'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Top Greek Organizations -------------------
    st.subheader("Top Greek Organizations Across All Sessions")
    
    # Aggregate data across all sessions
    org_totals = {}
    
    for session, counts in greek_data.items():
        for org, count in counts.items():
            if org != 'Non-Greek':
                if org not in org_totals:
                    org_totals[org] = 0
                org_totals[org] += count
    
    # Convert to DataFrame for charting
    org_df = pd.DataFrame([
        {"Organization": org, "Attendees": count}
        for org, count in sorted(org_totals.items(), key=lambda x: x[1], reverse=True)
        if org != 'Non-Greek'
    ])
    
    # Only show top 15 to keep chart readable
    top_org_df = org_df.head(15) if len(org_df) > 15 else org_df
    
    if not top_org_df.empty:
        # Create horizontal bar chart
        fig = px.bar(
            top_org_df,
            y='Organization',
            x='Attendees',
            color='Attendees',
            color_continuous_scale='blues',
            title=f'Top {len(top_org_df)} Greek Organizations by Attendance',
            orientation='h'
        )
        
        fig.update_layout(
            height=max(400, len(top_org_df) * 25),  # Scale height based on number of orgs
            yaxis={'categoryorder':'total ascending'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No Greek organization data available.")
    
    # ------------------- Sorority/Fraternity Analysis -------------------
    st.subheader("Sorority vs. Fraternity Attendance")
    
    # Try to categorize Greek organizations as sororities or fraternities
    sorority_keywords = ['sorority', 'sigma', 'kappa', 'alpha', 'delta', 'gamma', 'phi', 'chi', 'omega', 'pi', 'theta']
    fraternity_keywords = ['fraternity', 'tau', 'phi', 'kappa', 'alpha', 'delta', 'gamma', 'sigma', 'omega', 'pi', 'theta']
    
    # Function to categorize Greek organizations
    def categorize_greek_org(org_name):
        if pd.isna(org_name) or org_name == 'Non-Greek':
            return 'Non-Greek'
        
        org_lower = org_name.lower()
        
        if 'sorority' in org_lower:
            return 'Sorority'
        elif 'fraternity' in org_lower:
            return 'Fraternity'
        else:
            # Try to guess based on typical naming patterns
            if any(keyword in org_lower for keyword in sorority_keywords) and 'sorority' in org_lower:
                return 'Sorority'
            elif any(keyword in org_lower for keyword in fraternity_keywords) and 'fraternity' in org_lower:
                return 'Fraternity'
            else:
                return 'Unknown Greek'
    
    # Prepare data for sorority/fraternity comparison
    greek_type_data = []
    
    for session, counts in greek_data.items():
        total = session_totals[session]
        
        # Track counts by type
        type_counts = {'Sorority': 0, 'Fraternity': 0, 'Unknown Greek': 0, 'Non-Greek': 0}
        
        for org, count in counts.items():
            org_type = categorize_greek_org(org)
            type_counts[org_type] += count
        
        # Add data for each type
        for org_type, count in type_counts.items():
            if org_type != 'Non-Greek':  # Skip Non-Greek for this chart
                greek_type_data.append({
                    'Session': session,
                    'Organization Type': org_type,
                    'Count': count,
                    'Percentage': (count / total * 100) if total > 0 else 0
                })
    
    greek_type_df = pd.DataFrame(greek_type_data)
    
    if not greek_type_df.empty:
        # Create a grouped bar chart
        fig = px.bar(
            greek_type_df,
            x='Session',
            y='Count',
            color='Organization Type',
            title='Sorority vs. Fraternity Attendance by Session',
            barmode='group',
            color_discrete_sequence=['#F472B6', '#60A5FA', '#9CA3AF']  # Pink, Blue, Gray
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            yaxis_title='Number of Attendees',
            legend_title='Organization Type'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Greek Organization Preference by Session -------------------
    st.subheader("Greek Organization Preference by Session")
    
    # Create a standardized DataFrame for plotting
    plot_data = []
    
    for session, counts in greek_data.items():
        total = session_totals[session]
        
        # Include only the top 5 Greek organizations for readability
        top_orgs = [org for org, _ in counts.items() if org != 'Non-Greek']
        top_orgs = sorted(top_orgs, key=lambda x: counts[x], reverse=True)[:5]
        
        for org in top_orgs:
            count = counts.get(org, 0)
            plot_data.append({
                'Session': session,
                'Greek Organization': org,
                'Count': count,
                'Percentage': (count / total * 100) if total > 0 else 0
            })
    
    plot_df = pd.DataFrame(plot_data)
    
    if not plot_df.empty:
        # Create a heatmap
        pivot_df = plot_df.pivot_table(
            index='Greek Organization',
            columns='Session',
            values='Percentage',
            fill_value=0
        )
        
        fig = px.imshow(
            pivot_df,
            color_continuous_scale='blues',
            labels=dict(x="Session", y="Greek Organization", color="Percentage"),
            title="Top Greek Organizations Preference by Session (%)"
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=max(400, len(pivot_df) * 30)  # Scale height based on number of orgs
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Greek Data Download -------------------
    st.subheader("Greek Affiliation Data")
    
    # Prepare full data for download
    all_data = []
    
    for session, counts in greek_data.items():
        for org, count in counts.items():
            org_type = categorize_greek_org(org)
            percentage = (count / session_totals[session] * 100) if session_totals[session] > 0 else 0
            
            all_data.append({
                'Session': session,
                'Greek Organization': org,
                'Organization Type': org_type,
                'Count': count,
                'Percentage': percentage
            })
    
    all_data_df = pd.DataFrame(all_data)
    
    # Display the DataFrame
    st.dataframe(all_data_df)
    
    # Create download link
    st.markdown(
        create_download_link(all_data_df, "greek_affiliation_data.csv", "Download Greek Affiliation Data"),
        unsafe_allow_html=True
    )
    
    # ------------------- Insights -------------------
    # Find session with highest Greek participation
    session_greek_pct = {}
    for session, counts in greek_data.items():
        greek_count = sum(count for org, count in counts.items() if org != 'Non-Greek')
        total = session_totals[session]
        session_greek_pct[session] = (greek_count / total * 100) if total > 0 else 0
    
    highest_greek_session = max(session_greek_pct.items(), key=lambda x: x[1]) if session_greek_pct else ("None", 0)
    
    # Find most represented Greek organization
    most_represented_org = max(org_totals.items(), key=lambda x: x[1]) if org_totals else ("None", 0)
    
    # Calculate sorority vs fraternity overall ratio
    sorority_count = 0
    fraternity_count = 0
    
    for session, counts in greek_data.items():
        for org, count in counts.items():
            org_type = categorize_greek_org(org)
            if org_type == 'Sorority':
                sorority_count += count
            elif org_type == 'Fraternity':
                fraternity_count += count
    
    sorority_fraternity_ratio = sorority_count / fraternity_count if fraternity_count > 0 else 0
    
    # Generate insights
    insights = {
        "Highest Greek participation": f"{highest_greek_session[0]} had {highest_greek_session[1]:.1f}% Greek-affiliated attendees",
        "Most represented organization": f"{most_represented_org[0]} had {most_represented_org[1]} attendees across all sessions",
        "Sorority to fraternity ratio": f"{sorority_fraternity_ratio:.1f}:1 (sororities to fraternities)"
    }
    
    st.markdown(generate_insights(insights), unsafe_allow_html=True)
    
    # ------------------- Recommendations -------------------
    st.subheader("Recommendations")
    
    st.markdown("""
    1. **Greek Network Activation**: Leverage the most engaged Greek organizations as ambassadors for future events.
    
    2. **Targeted Content**: Create content that appeals specifically to sororities or fraternities based on their attendance patterns.
    
    3. **Greek Leadership Focus**: For sessions with low Greek attendance, engage Greek leadership to increase participation.
    
    4. **Inter-Greek Outreach**: Identify which Greek organizations rarely attend events and develop specific outreach strategies.
    
    5. **Cross-Promotion**: Use insights about which organizations attend which sessions to inform cross-promotional opportunities.
    """)

def attendance_by_decade(all_sheets):
    """Analyze attendance patterns by graduation decade"""
    st.markdown("<h3 class='section-header'>Attendance by Graduation Decade</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis groups attendees by their graduation decade and examines which sessions appealed more 
    to recent graduates versus older alumni.
    """)
    
    # Check if class year data exists
    has_class_year = all(
        'CL YR' in df.columns 
        for name, df in all_sheets.items() 
        if name.lower() != 'sheet7'
    )
    
    if not has_class_year:
        st.error("Class Year (CL YR) column not found in one or more sheets. Unable to perform analysis.")
        return
    
    # Function to convert class year to decade
    def get_decade(year):
        """Convert class year to decade"""
        if pd.isna(year):
            return "Unknown"
        
        try:
            # The data shows years are numeric (e.g., 1983.0, 2012.0)
            # Convert to integer by rounding down
            year_int = int(year)
            
            if year_int < 1950:
                return "Pre-1950s"
            elif year_int >= 2020:
                return "2020s"
            else:
                # Get the decade (1980, 1990, etc.)
                decade = (year_int // 10) * 10
                return f"{decade}s"
        except (ValueError, TypeError):
            # If conversion fails, try string parsing as fallback
            year_str = str(year).strip()
            
            # If it's a 4-digit year (e.g., "1985")
            if year_str.isdigit() and len(year_str) == 4:
                year_int = int(year_str)
                if year_int < 1950:
                    return "Pre-1950s"
                elif year_int >= 2020:
                    return "2020s"
                else:
                    decade = (year_int // 10) * 10
                    return f"{decade}s"
            # If it's a 2-digit year (e.g., "85" for 1985)
            elif year_str.isdigit() and len(year_str) == 2:
                year_int = int(year_str)
                if year_int >= 50:  # Assuming 50-99 is 1950-1999
                    decade = 1900 + (year_int // 10) * 10
                    return f"{decade}s"
                else:  # Assuming 00-49 is 2000-2049
                    decade = 2000 + (year_int // 10) * 10
                    return f"{decade}s"
        
        # If all parsing attempts fail
        return "Unknown"
    
    # Extract decade data from each session
    decade_data = {}
    session_totals = {}
    all_decades = set()
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() == 'sheet7':  # Skip empty sheet
            continue
        
        # # Let's inspect a few class year values to debug
        # if 'CL YR' in df.columns:
        #     sample_years = df['CL YR'].head(5).tolist()
        #     st.write(f"Debug: Sample class years from {sheet_name}: {sample_years}")
        
        # Convert class years to decades
        df['Decade'] = df['CL YR'].apply(get_decade)
        
        # Count attendees by decade
        decade_counts = df['Decade'].value_counts()
        decade_data[sheet_name] = decade_counts
        session_totals[sheet_name] = len(df)
        all_decades.update(decade_counts.index)
    
    # Sort decades chronologically
    decade_order = [
        "Pre-1950s", "1950s", "1960s", "1970s", "1980s", 
        "1990s", "2000s", "2010s", "2020s", "Unknown"
    ]
    sorted_decades = sorted(all_decades, key=lambda x: 
                           decade_order.index(x) if x in decade_order else 999)
    
    # ------------------- Decade Overview Metrics -------------------
    st.subheader("Decade Overview")
    
    # Create metrics for different generations
    col1, col2, col3, col4 = st.columns(4)
    
    # Aggregate all attendees by decade
    all_decade_counts = {}
    for session, counts in decade_data.items():
        for decade, count in counts.items():
            if decade not in all_decade_counts:
                all_decade_counts[decade] = 0
            all_decade_counts[decade] += count
    
    # Calculate generational groups
    recent_grads = sum(all_decade_counts.get(d, 0) for d in ["2010s", "2020s"])
    mid_career = sum(all_decade_counts.get(d, 0) for d in ["1990s", "2000s"])
    established = sum(all_decade_counts.get(d, 0) for d in ["1970s", "1980s"])
    senior = sum(all_decade_counts.get(d, 0) for d in ["Pre-1950s", "1950s", "1960s"])
    
    # Total alumni with known decades
    total_known = sum(all_decade_counts.get(d, 0) for d in all_decade_counts if d != "Unknown")
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{recent_grads}</div>
            <div class='metric-label'>Recent Graduates<br/>(2010s-2020s)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{mid_career}</div>
            <div class='metric-label'>Mid-Career Alumni<br/>(1990s-2000s)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{established}</div>
            <div class='metric-label'>Established Alumni<br/>(1970s-1980s)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{senior}</div>
            <div class='metric-label'>Senior Alumni<br/>(Pre-1970s)</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ------------------- Decade Distribution by Session -------------------
    st.subheader("Graduation Decade Distribution by Session")
    
    # Create a standardized DataFrame for plotting
    plot_data = []
    
    for session, counts in decade_data.items():
        total = session_totals[session]
        for decade in sorted_decades:
            count = counts.get(decade, 0)
            percentage = (count / total * 100) if total > 0 else 0
            plot_data.append({
                'Session': session,
                'Decade': decade,
                'Count': count,
                'Percentage': percentage
            })
    
    plot_df = pd.DataFrame(plot_data)
    
    # Create a stacked bar chart showing percentage breakdown
    fig = px.bar(
        plot_df,
        x='Session',
        y='Percentage',
        color='Decade',
        title='Graduation Decade Breakdown by Session (%)',
        labels={'Percentage': 'Percentage of Attendees', 'Session': 'Session Name'},
        color_discrete_sequence=px.colors.qualitative.Bold,
        category_orders={"Decade": sorted_decades}
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600,
        barmode='stack',
        yaxis_title='Percentage of Attendees (%)',
        legend_title='Graduation Decade'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Decade Preference by Session -------------------
    st.subheader("Decade Preference for Sessions")
    
    # Calculate a relative preference index
    # For each decade, how much more/less likely is it to attend each session compared to overall distribution?
    
    # First, calculate the overall distribution
    overall_counts = plot_df.groupby('Decade')['Count'].sum()
    overall_total = overall_counts.sum()
    overall_percentages = (overall_counts / overall_total * 100) if overall_total > 0 else 0
    
    # Calculate the preference index
    preference_data = []
    
    for session, counts in decade_data.items():
        session_total = session_totals[session]
        
        for decade in sorted_decades:
            decade_count = counts.get(decade, 0)
            decade_pct = (decade_count / session_total * 100) if session_total > 0 else 0
            overall_pct = overall_percentages.get(decade, 0)
            
            # Preference index: how much more/less represented is this decade in this session
            # A value of 1.0 means it's represented at the expected rate
            # >1.0 means over-represented, <1.0 means under-represented
            preference_index = (decade_pct / overall_pct) if overall_pct > 0 else 0
            
            preference_data.append({
                'Session': session,
                'Decade': decade,
                'Preference Index': preference_index
            })
    
    preference_df = pd.DataFrame(preference_data)
    
    # Create a heatmap
    # First, create the pivot table and reindex to control row order directly
    pivot_df = preference_df.pivot(index='Decade', columns='Session', values='Preference Index')
    # Reindex to control row order directly
    pivot_df = pivot_df.reindex(sorted_decades)
    
    fig = px.imshow(
        pivot_df,
        color_continuous_scale='RdBu_r',
        labels=dict(x="Session", y="Decade", color="Preference Index"),
        title="Decade Preference Index (>1: Over-represented, <1: Under-represented)",
        range_color=[0, 2]  # 0 to 2 range to make 1.0 the midpoint
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Explanation
    st.markdown("""
    **Understanding the Preference Index:**
    - **Preference Index = 1.0**: The decade is represented at the expected rate
    - **Preference Index > 1.0**: The decade is over-represented in this session
    - **Preference Index < 1.0**: The decade is under-represented in this session
    - **Example**: An index of 2.0 means alumni from this decade are twice as likely to attend this session compared to the overall average
    """)
    
    # ------------------- Generational Analysis -------------------
    st.subheader("Generational Attendance Patterns")
    
    # Group decades into generations
    generation_map = {
        "Pre-1950s": "Senior Alumni (pre-1950s)",
        "1950s": "Senior Alumni (1950-1969)",
        "1960s": "Senior Alumni (1950-1969)",
        "1970s": "Established Alumni (1970-1989)",
        "1980s": "Established Alumni (1970-1989)",
        "1990s": "Mid-Career Alumni (1990-2009)",
        "2000s": "Mid-Career Alumni (1990-2009)",
        "2010s": "Recent Graduates (2010-present)",
        "2020s": "Recent Graduates (2010-present)",
        "Unknown": "Unknown"
    }
    
    # Generation order
    generation_order = ["Recent Graduates (2010-present)", "Mid-Career Alumni (1990-2009)", "Established Alumni (1970-1989)", "Senior Alumni (1950-1969)", "Unknown"]
    
    # Create generation data
    generation_data = []
    
    for session, counts in decade_data.items():
        # Group by generation
        gen_counts = {}
        for decade, count in counts.items():
            generation = generation_map.get(decade, "Unknown")
            if generation not in gen_counts:
                gen_counts[generation] = 0
            gen_counts[generation] += count
        
        # Add to dataset
        total = session_totals[session]
        for generation, count in gen_counts.items():
            percentage = (count / total * 100) if total > 0 else 0
            generation_data.append({
                'Session': session,
                'Generation': generation,
                'Count': count,
                'Percentage': percentage
            })
    
    generation_df = pd.DataFrame(generation_data)
    
    
    # Create a grouped bar chart
    fig = px.bar(
        generation_df,
        x='Session',
        y='Count',
        color='Generation',
        title='Generational Attendance by Session (Count)',
        labels={'Count': 'Number of Attendees', 'Session': 'Session Name'},
        barmode='group',
        color_discrete_sequence=px.colors.qualitative.Bold,
        category_orders={"Generation": generation_order}
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600,
        yaxis_title='Number of Attendees',
        legend_title='Generation'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Data Download -------------------
    st.subheader("Graduation Decade Data")
    
    # Pivot and display the data in tabular form
    pivot_df = plot_df.pivot_table(
        index='Decade',
        columns='Session',
        values='Count',
        aggfunc='sum',
        fill_value=0
    )
    
    # Add totals row and column
    pivot_df['Total'] = pivot_df.sum(axis=1)
    pivot_df.loc['Total'] = pivot_df.sum()
    
    # Reorder rows by decade
    pivot_df = pivot_df.reindex(sorted_decades + ['Total'])
    
    # Display the table
    st.dataframe(pivot_df)
    
    # Create download link
    st.markdown(
        create_download_link(pivot_df.reset_index(), "decade_attendance_data.csv", "Download Decade Attendance Data"),
        unsafe_allow_html=True
    )
    
    # ------------------- Insights -------------------
    # Find most common decade overall with proper error handling
    if not overall_counts.empty:
        if 'Unknown' in overall_counts.index:
            non_unknown_counts = overall_counts.drop('Unknown')
            if not non_unknown_counts.empty:
                most_common_decade = non_unknown_counts.idxmax()
                most_common_percent = (overall_counts[most_common_decade] / overall_total * 100) if overall_total > 0 else 0
            else:
                most_common_decade = "Unknown"
                most_common_percent = 100.0
        else:
            most_common_decade = overall_counts.idxmax()
            most_common_percent = (overall_counts[most_common_decade] / overall_total * 100) if overall_total > 0 else 0
    else:
        most_common_decade = "No data"
        most_common_percent = 0
    
    # Find session with highest recent graduate attendance
    recent_grad_pct = {}
    for session, counts in decade_data.items():
        recent_count = counts.get('2010s', 0) + counts.get('2020s', 0)
        total = session_totals[session]
        recent_grad_pct[session] = (recent_count / total * 100) if total > 0 else 0
    
    highest_recent_session = max(recent_grad_pct.items(), key=lambda x: x[1]) if recent_grad_pct else ("None", 0)
    
    # Find generation with highest variability across sessions - with error handling
    generation_variability = {}
    for generation in generation_order:
        if generation == "Unknown":
            continue
        
        gen_percentages = generation_df[generation_df['Generation'] == generation]['Percentage']
        if not gen_percentages.empty and len(gen_percentages) > 1:  # Need at least 2 values for std
            generation_variability[generation] = gen_percentages.std()
    
    if generation_variability:
        most_variable_gen = max(generation_variability.items(), key=lambda x: x[1])
    else:
        most_variable_gen = ("None", 0)
    
    # Generate insights
    insights = {
        "Primary decade": f"The {most_common_decade} graduates made up {most_common_percent:.1f}% of all attendees",
        "Young alumni attendance": f"{highest_recent_session[0]} had the highest attendance from recent graduates ({highest_recent_session[1]:.1f}%)",
        "Attendance variability": f"{most_variable_gen[0]} showed the most variable attendance patterns across sessions"
    }
    
    st.markdown(generate_insights(insights), unsafe_allow_html=True)
    
    # ------------------- Recommendations -------------------
    st.subheader("Recommendations")
    
    st.markdown("""
    1. **Generational Targeting**: Tailor marketing messages by graduation decade based on which sessions attracted which generations.
    
    2. **Content Development**: Develop session topics that specifically appeal to decades with lower attendance rates.
    
    3. **Cross-Generational Mentoring**: Use popular sessions to create networking opportunities between different graduation decades.
    
    4. **Feedback Collection**: Gather specific feedback from highly engaged decades to better understand their preferences.
    
    5. **Reunion Integration**: Integrate speaker series events into reunion programming for decades showing high interest.
    """)

def engagement_score_analysis(all_sheets):
    """Analyze the relationship between engagement scores and attendance patterns"""
    st.markdown("<h3 class='section-header'>Engagement Score Analysis</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis examines if individuals with higher engagement scores attended more speaker sessions and
    identifies which sessions attracted highly engaged constituents.
    """)
    
    # Check if engagement score data exists
    has_engagement = all(
        'Eng Score' in df.columns 
        for name, df in all_sheets.items() 
        if name.lower() != 'sheet7'
    )
    
    if not has_engagement:
        st.error("Engagement Score (Eng Score) column not found in one or more sheets. Unable to perform analysis.")
        return
    
    # Extract engagement score data from each session
    engagement_data = {}
    session_totals = {}
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() == 'sheet7':  # Skip empty sheet
            continue
        
        # Convert engagement scores to numeric
        df['Eng Score'] = pd.to_numeric(df['Eng Score'], errors='coerce')
        
        # Store engagement scores and totals
        engagement_data[sheet_name] = df['Eng Score'].dropna()
        session_totals[sheet_name] = len(df)
    
    # Create sets of attendees for cross-session analysis
    attendee_sets = {}
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() != 'sheet7':  # Skip empty sheet
            attendee_sets[sheet_name] = set(df['ID'].astype(str))
    
    # ------------------- Engagement Score Overview -------------------
    st.subheader("Engagement Score Overview")
    
    # Create metrics cards
    col1, col2, col3 = st.columns(3)
    
    # Calculate average engagement score across all sessions
    all_scores = []
    for session, scores in engagement_data.items():
        all_scores.extend(scores.tolist())
    
    avg_engagement = np.mean(all_scores) if all_scores else 0
    median_engagement = np.median(all_scores) if all_scores else 0
    
    # Find session with highest average engagement
    session_avg_scores = {session: scores.mean() for session, scores in engagement_data.items() if not scores.empty}
    highest_eng_session = max(session_avg_scores.items(), key=lambda x: x[1]) if session_avg_scores else ("None", 0)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{avg_engagement:.1f}</div>
            <div class='metric-label'>Average Engagement Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{median_engagement:.1f}</div>
            <div class='metric-label'>Median Engagement Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{highest_eng_session[0]}</div>
            <div class='metric-label'>Highest Engagement Session</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ------------------- Engagement Distribution by Session -------------------
    st.subheader("Engagement Score Distribution by Session")
    
    # Calculate quartiles for engagement scores
    def categorize_engagement(score):
        if pd.isna(score):
            return "Unknown"
        elif score <= 25:
            return "Low (0-25)"
        elif score <= 50:
            return "Medium-Low (26-50)"
        elif score <= 75:
            return "Medium-High (51-75)"
        else:
            return "High (76-100)"
    
    # Prepare data for visualization
    engagement_categories = []
    
    for session, scores in engagement_data.items():
        # Calculate for each category
        for score in scores:
            category = categorize_engagement(score)
            engagement_categories.append({
                'Session': session,
                'Engagement Category': category,
                'Score': score
            })
    
    engagement_df = pd.DataFrame(engagement_categories)
    
    # Box plot of engagement scores by session
    fig = px.box(
        engagement_df,
        x='Session',
        y='Score',
        color='Session',
        title='Engagement Score Distribution by Session',
        labels={'Score': 'Engagement Score', 'Session': 'Session Name'},
        color_discrete_map=get_session_colors()
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600,
        yaxis_title='Engagement Score',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Engagement Category Breakdown -------------------
    st.subheader("Engagement Category Breakdown by Session")
    
    # Count attendees by engagement category for each session
    category_counts = engagement_df.groupby(['Session', 'Engagement Category']).size().reset_index(name='Count')
    
    # Calculate percentages
    category_totals = category_counts.groupby('Session')['Count'].sum().reset_index()
    category_counts = category_counts.merge(category_totals, on='Session', suffixes=('', '_Total'))
    category_counts['Percentage'] = (category_counts['Count'] / category_counts['Count_Total'] * 100)
    
    # Category order for consistent display
    category_order = ["High (76-100)", "Medium-High (51-75)", "Medium-Low (26-50)", "Low (0-25)", "Unknown"]
    
    # Create a stacked bar chart
    fig = px.bar(
        category_counts,
        x='Session',
        y='Percentage',
        color='Engagement Category',
        title='Engagement Category Breakdown by Session (%)',
        labels={'Percentage': 'Percentage of Attendees', 'Session': 'Session Name'},
        color_discrete_sequence=px.colors.sequential.Viridis,
        category_orders={"Engagement Category": category_order}
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600,
        barmode='stack',
        yaxis_title='Percentage of Attendees (%)',
        legend_title='Engagement Category'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Multi-Session Attendance vs Engagement -------------------
    st.subheader("Multi-Session Attendance vs Engagement Score")
    
    # Calculate the number of sessions each attendee participated in
    attendance_count = {}
    all_attendees = set()
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() == 'sheet7':  # Skip empty sheet
            continue
            
        for idx, row in df.iterrows():
            attendee_id = str(row['ID'])
            all_attendees.add(attendee_id)
            
            if attendee_id not in attendance_count:
                attendance_count[attendee_id] = 0
            attendance_count[attendee_id] += 1
    
    # Create data for the scatter plot
    engagement_vs_attendance = []
    
    # Gather all engagement scores by attendee
    attendee_engagement = {}
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() == 'sheet7':  # Skip empty sheet
            continue
            
        for idx, row in df.iterrows():
            attendee_id = str(row['ID'])
            if 'Eng Score' in row and not pd.isna(row['Eng Score']):
                attendee_engagement[attendee_id] = row['Eng Score']
    
    # Create scatter plot data
    for attendee_id in all_attendees:
        if attendee_id in attendee_engagement and attendee_id in attendance_count:
            engagement_vs_attendance.append({
                'Attendee ID': attendee_id,
                'Engagement Score': attendee_engagement[attendee_id],
                'Sessions Attended': attendance_count[attendee_id]
            })
    
    attendance_df = pd.DataFrame(engagement_vs_attendance)
    
    if not attendance_df.empty:
        # Average engagement score by number of sessions attended
        avg_by_sessions = attendance_df.groupby('Sessions Attended')['Engagement Score'].mean().reset_index()
        
        # Scatter plot with trend line
        fig = px.scatter(
            attendance_df,
            x='Engagement Score',
            y='Sessions Attended',
            title='Relationship Between Engagement Score and Session Attendance',
            labels={'Engagement Score': 'Engagement Score', 'Sessions Attended': 'Number of Sessions Attended'},
            opacity=0.7,
            marginal_x='histogram',
            marginal_y='histogram'
        )
        
        # Add trend line
        fig.add_trace(
            go.Scatter(
                x=attendance_df['Engagement Score'],
                y=attendance_df['Sessions Attended'],
                mode='markers',
                marker=dict(color='blue', opacity=0.5),
                name='Attendees'
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=avg_by_sessions['Engagement Score'],
                y=avg_by_sessions['Sessions Attended'],
                mode='lines',
                line=dict(color='red', width=3),
                name='Average Trend'
            )
        )
        
        fig.update_layout(
            height=600,
            xaxis_title='Engagement Score',
            yaxis_title='Number of Sessions Attended'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Calculate correlation
        correlation = attendance_df['Engagement Score'].corr(attendance_df['Sessions Attended'])
        st.write(f"**Correlation coefficient**: {correlation:.3f} (Positive values indicate higher engagement scores correlate with attending more sessions)")
    
    # ------------------- Highly Engaged Attendees Analysis -------------------
    st.subheader("Highly Engaged Attendees Analysis")
    
    # Define threshold for "highly engaged"
    engagement_threshold = st.slider("Select engagement score threshold for 'highly engaged':", 0, 100, 75)
    
    # Identify highly engaged attendees and their sessions
    highly_engaged = {}
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() == 'sheet7':  # Skip empty sheet
            continue
            
        # Filter for highly engaged attendees
        high_eng_df = df[df['Eng Score'] >= engagement_threshold]
        
        # Count highly engaged attendees
        highly_engaged[sheet_name] = len(high_eng_df)
    
    # Calculate percentage of highly engaged attendees
    highly_engaged_pct = {
        session: (count / session_totals[session] * 100) if session_totals[session] > 0 else 0
        for session, count in highly_engaged.items()
    }
    
    # Create bar chart
    highly_engaged_df = pd.DataFrame([
        {"Session": session, "Percentage": percentage}
        for session, percentage in highly_engaged_pct.items()
    ])
    
    fig = px.bar(
        highly_engaged_df,
        x='Session',
        y='Percentage',
        color='Percentage',
        title=f'Percentage of Highly Engaged Attendees (Score ≥ {engagement_threshold}) by Session',
        labels={'Percentage': '% of Highly Engaged Attendees', 'Session': 'Session Name'},
        color_continuous_scale='blues'
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        yaxis_title='Percentage of Attendees (%)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Engagement Data Download -------------------
    st.subheader("Engagement Score Data")
    
    # Prepare full data for download
    full_engagement_data = []
    
    for attendee_id in all_attendees:
        if attendee_id in attendee_engagement:
            sessions = []
            for session, attendees in attendee_sets.items():
                if attendee_id in attendees:
                    sessions.append(session)
            
            full_engagement_data.append({
                'Attendee ID': attendee_id,
                'Engagement Score': attendee_engagement[attendee_id],
                'Sessions Attended': attendance_count.get(attendee_id, 0),
                'Session List': ", ".join(sessions)
            })
    
    full_engagement_df = pd.DataFrame(full_engagement_data)
    
    # Display the DataFrame
    st.dataframe(full_engagement_df)
    
    # Create download link
    st.markdown(
        create_download_link(full_engagement_df, "engagement_score_data.csv", "Download Engagement Score Data"),
        unsafe_allow_html=True
    )
    
    # ------------------- Insights -------------------
    # Find session with highest percentage of highly engaged attendees
    highest_engaged_session = max(highly_engaged_pct.items(), key=lambda x: x[1]) if highly_engaged_pct else ("None", 0)
    
    # Find average engagement score of multi-session attendees vs single-session
    multi_session_df = attendance_df[attendance_df['Sessions Attended'] > 1]
    single_session_df = attendance_df[attendance_df['Sessions Attended'] == 1]
    
    multi_session_avg = multi_session_df['Engagement Score'].mean() if not multi_session_df.empty else 0
    single_session_avg = single_session_df['Engagement Score'].mean() if not single_session_df.empty else 0
    
    engagement_diff = multi_session_avg - single_session_avg
    
    # Find attendance gap between high and low engaged attendees
    high_engaged_df = attendance_df[attendance_df['Engagement Score'] >= 75]
    low_engaged_df = attendance_df[attendance_df['Engagement Score'] <= 25]
    
    high_engaged_avg = high_engaged_df['Sessions Attended'].mean() if not high_engaged_df.empty else 0
    low_engaged_avg = low_engaged_df['Sessions Attended'].mean() if not low_engaged_df.empty else 0
    
    attendance_gap = high_engaged_avg - low_engaged_avg
    
    # Generate insights
    insights = {
        "Highly engaged audience": f"{highest_engaged_session[0]} had the highest percentage of highly engaged attendees ({highest_engaged_session[1]:.1f}%)",
        "Multi-session engagement": f"Multi-session attendees average {engagement_diff:.1f} points higher engagement than single-session attendees",
        "Attendance gap": f"Highly engaged individuals attend {attendance_gap:.1f} more sessions on average than low-engaged individuals"
    }
    
    st.markdown(generate_insights(insights), unsafe_allow_html=True)
    
    # ------------------- Recommendations -------------------
    st.subheader("Recommendations")
    
    st.markdown("""
    1. **Targeted Outreach**: Focus marketing for complex or specialized topics on highly engaged constituents who are more likely to attend.
    
    2. **Engagement Escalation**: Develop pathways to increase engagement scores through strategic session attendance.
    
    3. **Giving Strategy**: Coordinate with fundraising team to leverage highly engaged session attendees for giving opportunities.
    
    4. **Content Calibration**: Tailor session content complexity to match the engagement level of the target audience.
    
    5. **Multi-Session Strategy**: Create incentives for attending multiple sessions to increase overall engagement metrics.
    """)

def geographic_distribution(all_sheets):
    """Analyze geographic distribution of attendees"""
    st.markdown("<h3 class='section-header'>Geographic Distribution</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis maps attendee locations by state/region for each session to identify 
    geographic trends and potential locations for future in-person events.
    """)
    
    # Check if geographic data exists
    has_geo = all(
        all(col in df.columns for col in ['State', 'City', 'ZIP'])
        for name, df in all_sheets.items() 
        if name.lower() != 'sheet7'
    )
    
    if not has_geo:
        st.error("Geographic data columns (State, City, ZIP) not found in one or more sheets. Unable to perform analysis.")
        return
    
    # Extract geographic data from each session
    geo_data = {}
    session_totals = {}
    all_states = set()
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() == 'sheet7':  # Skip empty sheet
            continue
        
        # Count attendees by state
        state_counts = df['State'].fillna('Unknown').value_counts()
        geo_data[sheet_name] = state_counts
        session_totals[sheet_name] = len(df)
        all_states.update(state_counts.index)
    
    # ------------------- State Overview -------------------
    st.subheader("State Distribution Overview")
    
    # Create metrics cards
    col1, col2, col3 = st.columns(3)
    
    # Calculate total unique states
    total_states = len([s for s in all_states if s != 'Unknown'])
    
    # Find state with most attendees
    state_totals = {}
    for counts in geo_data.values():
        for state, count in counts.items():
            if state not in state_totals:
                state_totals[state] = 0
            state_totals[state] += count
    
    top_state = max(state_totals.items(), key=lambda x: x[1]) if state_totals else ('Unknown', 0)
    
    # Calculate percentage of in-state vs out-of-state
    # Assuming the institution's state is the most common state
    institution_state = top_state[0]
    total_attendees = sum(state_totals.values())
    in_state_percentage = (state_totals.get(institution_state, 0) / total_attendees * 100) if total_attendees > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{total_states}</div>
            <div class='metric-label'>States Represented</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{top_state[0]}</div>
            <div class='metric-label'>Most Common State</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{in_state_percentage:.1f}%</div>
            <div class='metric-label'>In-State Attendance</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ------------------- State Distribution by Session -------------------
    st.subheader("State Distribution by Session")
    
    # Create a standardized DataFrame for plotting
    plot_data = []
    
    for session, counts in geo_data.items():
        total = session_totals[session]
        for state in all_states:
            count = counts.get(state, 0)
            percentage = (count / total * 100) if total > 0 else 0
            plot_data.append({
                'Session': session,
                'State': state,
                'Count': count,
                'Percentage': percentage
            })
    
    plot_df = pd.DataFrame(plot_data)
    
    # Create a stacked bar chart showing percentage breakdown
    fig = px.bar(
        plot_df,
        x='Session',
        y='Percentage',
        color='State',
        title='State Distribution by Session (%)',
        labels={'Percentage': 'Percentage of Attendees', 'Session': 'Session Name'},
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600,
        barmode='stack',
        yaxis_title='Percentage of Attendees (%)',
        legend_title='State'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Regional Analysis -------------------
    st.subheader("Regional Distribution")
    
    # Define regions
    regions = {
        'Northeast': ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA'],
        'Midwest': ['OH', 'IN', 'IL', 'MI', 'WI', 'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS'],
        'South': ['DE', 'MD', 'DC', 'VA', 'WV', 'NC', 'SC', 'GA', 'FL', 'KY', 'TN', 'AL', 'MS', 'AR', 'LA', 'OK', 'TX'],
        'West': ['MT', 'ID', 'WY', 'CO', 'NM', 'AZ', 'UT', 'NV', 'WA', 'OR', 'CA', 'AK', 'HI']
    }
    
    # Function to get region for a state
    def get_region(state):
        if pd.isna(state) or state == 'Unknown':
            return 'Unknown'
        for region, states in regions.items():
            if state in states:
                return region
        return 'Other'
    
    # Add region to plot data
    plot_df['Region'] = plot_df['State'].apply(get_region)
    
    # Create regional summary
    region_summary = plot_df.groupby(['Session', 'Region'])['Count'].sum().reset_index()
    
    # Calculate percentages
    region_totals = region_summary.groupby('Session')['Count'].sum().reset_index()
    region_summary = region_summary.merge(region_totals, on='Session', suffixes=('', '_Total'))
    region_summary['Percentage'] = (region_summary['Count'] / region_summary['Count_Total'] * 100)
    
    # Create stacked bar chart for regions
    fig = px.bar(
        region_summary,
        x='Session',
        y='Percentage',
        color='Region',
        title='Regional Distribution by Session (%)',
        labels={'Percentage': 'Percentage of Attendees', 'Session': 'Session Name'},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        barmode='stack',
        yaxis_title='Percentage of Attendees (%)',
        legend_title='Region'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- City Analysis -------------------
    st.subheader("Top Cities Analysis")
    
    # Aggregate city data across all sessions
    city_data = {}
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() == 'sheet7':
            continue
            
        # Combine city and state for unique identification
        df['Location'] = df.apply(lambda x: f"{x['City']}, {x['State']}" if pd.notna(x['City']) and pd.notna(x['State']) else "Unknown", axis=1)
        city_counts = df['Location'].value_counts()
        
        for city, count in city_counts.items():
            if city not in city_data:
                city_data[city] = 0
            city_data[city] += count
    
    # Create DataFrame of top cities
    top_cities_df = pd.DataFrame([
        {"Location": city, "Attendees": count}
        for city, count in sorted(city_data.items(), key=lambda x: x[1], reverse=True)
        if city != "Unknown"
    ]).head(15)  # Show top 15 cities
    
    if not top_cities_df.empty:
        # Create horizontal bar chart
        fig = px.bar(
            top_cities_df,
            y='Location',
            x='Attendees',
        color='Attendees',
        color_continuous_scale='blues',
            title='Top 15 Cities by Total Attendance',
            orientation='h'
        )
        
        fig.update_layout(
            height=500,
            yaxis={'categoryorder':'total ascending'}
        )
        
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Geographic Data Download -------------------
    st.subheader("Geographic Distribution Data")
    
    # Prepare full data for download
    full_geo_data = []
    
    for session, df in all_sheets.items():
        if session.lower() == 'sheet7':
            continue
            
        for _, row in df.iterrows():
            location = f"{row['City']}, {row['State']}" if pd.notna(row['City']) and pd.notna(row['State']) else "Unknown"
            region = get_region(row['State']) if pd.notna(row['State']) else "Unknown"
            
            full_geo_data.append({
                'Session': session,
                'City': row['City'] if pd.notna(row['City']) else "Unknown",
                'State': row['State'] if pd.notna(row['State']) else "Unknown",
                'ZIP': row['ZIP'] if pd.notna(row['ZIP']) else "Unknown",
                'Region': region,
                'Location': location
            })
    
    full_geo_df = pd.DataFrame(full_geo_data)
    
    # Display the DataFrame
    st.dataframe(full_geo_df)
    
    # Create download link
    st.markdown(
        create_download_link(full_geo_df, "geographic_distribution_data.csv", "Download Geographic Data"),
        unsafe_allow_html=True
    )
    
    # ------------------- Insights -------------------
    # Find most geographically diverse session
    session_state_counts = {}
    for session, df in all_sheets.items():
        if session.lower() != 'sheet7':
            unique_states = df['State'].nunique()
            session_state_counts[session] = unique_states
    
    most_diverse_session = max(session_state_counts.items(), key=lambda x: x[1]) if session_state_counts else ("None", 0)
    
    # Calculate regional concentration
    primary_region = region_summary.groupby('Region')['Count'].sum().idxmax()
    primary_region_percentage = (region_summary[region_summary['Region'] == primary_region]['Count'].sum() / 
                               region_summary['Count'].sum() * 100)
    
    # Find session with highest out-of-state percentage
    session_out_of_state = {}
    for session, df in all_sheets.items():
        if session.lower() != 'sheet7':
            total = len(df)
            in_state = len(df[df['State'] == institution_state])
            out_of_state_pct = ((total - in_state) / total * 100) if total > 0 else 0
            session_out_of_state[session] = out_of_state_pct
    
    highest_out_of_state = max(session_out_of_state.items(), key=lambda x: x[1]) if session_out_of_state else ("None", 0)
    
    # Generate insights
    insights = {
        "Geographic reach": f"{most_diverse_session[0]} had the widest geographic reach with {most_diverse_session[1]} states represented",
        "Regional concentration": f"{primary_region} region accounts for {primary_region_percentage:.1f}% of all attendees",
        "Out-of-state appeal": f"{highest_out_of_state[0]} had the highest out-of-state attendance at {highest_out_of_state[1]:.1f}%"
    }
    
    st.markdown(generate_insights(insights), unsafe_allow_html=True)
    
    # ------------------- Recommendations -------------------
    st.subheader("Recommendations")
    
    st.markdown("""
    1. **Regional Event Planning**: Consider hosting in-person events in cities with high virtual attendance.
    
    2. **Time Zone Optimization**: Schedule virtual events considering the geographic distribution of attendees.
    
    3. **Local Chapter Engagement**: Leverage locations with high attendance to establish or strengthen local alumni chapters.
    
    4. **Marketing Strategy**: Develop region-specific marketing approaches based on attendance patterns.
    
    5. **Travel Considerations**: For future in-person events, consider travel accessibility from high-attendance regions.
    """)

def major_field_correlation(all_sheets):
    """Analyze if certain speaker topics attracted more attendees from related academic disciplines"""
    st.markdown("<h3 class='section-header'>Major Field of Study Correlation</h3>", unsafe_allow_html=True)
    
    st.write("""
    This analysis examines if certain speaker topics attracted more attendees from related academic disciplines, 
    based on their major field of study.
    """)
    
    # Check if major field data exists
    has_major = all(
        'Major' in df.columns 
        for name, df in all_sheets.items() 
        if name.lower() != 'sheet7'
    )
    
    if not has_major:
        st.error("Major field column not found in one or more sheets. Unable to perform analysis.")
        return
    
    # Extract major field data from each session
    major_data = {}
    session_totals = {}
    all_majors = set()
    
    # Function to standardize major names
    def standardize_major(major):
        if pd.isna(major):
            return "Unknown"
        
        major = str(major).strip().upper()
        
        # Common variations mapping
        variations = {
            'COMP SCI': 'COMPUTER SCIENCE',
            'BIO': 'BIOLOGY',
            'PSYCH': 'PSYCHOLOGY',
            'COMM': 'COMMUNICATIONS',
            'ECON': 'ECONOMICS',
            'ENG': 'ENGLISH',
            'BUS': 'BUSINESS',
            'BUS ADMIN': 'BUSINESS ADMINISTRATION'
        }
        
        for key, value in variations.items():
            if key in major:
                return value
        
        return major
    
    for sheet_name, df in all_sheets.items():
        if sheet_name.lower() == 'sheet7':  # Skip empty sheet
            continue
        
        # Standardize and count majors
        df['Standardized Major'] = df['Major'].apply(standardize_major)
        major_counts = df['Standardized Major'].value_counts()
        major_data[sheet_name] = major_counts
        session_totals[sheet_name] = len(df)
        all_majors.update(major_counts.index)
    
    # ------------------- Major Field Overview -------------------
    st.subheader("Major Field Overview")
    
    # Create metrics cards
    col1, col2, col3 = st.columns(3)
    
    # Calculate total unique majors
    total_majors = len([m for m in all_majors if m != 'Unknown'])
    
    # Find most common major
    major_totals = {}
    for counts in major_data.values():
        for major, count in counts.items():
            if major not in major_totals:
                major_totals[major] = 0
            major_totals[major] += count
    
    top_major = max(major_totals.items(), key=lambda x: x[1]) if major_totals else ('Unknown', 0)
    
    # Calculate percentage of known majors
    total_attendees = sum(major_totals.values())
    known_majors = sum(count for major, count in major_totals.items() if major != 'Unknown')
    known_percentage = (known_majors / total_attendees * 100) if total_attendees > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{total_majors}</div>
            <div class='metric-label'>Unique Majors</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{top_major[0]}</div>
            <div class='metric-label'>Most Common Major</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{known_percentage:.1f}%</div>
            <div class='metric-label'>Known Major Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ------------------- Major Distribution by Session -------------------
    st.subheader("Major Field Distribution by Session")
    
    # Get top 10 majors for cleaner visualization
    top_majors = sorted(
        [(major, count) for major, count in major_totals.items() if major != 'Unknown'],
        key=lambda x: x[1],
        reverse=True
    )[:10]
    top_major_names = [m[0] for m in top_majors]
    
    # Create a standardized DataFrame for plotting
    plot_data = []
    
    for session, counts in major_data.items():
        total = session_totals[session]
        for major in top_major_names:
            count = counts.get(major, 0)
            percentage = (count / total * 100) if total > 0 else 0
            plot_data.append({
                'Session': session,
                'Major': major,
                'Count': count,
                'Percentage': percentage
            })
    
    plot_df = pd.DataFrame(plot_data)
    
    # Create a stacked bar chart showing percentage breakdown
    fig = px.bar(
        plot_df,
        x='Session',
        y='Percentage',
        color='Major',
        title='Top 10 Majors Distribution by Session (%)',
        labels={'Percentage': 'Percentage of Attendees', 'Session': 'Session Name'},
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600,
        barmode='stack',
        yaxis_title='Percentage of Attendees (%)',
        legend_title='Major'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Major Field Categories -------------------
    st.subheader("Major Field Categories")
    
    # Define major categories
    major_categories = {
        'STEM': ['COMPUTER SCIENCE', 'BIOLOGY', 'CHEMISTRY', 'PHYSICS', 'MATHEMATICS', 'ENGINEERING'],
        'Social Sciences': ['PSYCHOLOGY', 'SOCIOLOGY', 'POLITICAL SCIENCE', 'ECONOMICS', 'ANTHROPOLOGY'],
        'Humanities': ['ENGLISH', 'HISTORY', 'PHILOSOPHY', 'LANGUAGES', 'LITERATURE'],
        'Business': ['BUSINESS', 'BUSINESS ADMINISTRATION', 'MARKETING', 'FINANCE', 'ACCOUNTING'],
        'Arts': ['ART', 'MUSIC', 'THEATER', 'DANCE', 'DESIGN'],
        'Other': []  # For majors not in other categories
    }
    
    # Function to categorize majors
    def get_major_category(major):
        if major == 'Unknown':
            return 'Unknown'
        
        for category, majors in major_categories.items():
            if any(m in major for m in majors):
                return category
        return 'Other'
    
    # Add category to plot data
    plot_df['Category'] = plot_df['Major'].apply(get_major_category)
    
    # Create category summary
    category_summary = plot_df.groupby(['Session', 'Category'])['Count'].sum().reset_index()
    
    # Calculate percentages
    category_totals = category_summary.groupby('Session')['Count'].sum().reset_index()
    category_summary = category_summary.merge(category_totals, on='Session', suffixes=('', '_Total'))
    category_summary['Percentage'] = (category_summary['Count'] / category_summary['Count_Total'] * 100)
    
    # Create stacked bar chart for categories
    fig = px.bar(
        category_summary,
        x='Session',
        y='Percentage',
        color='Category',
        title='Major Field Categories by Session (%)',
        labels={'Percentage': 'Percentage of Attendees', 'Session': 'Session Name'},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        barmode='stack',
        yaxis_title='Percentage of Attendees (%)',
        legend_title='Field Category'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ------------------- Major Field Preference Analysis -------------------
    st.subheader("Major Field Preference by Session")
    
    # Calculate preference index for each major in each session
    preference_data = []
    
    # Calculate overall distribution of majors
    total_major_counts = pd.Series(0, index=top_major_names)
    total_attendees = 0
    
    for counts in major_data.values():
        for major in top_major_names:
            total_major_counts[major] += counts.get(major, 0)
        total_attendees += sum(counts.get(major, 0) for major in top_major_names)
    
    overall_percentages = (total_major_counts / total_attendees * 100) if total_attendees > 0 else 0
    
    # Calculate preference index
    for session, counts in major_data.items():
        session_total = sum(counts.get(major, 0) for major in top_major_names)
        
        for major in top_major_names:
            major_count = counts.get(major, 0)
            session_percentage = (major_count / session_total * 100) if session_total > 0 else 0
            overall_percentage = overall_percentages.get(major, 0)
            
            preference_index = (session_percentage / overall_percentage) if overall_percentage > 0 else 0
            
            preference_data.append({
                'Session': session,
                'Major': major,
                'Preference Index': preference_index
            })
    
    preference_df = pd.DataFrame(preference_data)
    
    # Create a heatmap
    pivot_df = preference_df.pivot(index='Major', columns='Session', values='Preference Index')
    
    fig = px.imshow(
        pivot_df,
        color_continuous_scale='RdBu_r',
        labels=dict(x="Session", y="Major", color="Preference Index"),
        title="Top Major Fields Preference by Session (>1: Over-represented, <1: Under-represented)",
        range_color=[0, 2]  # 0 to 2 range to make 1.0 the midpoint
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Explanation
    st.markdown("""
    **Understanding the Preference Index:**
    - **Preference Index = 1.0**: The major is represented at the expected rate
    - **Preference Index > 1.0**: The major is over-represented in this session
    - **Preference Index < 1.0**: The major is under-represented in this session
    - **Example**: An index of 2.0 means this major is twice as likely to attend this session compared to the overall average
    """)
    
    # ------------------- Major Field Data Download -------------------
    st.subheader("Major Field Data")
    
    # Prepare full data for download
    full_major_data = []
    
    for session, df in all_sheets.items():
        if session.lower() == 'sheet7':
            continue
            
        for _, row in df.iterrows():
            standardized_major = standardize_major(row['Major'])
            category = get_major_category(standardized_major)
            
            full_major_data.append({
                'Session': session,
                'Original Major': row['Major'] if pd.notna(row['Major']) else "Unknown",
                'Standardized Major': standardized_major,
                'Major Category': category
            })
    
    full_major_df = pd.DataFrame(full_major_data)
    
    # Display the DataFrame
    st.dataframe(full_major_df)
    
    # Create download link
    st.markdown(
        create_download_link(full_major_df, "major_field_data.csv", "Download Major Field Data"),
        unsafe_allow_html=True
    )
    
    # ------------------- Insights -------------------
    # Find session with most diverse major representation
    session_major_counts = {}
    for session, df in all_sheets.items():
        if session.lower() != 'sheet7':
            unique_majors = df['Major'].nunique()
            session_major_counts[session] = unique_majors
    
    most_diverse_session = max(session_major_counts.items(), key=lambda x: x[1]) if session_major_counts else ("None", 0)
    
    # Find strongest major-session correlation
    strongest_preference = preference_df.loc[preference_df['Preference Index'].idxmax()]
    
    # Calculate major category distribution
    category_distribution = pd.Series([get_major_category(m) for m in major_totals.keys()]).value_counts()
    primary_category = category_distribution.index[0] if not category_distribution.empty else "Unknown"
    primary_category_percentage = (category_distribution.iloc[0] / len(major_totals) * 100) if not category_distribution.empty else 0
    
    # Generate insights
    insights = {
        "Major diversity": f"{most_diverse_session[0]} had the most diverse major representation with {most_diverse_session[1]} different majors",
        "Strongest correlation": f"{strongest_preference['Major']} majors were {strongest_preference['Preference Index']:.1f}x more likely to attend {strongest_preference['Session']}",
        "Field concentration": f"{primary_category} fields account for {primary_category_percentage:.1f}% of all majors"
    }
    
    st.markdown(generate_insights(insights), unsafe_allow_html=True)

    # ------------------- Recommendations -------------------
    st.subheader("Recommendations")
    
    st.markdown("""
    1. **Content Alignment**: Develop session content that resonates with the academic backgrounds of target audiences.
    
    2. **Cross-Disciplinary Appeal**: Design sessions that attract attendees from diverse academic fields.
    
    3. **Marketing Focus**: Target marketing efforts to academic departments with high attendance rates.
    
    4. **Alumni Networks**: Leverage academic department alumni networks for session promotion.
    
    5. **Speaker Selection**: Choose speakers whose backgrounds align with the academic interests of the audience.
    """) 