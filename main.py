import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_lightweight_charts import renderLightweightCharts
import time

from consts import priceVolumeChartOptions

# 초기 설정
database = st.session_state

# 실시간 주가 업데이트 기능을 모듈화
def display_real_time_price(ticker, price_placeholder):
    finance_res = yf.Ticker(ticker)

    while True:
        # 데이터 가져오기
        history = finance_res.history(period='5d').tail(1)  # '1m'로 실시간에 가까운 데이터 가져오기
        yesterday = finance_res.history(period='5d').tail(2)
        changes = yesterday
        print(yesterday)

        # 데이터가 비어있는지 확인
        if not history.empty:
            current_price = history['Close'].iloc[0]
            price_placeholder.metric(label=f"{ticker.upper()} 현재 주가 ()", value=f"${current_price:.2f}")
        else:
            price_placeholder.warning("데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")

        time.sleep(5)


def get_recent_close_data(ticker, period='1mo'):
    finance_res = yf.Ticker(ticker)
    history = finance_res.history(period=period)
    close_data = history[['Close']].reset_index()

    # 날짜 열을 datetime 형식으로 변환
    close_data['Date'] = pd.to_datetime(close_data['Date'])

    # 날짜를 원하는 형식으로 변환
    close_data['Date'] = close_data['Date'].dt.strftime('%Y-%m-%d')
    close_data['변동률'] = close_data['Close'].pct_change() * 100
    close_data = close_data.tail(7)

    return (close_data
            .sort_values(by=['Date'], ascending=False)
            .rename(columns={"Date": "날짜", "Close": "종가"}, inplace=False)
            .set_index(keys='날짜'))


# 데이터프레임 스타일링
def highlight_change(val):
    color = 'rgba(75, 137, 220, 0.5)' if val < 0 else 'rgba(219,68,85,0.3)' if val > 0 else ''
    return f'background-color: {color}'

# 메인 인터페이스
st.title("주식 데이터 모니터링")

# 조회 기간 선택
period_options = {'1일': '1d', '5일': '5d', '1개월': '1mo', '3개월': '3mo', '6개월': '6mo', '1년': '1y'}
selected_period_key = st.selectbox("조회 기간을 선택하세요", options=list(period_options.keys()), index=3)
selected_period_label = period_options[selected_period_key]

input_ticker = st.text_input("모니터링 할 티커를 입력해주세요.", placeholder="AAPL")
btn = st.button("입력", type="primary")

if btn:
    finance_res = yf.Ticker(input_ticker)
    history = finance_res.history(period=selected_period_label)
    close = history[['Close']].reset_index()
    close['time'] = close['Date'].apply(lambda x: str(x).split(" ")[0])
    close['value'] = close['Close'].apply(lambda x: round(x, 3))
    close = close[['time', 'value']]

    priceVolumeSeries = [
        {
            "type": 'Area',
            "data": close.to_dict('records'),
            "options": {
                "topColor": 'rgba(38,198,218, 0.56)',
                "bottomColor": 'rgba(38,198,218, 0.04)',
                "lineColor": 'rgba(38,198,218, 1)',
                "lineWidth": 2,
            }
        }
    ]

    st.subheader(f"{finance_res.info.get('shortName', input_ticker.upper())} {selected_period_key} 주가 변동 그래프")

    # 실시간 주가를 표시할 placeholder 생성
    price_placeholder = st.empty()

    # 실시간 주가 업데이트 기능 호출 (초기 실행)
    finance_res = yf.Ticker(input_ticker)
    history = finance_res.history(period='5d').tail(1)  # 최근 1분 데이터 가져오기
    yesterday = finance_res.history(period='5d').tail(2)

    if not history.empty:
        current_price = history['Close'].iloc[0]
        yesterday_price = yesterday['Close'].iloc[0]
        change = round(1 - yesterday_price/current_price, 5) * 100
        price_placeholder.metric(label=f"{input_ticker.upper()} 현재 주가", value=f"${current_price:.2f} ({change}%)")
    else:
        price_placeholder.warning("데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")

    renderLightweightCharts([
        {
            "chart": priceVolumeChartOptions,
            "series": priceVolumeSeries
        }
    ], 'priceAndVolume')

    recent_data = get_recent_close_data(input_ticker)
    styled_df = recent_data.style.map(highlight_change, subset=['변동률']) \
        .format({"종가": "{:.2f}", "변동률": "{:.2f}%"}) \
        .set_table_styles([
        {'selector': 'thead th', 'props': [('font-size', '30px')]},
        {'selector': 'tbody td', 'props': [('font-size', '18px')]},
        {'selector': 'tbody td', 'props': [('padding', '10px')]},
        {'selector': 'table', 'props': [('width', '80%'), ('margin', '0 auto')]}  # 테이블 폭을 80%로 설정
    ])

    st.dataframe(styled_df, width=1200)

    # 실시간 주가 업데이트를 주기적으로 갱신
    while True:
        history = finance_res.history(period='5d').tail(1)
        if not history.empty:
            current_price = history['Close'].iloc[0]
            yesterday_price = yesterday['Close'].iloc[0]
            change = round(1 - yesterday_price/current_price, 5) * 100
            price_placeholder.metric(label=f"{input_ticker.upper()} 현재 주가", value=f"${current_price:.2f} ({change}%)")
        time.sleep(5)
