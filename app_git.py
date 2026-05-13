import streamlit as st
import requests
import math
from streamlit_js_eval import get_geolocation

# --- 1. 初期設定と定数定義 ---
st.set_page_config(page_title="USJ 最強ナビゲーター", page_icon="🎢")

# APIキーの取得（セキュリティのためsecretsから取得）
if "GEMINI_API_KEY" not in st.secrets:
    st.error("エラー: GEMINI_API_KEY が設定されていません。")
    st.stop()
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# APIモデル設定（ここでも変数を使うと管理が楽になります）
MODEL_ID = "gemini-3.1-flash-lite"
#MODEL_ID = "gemini-3.1-flash-lite-preview"
#MODEL_ID = "gemini-3-flash-preview"
#MODEL_ID = "gemini-robotics-er-1.5-preview"
DISPLAY_MODEL = MODEL_ID.replace("-", " ").title()

# 日本語変換マップ
NAME_MAP = {
    "Harry Potter and the Forbidden Journey™": "ハリー・ポッター・アンド・ザ・フォービドゥン・ジャーニー™",
    "Hollywood Dream - The Ride": "ハリウッド・ドリーム・ザ・ライド",
    "Elmo's Go-Go Skateboard": "エルモのゴーゴー・スケートボード",
    "Despicable Me Minion Mayhem": "ミニオン・ハチャメチャ・ライド",
    "Space Fantasy – The Ride": "スペース・ファンタジー・ザ・ライド",
    "The Flying Dinosaur": "ザ・フライング・ダイナソー",
    "Big Bird's Big Top Circus": "ビッグバードのビッグトップ・サーカス",
    "Detective Conan: The World": "名探偵コナン・ザ・ワールド",
    "Elmo's Bubble Bubble": "エルモのバブル・バブル",
    "Elmo's Little Drive": "エルモのリトル・ドライブ",
    "Flight of the Hippogriff™": "フライト・オブ・ザ・ヒッポグリフ™",
    "Freeze Ray Sliders": "ミニオン・ハチャメチャ・アイス",
    "Hello Kitty's Cupcake Dream": "ハローキティのカップケーキ・ドリーム",
    "Hello Kitty's Ribbon Collection": "ハローキティのリボン・コレクション",
    "Hollywood Dream -The Ride - Backdrop-": "ハリウッド・ドリーム・ザ・ライド ～バックドロップ～",
    "JAWS™": "ジョーズ™",
    "Jurassic Park – The Ride™": "ジュラシック・パーク・ザ・ライド™",
    "Mario Kart: Koopa's Challenge™": "マリオカート ～クッパの挑戦状～™",
    "Mine Cart Madness™": "ドンキーコングのクレイジー・トロッコ™",
    "Moppy's Balloon Trip": "モッピーのバルーン・トリップ",
    "Ollivanders™": "オリバンダーの店™",
    "Playing with Curious George™": "プレイング・ウィズ・おさるのジョージ™",
    "Sesame Street 4-D Movie Magic™": "セサミストリート 4-D ムービー・マジック™",
    "Sesame's Big Drive": "セサミのビッグ・ドライブ",
    "Shrek’s 4-D Adventure™": "シュレック 4-D アドベンチャー™",
    "SING ON TOUR": "シング・オン・ツアー",
    "The Flying Snoopy": "フライング・スヌーピー",
    "Yoshi's Adventure™": "ヨッシー・アドベンチャー™"
}

# エリアとアトラクションの紐付け
AREA_MAPPING = {
    "ウィザーディング・ワールド・オブ・ハリー・ポッター™": [
        "Harry Potter and the Forbidden Journey™", "Flight of the Hippogriff™", "Ollivanders™"
    ],
    "スーパー・ニンテンドー・ワールド™": [
        "Mario Kart: Koopa's Challenge™", "Yoshi's Adventure™", "Mine Cart Madness™"
    ],
    "ミニオン・パーク": [
        "Despicable Me Minion Mayhem", "Freeze Ray Sliders"
    ],
    "ジュラシック・パーク": [
        "The Flying Dinosaur", "Jurassic Park – The Ride™"
    ],
    "アミティ・ビレッジ(ジョーズ)": [
        "JAWS™"
    ],
    "ユニバーサル・ワンダーランド": [
        "Elmo's Go-Go Skateboard", "Elmo's Bubble Bubble", "Elmo's Little Drive",
        "Hello Kitty's Cupcake Dream", "Hello Kitty's Ribbon Collection",
        "Moppy's Balloon Trip", "Big Bird's Big Top Circus", "The Flying Snoopy",
        "Sesame's Big Drive"
    ],
    "ハリウッド・エリア / ニューヨーク・エリア": [
        "Hollywood Dream - The Ride", "Hollywood Dream -The Ride - Backdrop-",
        "Space Fantasy – The Ride", "SING ON TOUR", "Detective Conan: The World",
        "Sesame Street 4-D Movie Magic™", "Shrek’s 4-D Adventure™",
        "Playing with Curious George™"
    ]
}

# 身長制限：132cm以上の乗り物（娘さんは乗れないもの）
OVER_132CM_RIDES = [
    "The Flying Dinosaur",
    "Hollywood Dream - The Ride",
    "Hollywood Dream -The Ride - Backdrop-"
]

# 各エリアの座標データ
spots = {
    "パーク入口": {"lat": 34.6654, "lon": 135.4323},
    "スーパー・ニンテンドー・ワールド™": {"lat": 34.6687, "lon": 135.4301},
    "ウィザーディング・ワールド・オブ・ハリー・ポッター™": {"lat": 34.6677, "lon": 135.4338},
    "ミニオン・パーク": {"lat": 34.6660, "lon": 135.4303},
    "アミティ・ビレッジ(ジョーズ)": {"lat": 34.6662, "lon": 135.4344},
    "ジュラシック・パーク": {"lat": 34.6645, "lon": 135.4305}
}

# --- 2. 関数定義 ---

def calculate_distance(lat1, lon1, lat2, lon2):
    """ハバーサイン公式で2地点の距離(m)を算出"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

@st.cache_data(ttl=180) # 3分間キャッシュ
def get_wait_times():
    url = "https://queue-times.com/parks/284/queue_times.json"
    headers = {"User-Agent": "Mozilla/5.0 USJ-Navi-App-User"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        rides = data.get('rides', [])
        if not rides:
            for land in data.get('lands', []):
                rides.extend(land.get('rides', []))
        return rides
    except Exception as e:
        st.error(f"待ち時間データの取得に失敗しました: {e}")
        return []

def ask_gemini_v3(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=60)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"AIとの通信でエラーが発生しました。時間を置いてお試しください。({e})"

# --- 3. UI構築 ---
st.title("🎢 USJ 最強ナビゲーター")
st.caption(f"モデル: {DISPLAY_MODEL} | 娘さんの身長(132cm未満)・ハリーポッター愛を反映済み")

# GPS取得
loc = get_geolocation()
spot_names = list(spots.keys())
if loc:
    gps_label = "📍 現在地 (GPS取得済み)"
    if gps_label not in spot_names:
        spot_names.insert(0, gps_label)
        spots[gps_label] = {"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']}

selected_spot = st.selectbox("📍 あなたの現在地はどこですか？", options=spot_names)

tab1, tab2 = st.tabs(["✨ おすすめを教えて！", "⏱️ リアルタイム待ち時間"])

with tab1:
    if st.button("✨ 提案をリクエストする"):
        with st.spinner("状況を完璧に分析中..."):
            rides_data = get_wait_times()
            if not rides_data:
                st.warning("現在、待ち時間データが取得できません。定番ルートでお楽しみください。")
            else:
                current_coords = spots[selected_spot]
                wait_time_summary = ""
                
                # エリアごとに情報を整理
                for area_name, rides_in_area in AREA_MAPPING.items():
                    # エリアまでの距離・徒歩時間を算出
                    dist_info = ""
                    if area_name in spots:
                        t_coords = spots[area_name]
                        dist_m = calculate_distance(current_coords['lat'], current_coords['lon'], t_coords['lat'], t_coords['lon'])
                        walk_min = round(dist_m / 80) # 80m/min
                        dist_info = f"（現在地から約{int(dist_m)}m / 徒歩{walk_min}分）"
                    
                    wait_time_summary += f"\n### {area_name} {dist_info}\n"
                    
                    for r in rides_data:
                        eng_name = r.get('name')
                        if eng_name in rides_in_area:
                            if eng_name in OVER_132CM_RIDES:
                                continue # 132cm制限は除外
                            
                            jp_name = NAME_MAP.get(eng_name, eng_name)
                            wait = r.get('wait_time', 0)
                            status = "営業中" if r.get('is_open') else "休止中"
                            wait_time_summary += f"- {jp_name}: {wait}分 ({status})\n"

                prompt = f"""
                あなたはUSJの超ベテランガイドです。
                同行者：ハリー・ポッターが大好き（一択！）な小学3年生の女の子。
                制限：身長132cm未満。
                状況：午前中はハリー・ポッターエリアを遊び尽くす予定。

                【現在のデータ】
                ・現在地: {selected_spot}
                ・エリア別待ち時間と移動目安:
                {wait_time_summary}

                【依頼】
                上記を分析し、次に向かうべき最高の一手を1つだけ提案してください。
                ハリー・ポッターエリア内での効率、あるいは混雑状況に応じた移動を考慮してください。
                
                【回答ルール】
                1. 「ズバリこちらです！」と結論から。
                2. 理由を3点（距離・待ち時間・娘さんの好みの観点）。
                3. ワクワクするアドバイスを添えて。
                日本語・Markdown形式で出力してください。
                """
                
                answer = ask_gemini_v3(prompt)
                st.success("AIガイドからの最適解")
                st.markdown(answer)

with tab2:
    if st.button("🔄 情報を更新する"):
        rides = get_wait_times()
        if rides:
            for area_name, rides_in_area in AREA_MAPPING.items():
                st.subheader(f"📍 {area_name}")
                for r in rides:
                    eng_name = r.get('name')
                    if eng_name in rides_in_area:
                        jp_name = NAME_MAP.get(eng_name, eng_name)
                        wait = r.get('wait_time', 0)
                        status = f"🟢 {wait}分待ち" if r.get('is_open') else "🔴 休止中"
                        st.write(f"**{area_name} - {jp_name}** : {status}")
        else:
            st.error("データを取得できませんでした。")

st.divider()
st.caption("Here we go! 2026/6/1 最高の家族の思い出を！")
