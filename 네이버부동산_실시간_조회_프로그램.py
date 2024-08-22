import requests, math
from bs4 import BeautifulSoup
import json
from openpyxl import Workbook
import datetime
import pandas as pd
import numpy as np
import math
import streamlit as st
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
import urllib.parse
from geopy.distance import distance
import plotly.graph_objs as go
import re
import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import great_circle


st.title("네이버 부동산 실시간 조회")
st.markdown(
    """
    <p style='font-size: 12px; color: gray;'> 주소 입력을 통해 원하는 위치의 매물을 확인할 수 있어요. </p>
    """ ,
    unsafe_allow_html=True
    )

def initialize_session_state():
    if 'lon' not in st.session_state:
        st.session_state.lon = None
    if 'lat' not in st.session_state:
        st.session_state.lat = None
    if 'spc_min' not in st.session_state:
        st.session_state.spc_min = None
    if 'spc_max' not in st.session_state:
        st.session_state.spc_max = None
    if 'address' not in st.session_state:
        st.session_state.address = None
    
def haversine_distance(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences in coordinates
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(delta_lat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance in kilometers
    distance = R * c

    return distance

def render_sidebar_filters():
    st.sidebar.title("필터")
    # 주의 사항 아주 작게 표기
    st.sidebar.markdown(
    """
    <p style='font-size: 12px; color: gray;'> 현재 저장된 기본 수집 로직을 따르려면 그냥 지나가주세요.</p>
    """, 
    unsafe_allow_html=True
    )
    col1, col2 = st.sidebar.columns([0.5, 0.5])
    with col1:
        selected_min_area = st.radio(
            "최소 면적",
            options = ["~10평대", "10평대", "20평대", "30평대", "40평대", "50평대", "60평대", "70평대~"],
            index=3)
    with col2:
        selected_max_area = st.radio(
            "최대 면적",
            options = ["~10평대", "10평대", "20평대", "30평대", "40평대", "50평대", "60평대", "70평대~"],
            index=7)
    area_list = [33, 66, 99, 132, 165, 198, 231, 900000000]
    if selected_min_area == "~10평대":
        spc_max = area_list[0]
    elif selected_min_area == "10평대":
        spc_min = area_list[0]
    elif selected_min_area == "20평대":
        spc_min = area_list[1]
    elif selected_min_area == "30평대":
        spc_min = area_list[2]
    elif selected_min_area == "40평대":
        spc_min = area_list[3]
    elif selected_min_area == "50평대":
        spc_min = area_list[4]
    elif selected_min_area == "60평대":
        spc_min = area_list[5]
    else:
        spc_min = area_list[6]

    if selected_max_area == "~10평대":
        spc_max = area_list[0]
    elif selected_max_area == "10평대":
        spc_max = area_list[0]
    elif selected_max_area == "20평대":
        spc_max = area_list[1]
    elif selected_max_area == "30평대":
        spc_max = area_list[2]
    elif selected_max_area == "40평대":
        spc_max = area_list[3]
    elif selected_max_area == "50평대":
        spc_max = area_list[4]
    elif selected_max_area == "60평대":
        spc_max = area_list[5]
    else:
        spc_max = area_list[6]
    
    st.session_state.spc_min = int(spc_min)
    st.session_state.spc_max = int(spc_max)

def render_table():
    lat_margin = 0.00135
    lon_margin = 0.00171

    if st.session_state.lon and st.session_state.lat:
        lft = st.session_state.lon - lon_margin
        rgt = st.session_state.lon + lon_margin
        top = st.session_state.lat + lat_margin
        btm = st.session_state.lat - lat_margin
        
        st.session_state.lft = lft
        st.session_state.rgt = rgt
        st.session_state.top = top
        st.session_state.btm = btm

        cluster_url = "https://m.land.naver.com/cluster/clusterList?view=atcl&rletTpCd=SG:SMS:GM:APTHGJ&tradTpCd=B2&z=19&lat={}&lon={}&btm={}&lft={}&top={}&rgt={}&spcMin=99&spcMax=900000000&pCortarNo=&addon=COMPLEX&isOnlyIsale=false".format(st.session_state.lat, st.session_state.lon, btm, lft, top, rgt)
        headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'}

        lgeo_holder = []
        mm_count_holder = []
        mm_lat_holder = []
        mm_lon_holder = []
        distance_holder = []

        cluster_res = requests.get(cluster_url, headers=headers)
        try:
            cluster_str = json.loads(json.dumps(cluster_res.json()))
        except:
            st.write("조회가 어려운 지역입니다.")
        else:
            values = cluster_str['data']['ARTICLE']
            for v in values:
                lgeo = v['lgeo']
                mm_count = v['count']
                mm_lat = v['lat']
                mm_lon = v['lon']
                dist = haversine_distance(st.session_state.lat, st.session_state.lon, mm_lat, mm_lon)
                lgeo_holder.append(lgeo)
                mm_count_holder.append(mm_count)
                mm_lat_holder.append(mm_lat)
                mm_lon_holder.append(mm_lon)
                distance_holder.append(dist)

        lgeo_df = pd.DataFrame()
        lgeo_df['lgeo'] = lgeo_holder
        lgeo_df['count'] = mm_count_holder
        lgeo_df['lat'] = mm_lat_holder
        lgeo_df['lon'] = mm_lon_holder
        lgeo_df['distance(km)'] = distance_holder
        # 10m 미만만 취급
        lgeo_df = lgeo_df[lgeo_df['distance(km)'] < 0.01]
        lgeo_df = lgeo_df.sort_values(by='distance(km)', ascending=True)

        if len(lgeo_df) == 0:
            st.write("조회되는 매물이 없습니다.")
        else:
            lgeo = lgeo_df['lgeo'].iloc[0]
            mm_lat = lgeo_df['lat'].iloc[0]
            mm_lon = lgeo_df['lon'].iloc[0]
            mm_count = lgeo_df['count'].iloc[0]
            mm_lft = mm_lon - lon_margin
            mm_rgt = mm_lon + lon_margin
            mm_top = mm_lat + lat_margin
            mm_btm = mm_lat - lat_margin

            checkdate_holder = []
            atclNo_holder = []
            rletTpNm_holder = []
            tradTpNm_holder = []
            prc_holder = []
            spc1_holder = []
            spc2_holder = []
            curr_flr_holder = []
            entire_flr_holder = []
            tagList_holder = []
            rltrNm_holder = []
            detailed_info_holder = []

            page_total = (mm_count - 1) // 20 + 1
            mm_idx = 0
            for i in range(page_total):
                page_count = i + 1
                properties_url = "https://m.land.naver.com/cluster/ajax/articleList?itemId={}&mapKey=&lgeo={}&rletTpCd=SG:SMS:GM:APTHGJ&tradTpCd=B2&z=19&lat={}&lon={}&btm={}&lft={}&top={}&rgt={}&cortarNo=&showR0=&spcMin=99&spcMax=900000000&sort=dates&page={}".format(lgeo, lgeo, mm_lat, mm_lon, mm_btm, mm_lft, mm_top, mm_rgt, page_count)
                properties_res = requests.get(properties_url, headers=headers)
                try:
                    properties_str = json.loads(json.dumps(properties_res.json()))
                except:
                    st.write("매물이 없습니다.")
                else:
                    values = properties_str['body']
                    if len(values) == 0:
                        pass
                    else:
                        for v in values:
                            mm_idx += 1
                            # 원하는 데이터만 따로 추출
                            atclCfmYmd = v['atclCfmYmd']        # 확인날짜
                            atclNo = v['atclNo']                # 물건번호
                            rletTpNm = v['rletTpNm']            # 상가구분
                            tradTpNm = v['tradTpNm']            # 매매/전세/월세 구분
                            prc = int(v['prc'])                 # 가격 (보증금 숫자)
                            if prc < 10000:
                                prc = str(prc) + "만원"
                            else:
                                if prc % 10000 == 0:
                                    prc = str(round(prc / 10000)) + "억원"
                                else:
                                    prc = str(round(prc / 10000, 1)) + "억원"
                            spc1 = str(round(float(v['spc1']) / 3.3)) + "평"    # 계약면적(m2)
                            spc2 = str(round(float(v['spc2']) / 3.3)) + "평"    # 전용면적(m2)
                            try:
                                hanPrc = v['hanPrc']               # 보증금
                            except:
                                hanPrc = 0
                            rentPrc = int(v['rentPrc'])              # 월세
                            if rentPrc < 10000:
                                rentPrc = str(rentPrc) + "만원"
                            else:
                                if rentPrc % 10000 == 0:
                                    rentPrc = str(round(rentPrc / 10000)) + "억원"
                                else:
                                    rentPrc = str(round(rentPrc / 10000, 1)) + "억원"
                            curr_flr = v['flrInfo'].split("/")[0] + "층"           # 현재층
                            entire_flr = v['flrInfo'].split("/")[1] + "층"          # 전체층
                            tagList = v['tagList']              # 기타 정보
                            rltrNm = v['rltrNm']                # 부동산
                            detailed_information = "https://m.land.naver.com/article/info/{}".format(atclNo)

                            checkdate_holder.append(atclCfmYmd)
                            atclNo_holder.append(atclNo)
                            rletTpNm_holder.append(rletTpNm)
                            tradTpNm_holder.append(tradTpNm)
                            prc_holder.append(prc)
                            spc1_holder.append(spc1)
                            spc2_holder.append(spc2)
                            curr_flr_holder.append(curr_flr)
                            entire_flr_holder.append(entire_flr)
                            tagList_holder.append(tagList)
                            rltrNm_holder.append(rltrNm)
                            detailed_info_holder.append(detailed_information)
                        
            result = pd.DataFrame()
            result['확인날짜'] = checkdate_holder
            result['물건번호'] = atclNo_holder
            result['상가구분'] = rletTpNm_holder
            result['거래구분'] = tradTpNm_holder
            result['보증금'] = prc_holder
            result['계약면적'] = spc1_holder
            result['전용면적'] = spc2_holder
            result['현재층'] = curr_flr_holder
            result['전체층'] = entire_flr_holder
            result['부동산'] = rltrNm_holder
            result['상세정보'] = detailed_info_holder

            st.write("검색 결과")
            result = result[['상세정보', '확인날짜', '물건번호', '상가구분', '보증금', '계약면적', '전용면적',
                            '현재층', '전체층', '부동산']]
            st.dataframe(result, column_config={"상세정보": st.column_config.LinkColumn(display_text='링크')}, hide_index=True)

# def render_map(lat, lon):
 

if __name__ == "__main__":
    initialize_session_state()
    render_sidebar_filters()
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)

    # 주소 입력
    address_input = st.sidebar.text_input("주소를 입력해주세요:")
    st.session_state.address = address_input
    if st.sidebar.button("검색"):
        # input값으로 받은 주소를 좌표로 변환
        url = "https://dapi.kakao.com/v2/local/search/address.json?query={}".format(address_input)
        headers = {
            'Authorization': 'KakaoAK c1afa92688b614956bcba3f1d57ca16f'
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            documents = response.json().get('documents', [])

            if not documents:
                st.sidebar.write("주소 조회 결과가 없어요. 다시 입력해주세요.")
                st.session_state.lon = None
                st.session_state.lat = None
            else:
                address_data = documents[0].get('address', {})
                lon = address_data.get('x')
                lat = address_data.get('y')
                st.session_state.lon = float(lon)
                st.session_state.lat = float(lat)
                if lon and lat:
                    st.sidebar.write("입력하신 주소의 좌표를 확보했습니다.")
                else:
                    st.sidebar.write("좌표를 찾을 수 없습니다. 다른 주소로 시도해보세요.")
        except requests.exceptions.RequestException as e:
            st.sidebar.write("API 요청 중 오류가 발생했습니다. 나중에 다시 시도해주세요.")
        except Exception as e:
            st.sidebar.write("오류가 발생했습니다. 다시 시도해주세요.")

        render_table()

        layer = "Base"
        tileType = "png"
        vworld_key = "4E4307C2-1FEC-37E4-91D7-9E906DC2C228"
        tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/{layer}/{{z}}/{{y}}/{{x}}.{tileType}"
        attr = "Vworld"

        if st.session_state.lon and st.session_state.lat:
            m = folium.Map(location=[lat, lon],
                        zoom_start=15,
                        tiles=tiles,
                        attr=attr,
                        overlay=True,
                        control=True)
            
            folium.Marker(location=[lat, lon],
                        radius=15,
                        icon=folium.Icon(color='blue', icon='building', prefix='fa')
                        ).add_to(m)
            
            with st.container():
                st.write("지도")
                st.components.v1.html(m._repr_html_(), height=500, width=800)

        