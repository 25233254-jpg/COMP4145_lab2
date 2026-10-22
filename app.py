import pandas as pd
import streamlit as st
import altair as alt

from trading_strategy import get_stock_data, calculate_moving_averages, identify_golden_cross, implement_strategy


@st.cache_data
def load_strategy_data():
    data = get_stock_data("MSFT")
    data = calculate_moving_averages(data)
    data = identify_golden_cross(data)
    positions = implement_strategy(data)
    return data, positions


st.set_page_config(page_title="MSFT Trading Dashboard", page_icon="📈", layout="wide")


def format_currency(value):
    return f"${value:,.2f}"


data, positions = load_strategy_data()

page = st.sidebar.radio("Navigation", ["Price Chart", "Trade Statistics", "Detailed Trades"])

if page == "Price Chart":
    st.title("MSFT Price Chart")
    st.caption("Whole-period stock price with moving averages and trade signals")

    chart_df = data.reset_index().rename(columns={"index": "Date", "Close": "ClosePrice"})
    chart_df["Date"] = pd.to_datetime(chart_df["Date"])

    buy_points = positions[["BuyDate", "BuyPrice"]].rename(columns={"BuyDate": "Date", "BuyPrice": "Price"})
    sell_points = positions[["SellDate", "SellPrice"]].rename(columns={"SellDate": "Date", "SellPrice": "Price"})

    base = (
        alt.Chart(chart_df)
        .mark_line(point=False)
        .encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("ClosePrice:Q", title="Price ($)"),
            tooltip=["Date:T", "ClosePrice:Q", "MA50:Q", "MA200:Q"],
        )
    )

    ma50 = (
        alt.Chart(chart_df)
        .mark_line(color="#f39c12", strokeWidth=2)
        .encode(x="Date:T", y="MA50:Q")
    )

    ma200 = (
        alt.Chart(chart_df)
        .mark_line(color="#2980b9", strokeWidth=2)
        .encode(x="Date:T", y="MA200:Q")
    )

    buy_markers = (
        alt.Chart(buy_points)
        .mark_circle(size=100, color="green")
        .encode(x="Date:T", y="Price:Q", tooltip=["Date:T", "Price:Q"])
    )

    sell_markers = (
        alt.Chart(sell_points)
        .mark_circle(size=100, color="red")
        .encode(x="Date:T", y="Price:Q", tooltip=["Date:T", "Price:Q"])
    )

    st.altair_chart(base + ma50 + ma200 + buy_markers + sell_markers, use_container_width=True)

elif page == "Trade Statistics":
    st.title("Overall Trade Statistics")

    if positions.empty:
        st.info("No trades were generated for the selected strategy.")
    else:
        total_trades = len(positions)
        winning_trades = int((positions["ProfitPct"] > 0).sum())
        losing_trades = total_trades - winning_trades
        avg_profit = positions["ProfitPct"].mean()
        avg_holding = positions["HoldingDays"].mean()
        win_rate = (winning_trades / total_trades) * 100 if total_trades else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Trades", total_trades)
        col2.metric("Winning Trades", winning_trades)
        col3.metric("Losing Trades", losing_trades)
        col4.metric("Win Rate", f"{win_rate:.2f}%")

        col5, col6, col7 = st.columns(3)
        col5.metric("Average Profit", f"{avg_profit:.2f}%")
        col6.metric("Average Holding Days", f"{avg_holding:.1f} days")
        col7.metric("Target Reached", int((positions["SellReason"] == "Target reached").sum()))

        profit_summary = (
            positions[["BuyDate", "SellDate", "ProfitPct", "SellReason"]]
            .copy()
        )
        profit_summary["ProfitPct"] = profit_summary["ProfitPct"].round(2)
        st.dataframe(profit_summary, use_container_width=True)

        st.subheader("Profit Distribution")
        chart = alt.Chart(positions).mark_bar().encode(
            x=alt.X("ProfitPct:Q", bin=True, title="Profit (%)"),
            y="count()",
        )
        st.altair_chart(chart, use_container_width=True)

else:
    st.title("Detailed Trades Record")

    if positions.empty:
        st.info("No trade records are available.")
    else:
        display_df = positions.copy()
        display_df["BuyDate"] = pd.to_datetime(display_df["BuyDate"]).dt.strftime("%Y-%m-%d")
        display_df["SellDate"] = pd.to_datetime(display_df["SellDate"]).dt.strftime("%Y-%m-%d")
        display_df["BuyPrice"] = display_df["BuyPrice"].map(lambda x: format_currency(x))
        display_df["SellPrice"] = display_df["SellPrice"].map(lambda x: format_currency(x))
        display_df["ProfitPct"] = display_df["ProfitPct"].map(lambda x: f"{x:.2f}%")

        st.dataframe(display_df, use_container_width=True, hide_index=True)
