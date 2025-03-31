import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from io import BytesIO
import re

def load_data(uploaded_file):
    """
    Load data from the uploaded Excel file
    """
    try:
        # Load all sheets from the Excel file
        xls = pd.ExcelFile(uploaded_file)
        all_sheets = {}
        
        for sheet_name in xls.sheet_names:
            try:
                # Read each sheet into a DataFrame
                df = pd.read_excel(xls, sheet_name=sheet_name)
                all_sheets[sheet_name] = df
            except Exception as e:
                st.warning(f"Could not read sheet '{sheet_name}': {e}")
        
        return all_sheets
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        raise e

def clean_data(df):
    """
    Clean and prepare the data for analysis
    """
    # Make a copy to avoid modifying the original
    df_clean = df.copy()
    
    # Handle missing values
    for col in df_clean.columns:
        # Replace empty strings with NaN
        df_clean[col] = df_clean[col].replace('', np.nan)
    
    # Convert ID column to string if it exists
    if 'ID' in df_clean.columns:
        df_clean['ID'] = df_clean['ID'].astype(str)
    
    # Convert year columns to numeric where appropriate
    year_cols = ['CL YR', 'SP CL YR']
    for col in year_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # Identify date columns for conversion and exclusion from numeric processing
    date_cols = []
    for col in df_clean.columns:
        if 'Date' in col or 'date' in col:
            date_cols.append(col)
    
    # Convert date columns to datetime
    for col in date_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
    
    # Process gift amounts (remove $ and commas, convert to numeric)
    amount_cols = [col for col in df_clean.columns if ('Gift' in col or 'Ask' in col) and col not in date_cols]
    for col in amount_cols:
        if col in df_clean.columns:
            if df_clean[col].dtype == object:  # Only process if it's a string column
                # Check if it's a range column (like WE Range)
                if col == 'WE Range' or col == 'LT Giving':
                    # Keep as is, these are categorical ranges
                    pass
                else:
                    # Remove $ and commas, convert to numeric
                    df_clean[col] = df_clean[col].astype(str).str.replace('$', '', regex=False)
                    df_clean[col] = df_clean[col].astype(str).str.replace(',', '', regex=False)
                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # Extract decade from class year
    if 'CL YR' in df_clean.columns:
        df_clean['Decade'] = (df_clean['CL YR'] // 10) * 10
        df_clean['Decade'] = df_clean['Decade'].apply(lambda x: f"{int(x)}s" if not pd.isna(x) else "Unknown")
    
    # Extract state from address for geographic analysis
    if 'State' in df_clean.columns:
        # Fill missing states with "Unknown"
        df_clean['State'] = df_clean['State'].fillna('Unknown')
    
    # Create a combined giving metric for analysis (excluding date columns)
    giving_cols = [col for col in df_clean.columns if 
                  ('Gifts' in col or 'Gift' in col) and 
                  'Pledge' not in col and 
                  col not in date_cols and
                  df_clean[col].dtype != 'datetime64[ns]']  # Additional datetime check
    
    if giving_cols:
        try:
            # Sum all available giving columns to get total giving
            df_clean['Total_All_Giving'] = df_clean[giving_cols].sum(axis=1, skipna=True)
        except Exception as e:
            st.warning(f"Could not calculate Total_All_Giving: {e}")
            # Fallback - try each column individually
            df_clean['Total_All_Giving'] = 0
            for col in giving_cols:
                try:
                    numeric_values = pd.to_numeric(df_clean[col], errors='coerce')
                    df_clean['Total_All_Giving'] += numeric_values.fillna(0)
                except:
                    pass
    
    return df_clean

def create_download_link(df, filename="data.csv", text="Download CSV"):
    """
    Create a download link for a dataframe
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def extract_wealth_range_value(wealth_range):
    """
    Extract the lower bound of the wealth range for sorting
    """
    if pd.isna(wealth_range) or wealth_range == '':
        return 0
    
    # Extract numbers from strings like "$5,000-$9,999"
    numbers = re.findall(r'[\d,]+', str(wealth_range))
    if not numbers:
        return 0
    
    # Convert the first number to float
    try:
        # Remove commas and convert to float
        return float(numbers[0].replace(',', ''))
    except:
        return 0

def get_decade_label(year):
    """Convert a year to a decade label like '1990s'"""
    if pd.isna(year):
        return "Unknown"
    try:
        decade = (int(year) // 10) * 10
        return f"{decade}s"
    except:
        return "Unknown"

def categorize_giving_level(amount):
    """Categorize giving amount into levels"""
    if pd.isna(amount) or amount == 0:
        return "Non-Donor"
    elif amount < 100:
        return "<$100"
    elif amount < 1000:
        return "$100-$999"
    elif amount < 5000:
        return "$1,000-$4,999"
    elif amount < 10000:
        return "$5,000-$9,999"
    elif amount < 25000:
        return "$10,000-$24,999"
    else:
        return "$25,000+"

def get_session_colors():
    """Return a consistent color map for sessions"""
    return {
        "2021 Lets Be Real": "#1E40AF",
        "wendie malik": "#3B82F6",
        "karlyn crowley session": "#60A5FA",
        "no more hiding session": "#93C5FD",
        "February 22 session ": "#BFDBFE",
        "2024 Women in Politics": "#1E3A8A",
        "session with Jordane Wells": "#2563EB"
    }

def generate_insights(data_dict, title="Key Insights"):
    """Generate an insights box with bullet points"""
    insights_html = f"""
    <div class='insight-box'>
        <h4>{title}:</h4>
        <ul>
    """
    
    for key, value in data_dict.items():
        insights_html += f"<li><b>{key}</b>: {value}</li>"
    
    insights_html += """
        </ul>
    </div>
    """
    
    return insights_html

def format_large_number(num):
    """Format large numbers with K, M suffixes"""
    if num < 1000:
        return str(int(num))
    elif num < 1000000:
        return f"{num/1000:.1f}K"
    else:
        return f"{num/1000000:.1f}M" 