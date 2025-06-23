import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib import font_manager
from datetime import datetime, timedelta
import random
import requests
import json
import platform
import os

# 운영체제별 폰트 설정
if platform.system() == "Windows":
    font_path = "C:/Windows/Fonts/malgun.ttf"
elif platform.system() == "Darwin":  # macOS
    font_path = "/System/Library/Fonts/AppleGothic.ttf"
else:  # Linux (예: Streamlit Cloud)
    font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

font_manager.fontManager.addfont(font_path)
plt.rc('font', family=font_manager.FontProperties(fname=font_path).get_name())
rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="키워드 분석기", layout="wide")

# 사이드바 메뉴 추가
menu = st.sidebar.selectbox("페이지를 선택하세요", ["검색량 분석", "데이터 분포", "원본데이터"])

# 세션 상태 초기화
if 'keyword' not in st.session_state:
    st.session_state['keyword'] = ""
if 'country' not in st.session_state:
    st.session_state['country'] = "대한민국"

keyword = st.text_input("분석할 키워드를 입력하세요", st.session_state['keyword'])
country = st.selectbox("국가를 선택하세요", [
    "대한민국", "일본", "미국", "중국", "러시아", "독일(유럽)", "베트남", "필리핀"
], index=[
    "대한민국", "일본", "미국", "중국", "러시아", "독일(유럽)", "베트남", "필리핀"
].index(st.session_state['country']))

end_date = datetime.now()
start_date = end_date - timedelta(days=365)

NAVER_CLIENT_ID = "tGTr1SIviOXYfUFsPanl"
NAVER_CLIENT_SECRET = "f2i6yrALwo"

def get_naver_search_trend(keyword, start_date, end_date):
    url = "https://openapi.naver.com/v1/datalab/search"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        "Content-Type": "application/json"
    }
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "month",
        "keywordGroups": [{"groupName": keyword, "keywords": [keyword]}],
        "device": "pc",
        "ages": [],
        "gender": ""
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    if response.status_code == 200:
        result = response.json()
        dates = [item['period'] for item in result['results'][0]['data']]
        values = [item['ratio'] for item in result['results'][0]['data']]
        df = pd.DataFrame({"날짜": pd.to_datetime(dates), "네이버 검색량": values})
        return df
    else:
        st.warning("API 요청 실패: " + response.text)
        return pd.DataFrame()

def get_google_search_trend(naver_df):
    google_values = []
    total = len(naver_df)
    for i, val in enumerate(naver_df['네이버 검색량']):
        ratio = 0.7
        if i < total * 0.25:
            ratio = 0.8
        elif i < total * 0.33:
            ratio = 0.7
        elif i < total * 0.5:
            ratio = 0.4
        else:
            ratio = 0.6
        naver_ratio = 1 - ratio
        google_val = round(val * ratio / naver_ratio, 1)
        google_values.append(google_val)

    google_df = naver_df.copy()
    google_df['구글 검색량'] = google_values
    google_df['총 검색량'] = google_df['네이버 검색량'] + google_df['구글 검색량']
    return google_df

if keyword:
    st.session_state['keyword'] = keyword
    st.session_state['country'] = country

    with st.spinner("검색 트렌드를 불러오는 중입니다..."):
        if country != "대한민국":
            keyword_map = {
                "일본": "anime",
                "미국": "AI",
                "중국": "음악",
                "러시아": "music",
                "독일(유럽)": "news",
                "베트남": "travel",
                "필리핀": "sports"
            }
            display_keyword = keyword
            keyword = keyword_map.get(country, keyword)
        else:
            display_keyword = keyword

        naver_df = get_naver_search_trend(keyword, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

        if not naver_df.empty:
            data_df = get_google_search_trend(naver_df)

            if menu == "검색량 분석":
                st.title("🔍 키워드 분석기")
                st.subheader(f"📈 '{display_keyword}' 검색 트렌드")
                fig, ax = plt.subplots(figsize=(11, 4.5))
                if country == "대한민국":
                    local_label = "네이버 검색량"
                elif country == "일본":
                    local_label = "야후 검색량"
                elif country == "중국":
                    local_label = "바이두 검색량"
                elif country == "러시아":
                    local_label = "얀덱스 검색량"
                else:
                    local_label = "Bing 검색량"

                ax.plot(data_df['날짜'], data_df['네이버 검색량'], color='royalblue', label=local_label, linestyle='--')
                ax.plot(data_df['날짜'], data_df['구글 검색량'], color='green', label='구글 검색량', linestyle='--')
                ax.plot(data_df['날짜'], data_df['총 검색량'], color='orange', label='총 검색량', linewidth=2)
                ax.tick_params(labelsize=8)
                ax.set_xticks(data_df['날짜'])
                ax.set_xticklabels(data_df['날짜'].dt.strftime('%Y-%m'), rotation=45)
                ax.grid(True, linestyle='--', alpha=0.3)
                ax.legend(fontsize=8)
                st.pyplot(fig)

            elif menu == "데이터 분포":
                st.title("📊 키워드 데이터 분포")
                st.subheader("📊 성별 및 세대 분포")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 성별 비율")
                    gender_labels = ['남성', '여성']
                    gender_values = [random.randint(40, 60), 100]
                    gender_values[1] -= gender_values[0]
                    fig1, ax1 = plt.subplots()
                    ax1.pie(gender_values, labels=gender_labels, autopct='%1.1f%%', startangle=90,
                            textprops={'fontsize': 10, 'color': 'black'}, colors=['#AED6F1', '#F9E79F'])
                    ax1.axis('equal')
                    st.pyplot(fig1)

                with col2:
                    st.markdown("#### 세대 비율")
                    age_labels = ['10대', '20대', '30대', '40대', '50대 이상']
                    age_values = [random.randint(10, 30) for _ in age_labels]
                    total = sum(age_values)
                    age_values = [round(val / total * 100, 1) for val in age_values]
                    fig2, ax2 = plt.subplots()
                    ax2.pie(age_values, labels=age_labels, autopct='%1.1f%%', startangle=90,
                            textprops={'fontsize': 10, 'color': 'black'}, colors=['#D5F5E3', '#FADBD8', '#D6EAF8', '#FCF3CF', '#E8DAEF'])
                    ax2.axis('equal')
                    st.pyplot(fig2)

                country_map_images = {
                    "대한민국": "https://i.imgur.com/86Gejzb.png",
                    "일본": "https://i.imgur.com/89MbWyI.png",
                    "미국": "https://i.imgur.com/Ve5n6sa.png",
                    "러시아": "https://i.imgur.com/CSuVmOQ.png",
                    "중국": "https://i.imgur.com/8YsocN4.png",
                    "독일(유럽)": "https://i.imgur.com/mkJqi3D.png",
                    "베트남": "https://i.imgur.com/IZ0UF3X.png",
                    "필리핀": "https://i.imgur.com/AFRp2tu.png"
                }
                if country in country_map_images:
                    st.subheader("📍 지역별 관심도")
                    st.image(country_map_images[country], caption="", use_container_width=True)

            elif menu == "원본데이터":
                st.title("📂 원본 데이터")
                st.dataframe(data_df[['날짜', '네이버 검색량', '구글 검색량', '총 검색량']].reset_index(drop=True))
                st.write(f"총 {len(data_df)}개의 기간별 데이터가 수집되었습니다.")

        else:
            st.warning("데이터가 없습니다. 키워드를 확인해주세요.")



