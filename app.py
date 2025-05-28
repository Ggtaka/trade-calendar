import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import calendar
import matplotlib.patches as mpatches
from db import init_db, insert_trade, get_all_trades, get_trades_by_date, delete_all_trades

# Init database
conn = init_db()
st.set_page_config("Trade Calendar", layout="wide")

# 📐 Styling
st.markdown("""
    <style>
    .stTitle { font-size: 32px !important; }
    .stMarkdown h2 { font-size: 28px !important; }
    .stMarkdown p { font-size: 18px !important; }
    .element-container { font-size: 18px !important; }
    </style>
""", unsafe_allow_html=True)

# 🔄 Title + manual refresh
st.title("📊 Trade Calendar with SQLite (Tradovate Format)")
if st.button("🔄 Refresh Now"):
    st.rerun()

# 📂 Sidebar Upload & Delete
with st.sidebar:
    st.header("📁 Upload Tradovate CSV")
    csv_file = st.file_uploader("Upload Tradovate File", type="csv")

    if st.button("🗑 Delete All Trades"):
        delete_all_trades(conn)
        st.warning("All trades deleted.")
        st.rerun()

# 📥 Handle Upload
if csv_file:
    df = pd.read_csv(csv_file)
    df['pnl'] = df['pnl'].replace('[\$,()]', '', regex=True).astype(float) * df['pnl'].str.contains('\(').apply(lambda x: -1 if x else 1)
    df['boughtTimestamp'] = pd.to_datetime(df['boughtTimestamp'], errors='coerce')
    df['date'] = df['boughtTimestamp'].dt.date
    df['timestamp'] = df['boughtTimestamp'].astype(str)

    for _, row in df.iterrows():
        insert_trade(conn, (
            str(row['date']),
            row['symbol'],
            int(row['qty']),
            row['pnl'],
            row['timestamp']
        ))

    st.success("Trades imported!")
    st.rerun()

# 📊 Load and summarize
trades = pd.DataFrame(get_all_trades(conn), columns=["ID", "Date", "Symbol", "Qty", "PnL", "Timestamp"])
trades["Date"] = pd.to_datetime(trades["Date"])
summary = trades.groupby(trades["Date"].dt.date).agg(PnL=('PnL', 'sum'), Trades=('ID', 'count')).reset_index()
summary["Date"] = pd.to_datetime(summary["Date"])

# 📅 Calendar Rendering
if not summary.empty:
    year = summary["Date"].dt.year.max()
    month = summary["Date"].dt.month.max()

    st.subheader(f"{calendar.month_name[month]} {year} Trade Calendar")

    cal = calendar.Calendar()
    weeks = list(cal.monthdayscalendar(year, month))
    pnl_map = summary.set_index(summary["Date"].dt.day)["PnL"].to_dict()
    trade_map = summary.set_index(summary["Date"].dt.day)["Trades"].to_dict()

    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 7)
    ax.set_ylim(-len(weeks), 0)
    ax.set_axis_off()

    for row, week in enumerate(weeks):
        for col, day in enumerate(week):
            if day == 0:
