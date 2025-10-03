import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import datetime, timedelta

# --- App Configuration ---
st.set_page_config(page_title="AI Expense Tracker", layout="wide")

# --- Initialize Session State ---
if 'expenses' not in st.session_state:
    st.session_state.expenses = []

# --- Main Title ---
st.title("AI-Powered Personal Expense Tracker")

# --- Input Form in a Sidebar ---
st.sidebar.header("Add a New Expense")
with st.sidebar.form("expense_form", clear_on_submit=True):
    expense_date = st.date_input("Date")
    amount = st.number_input("Amount", min_value=0.01, format="%.2f")
    category = st.selectbox("Category", ["Food", "Rent", "Travel", "Utilities", "Shopping", "Other"])
    submitted = st.form_submit_button("Add Expense")

    if submitted:
        st.session_state.expenses.append({
            "date": expense_date,
            "amount": amount,
            "category": category
        })
        st.sidebar.success("Expense added!")

# --- Main Page Display ---
if not st.session_state.expenses:
    st.info("Add an expense using the form on the left to see your summary.")
else:
    df = pd.DataFrame(st.session_state.expenses)
    df['date'] = pd.to_datetime(df['date'])

    # --- Metrics and Charts ---
    st.header("Expense Summary")
    
    total_spend = df['amount'].sum()
    # CHANGED: Currency symbol updated to INR
    st.metric(label="Overall Total Spend", value=f"₹{total_spend:,.2f}")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Spend by Category")
        category_spend = df.groupby('category')['amount'].sum().reset_index()
        
        fig_pie = px.pie(category_spend, names='category', values='amount', 
                         title='Expense Distribution', hole=.3)
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("All Expenses")
        st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

    # --- AI-Powered Projection ---
    st.header("Spending Projection (AI Feature)")

    if len(df['date'].unique()) > 1:
        df_proj = df.copy()
        df_proj = df_proj.sort_values(by='date')
        df_proj['cumulative_spend'] = df_proj['amount'].cumsum()
        df_proj['days_since_start'] = (df_proj['date'] - df_proj['date'].min()).dt.days
        
        X = df_proj[['days_since_start']]
        y = df_proj['cumulative_spend']
        model = LinearRegression()
        model.fit(X, y)

        last_date = df_proj['date'].max()
        future_days = pd.to_numeric((last_date - df_proj['date'].min()).days) + np.arange(0, 31).reshape(-1, 1)
        
        future_spend = model.predict(future_days)

        projection_df = pd.DataFrame({
            'Date': [df_proj['date'].min() + timedelta(days=int(d)) for d in future_days.flatten()],
            'Projected Cumulative Spend': future_spend
        })

        fig_proj = px.line(title='Spending Trend and 30-Day Projection')
        fig_proj.add_scatter(x=df_proj['date'], y=df_proj['cumulative_spend'], mode='lines+markers', name='Actual Spending')
        fig_proj.add_scatter(x=projection_df['Date'], y=projection_df['Projected Cumulative Spend'], mode='lines', name='Projected Spending', line=dict(dash='dash'))
        
        st.plotly_chart(fig_proj, use_container_width=True)
        
        projected_total = projection_df['Projected Cumulative Spend'].iloc[-1]
        # CHANGED: Currency symbol updated to INR
        st.metric(label="Projected Spend in 30 Days", value=f"₹{projected_total:,.2f}")

    else:
        st.info("Add expenses on at least two different days to see a spending projection.")