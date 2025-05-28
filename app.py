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
    st.experimental_rerun()

# 📂 Sidebar Upload & Delete
with st.sidebar:
    st.header("📁 Upload Tradovate CSV")
    csv_file = st.file_uploader("Upload Tradovate File", type="csv")

    if st.button("🗑 Delete All Trades"):
        delete_all_trades(conn)
        st.warning("All trades deleted.")
        st.experimental_rerun()

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
    st.experimental_rerun()

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
                continue
            pnl = pnl_map.get(day, 0)
            trades_count = trade_map.get(day, 0)
            color = "#d4f4dd" if pnl > 0 else "#f4d4d4" if pnl < 0 else "#e0e0e0"

            ax.add_patch(plt.Rectangle((col, -row), 1, 1, color=color, edgecolor='gray'))

            # ✅ Big, Bold Text
            ax.text(col + 0.1, -row + 0.9, f"{day}", ha='left', va='top', fontsize=18, fontweight='bold', color='black')
            ax.text(col + 0.5, -row + 0.5, f"${pnl:.2f}", ha='center', va='center', fontsize=16, fontweight='bold', color='black')

    ax.set_title(f"{calendar.month_name[month]} {year} Trade Calendar", fontsize=20, weight='bold')
    legend_items = [
        mpatches.Patch(color="#d4f4dd", label='Profit Day'),
        mpatches.Patch(color="#f4d4d4", label='Loss Day'),
        mpatches.Patch(color="#e0e0e0", label='No Trades'),
    ]
    ax.legend(handles=legend_items, loc='lower center', bbox_to_anchor=(0.5, -0.1), ncol=3)
    plt.tight_layout()
    st.pyplot(fig)

# 📋 Detail View
st.subheader("📋 View Trade Details")
selected_date = st.date_input("Select a date to view trades")
trades_for_day = trades[trades["Date"].dt.date == selected_date]
if not trades_for_day.empty:
    st.markdown(f"### Trades for {selected_date}")
    st.dataframe(trades_for_day)
else:
    st.info("No trades for this date.")
