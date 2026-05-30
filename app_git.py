import streamlit as st
import requests
import math
from streamlit_js_eval import get_geolocation

# --- 1. 初期設定とモデル定義 ---
st.set_page_config(page_title="USJ 最強ナビゲーター", page_icon="🎢")

# API設定（セキュリティのためsecretsから取得）
if "GEMINI_API_KEY" not in st.secrets:
    st.error("エラー: GEMINI_API_KEY が設定されていません。")
    st.stop()

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
MODEL_ID = "gemini-3.1-flash-lite"
DISPLAY_MODEL = MODEL_ID.replace("-", " ").title()

# --- 2. 日本語変換用の辞書 ---
NAME_MAP = {
    "Harry Potter and the Forbidden Journey™": "ハリー・ポッター・アンド・ザ・フォービドゥン・ジャーニー™",
    "Harry Potter and the Forbidden Journey™ ": "ハリー・ポッター・アンド・ザ・フォービドゥン・ジャーニー™",
    "Hollywood Dream - The Ride": "ハリウッド・ドリーム・ザ・ライド",
    "Elmo's Go-Go Skateboard": "エルモのゴーゴー・スケートボード",
    "Despicable Me Minion Mayhem": "ミニオン・ハチャメチャ・ライド",
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
    "Yoshi's Adventure™": "ヨッシー・アドベンチャー™",
    "WaterWorld": "ウォーターワールド",
    "Universal Monsters Live Rock and Roll Show": "ユニバーサル・モンスター・ライブ・ロックンロール・ショー",
    "Snoopy's Flying Ace Adventure": "スヌーピーのフライング・エース・アドベンチャー",
    "Snoopy's Sound Stage Adventure": "スヌーピーのサウンド・ステージ・アドベンチャー"
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
        "Sesame's Big Drive", "Snoopy's Flying Ace Adventure", "Snoopy's Sound Stage Adventure"
    ],
    "ハリウッド・エリア / ニューヨーク・エリア": [
        "Hollywood Dream - The Ride", "Hollywood Dream -The Ride - Backdrop-",
        "スペース・ファンタジー・ザ・ライド ～CLUB ZEDD REMIX～", "Space Fantasy – The Ride - Club Zedd Remix",  # エリア内に登録
        "SING ON TOUR", "Detective Conan: The World",
        "Sesame Street 4-D Movie Magic™", "Shrek’s 4-D Adventure™",
        "Playing with Curious George™"
    ]
}

# 身長制限：132cm以上の乗り物（データ除外用）
OVER_132CM_RIDES = ["The Flying Dinosaur", "Hollywood Dream - The Ride", "Hollywood Dream -The Ride - Backdrop-"]

# 【新設】完全に除外するアトラクション（休止中の旧スペースファンタジーなどを完全に削る）
EXCLUDE_RIDES = ["Space Fantasy – The Ride", "スペース・ファンタジー・ザ・ライド"]

# 各エリアのマスター座標データ
spots = {
    "パーク入口": {"lat": 34.6654, "lon": 135.4323},
    "スーパー・ニンテンドー・ワールド™": {"lat": 34.6687, "lon": 135.4301},
    "ウィザーディング・ワールド・オブ・ハリー・ポッター™": {"lat": 34.6677, "lon": 135.4338},
    "ミニオン・パーク": {"lat": 34.6660, "lon": 135.4303},
    "アミティ・ビレッジ(ジョーズ)": {"lat": 34.6662, "lon": 135.4344},
    "ジュラシック・パーク": {"lat": 34.6645, "lon": 135.4305},
    "ユニバーサル・ワンダーランド": {"lat": 34.6666, "lon": 135.4358}
}

# --- 3. 関数定義 ---
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

@st.cache_data(ttl=180)
def get_wait_times():
    url = "https://queue-times.com/parks/284/queue_times.json"
    headers = {"User-Agent": "Mozilla/5.0 USJ-Navi-App"}
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
        st.error(f"データ取得エラー: {e}")
        return []

def ask_gemini_v3(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=60)
        res.raise_for_status()
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"AIへの通信エラーが発生しました。({e})"

# --- 4. サイドバー構築（当日ノーコード管理パネル） ---
with st.sidebar:
    st.header("⚙️ 当日コントロールパネル")
    debug_mode = st.checkbox("🔍 API生データ表示（デバッグ）", value=False)
    
    st.markdown("---")
    st.subheader("⚠️ 緊急ステータス上書き")
    st.caption("公式アプリと表示がズレている場合、ここで選択したアトラクションはPC不要で即座に「🔴 休止中 / 0分」に上書きされ、AIの提案ロジックからも除外されます。")
    
    INV_NAME_MAP = {v: k for k, v in NAME_MAP.items()}
    selected_closed_jps = st.multiselect(
        "🚫 強制休止にするアトラクション",
        options=sorted(list(INV_NAME_MAP.keys()))
    )
    dynamic_force_closed = [INV_NAME_MAP[jp].strip() for jp in selected_closed_jps]

# --- 5. メイン画面構築 ---
st.title("🎢 USJ 最強ナビゲーター")
st.caption(f"最新の {DISPLAY_MODEL} が、あなたの現在地から最適なプランを提案します。")

loc = get_geolocation()
spot_names = list(spots.keys())
if loc:
    gps_label = "📍 現在地 (GPS取得済み)"
    if gps_label not in spot_names:
        spot_names.insert(0, gps_label)
        spots[gps_label] = {"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']}

selected_spot = st.selectbox("📍 あなたの現在地はどこですか？", options=spot_names)

# タブ設定：左側が「リアルタイム待ち時間」、右側が「おすすめを教えて！」
tab1, tab2 = st.tabs(["⏱️ リアルタイム待ち時間", "✨ おすすめを教えて！"])

with tab1:
    if st.button("🔄 情報を更新する"):
        rides = get_wait_times()
        if rides:
            matched_api_names = set()
            
            for area_name, rides_in_area in AREA_MAPPING.items():
                area_rides = []
                for r in rides:
                    eng_name = r.get('name', 'Unknown')
                    
                    # 休止中の旧スペースファンタジーはスキップして完全削除
                    if eng_name.strip() in EXCLUDE_RIDES:
                        continue
                        
                    if eng_name.strip() in [name.strip() for name in rides_in_area]:
                        matched_api_names.add(eng_name.strip())
                        area_rides.append(r)
                
                if area_rides:
                    st.subheader(f"📍 {area_name}")
                    for r in area_rides:
                        eng_name = r.get('name', 'Unknown')
                        is_open = r.get('is_open', False)
                        wait = r.get('wait_time', 0)
                        raw_open, raw_wait = is_open, wait
                        
                        if eng_name.strip() in dynamic_force_closed:
                            is_open = False
                            wait = 0
                            
                        jp_name = NAME_MAP.get(eng_name, NAME_MAP.get(eng_name.strip(), eng_name))
                        status = f"🟢 {wait}分待ち" if is_open else "🔴 休止中"
                        debug_info = f" `(API生データ: is_open={raw_open}, wait={raw_wait})`" if debug_mode else ""
                        st.write(f"**{jp_name}** : {status}{debug_info}")
            
            # その他枠
            other_rides = []
            for r in rides:
                eng_name = r.get('name', 'Unknown')
                if eng_name.strip() in EXCLUDE_RIDES:
                    continue
                if eng_name.strip() not in matched_api_names:
                    other_rides.append(r)
                    
            if other_rides:
                st.subheader("📍 その他・期間限定・ショー")
                for r in other_rides:
                    eng_name = r.get('name', 'Unknown')
                    is_open = r.get('is_open', False)
                    wait = r.get('wait_time', 0)
                    raw_open, raw_wait = is_open, wait
                    
                    if eng_name.strip() in dynamic_force_closed:
                        is_open = False
                        wait = 0
                        
                    jp_name = NAME_MAP.get(eng_name, NAME_MAP.get(eng_name.strip(), eng_name))
                    status = f"🟢 {wait}分待ち" if is_open else "🔴 休止中"
                    debug_info = f" `(API生データ: is_open={raw_open}, wait={raw_wait})`" if debug_mode else ""
                    st.write(f"**{jp_name}** : {status}{debug_info}")
        else:
            st.error("待ち時間データを取得できませんでした。")

with tab2:
    if st.button("✨ 提案をリクエストする"):
        with st.spinner("最新の待ち時間をチェックして、2パターンの最適プランを練っています..."):
            rides_data = get_wait_times()
            
            if not rides_data:
                st.error("待ち時間データが取得できませんでした。")
            else:
