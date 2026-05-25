import streamlit as st
import requests
import math
from streamlit_js_eval import get_geolocation

# --- 1. 初期設定とモデル定義 ---
st.set_page_config(page_title="USJ 最強ナビゲーター", page_icon="🎢")

# API設定（セキュリティのためsecretsから安全に取得）
if "GEMINI_API_KEY" not in st.secrets:
    st.error("エラー: GEMINI_API_KEY が設定されていません。")
    st.stop()

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# APIモデル設定
MODEL_ID = "gemini-3.1-flash-lite"
DISPLAY_MODEL = MODEL_ID.replace("-", " ").title()

# --- 2. 日本語変換用の辞書 ---
NAME_MAP = {
    "Harry Potter and the Forbidden Journey™": "ハリー・ポッター・アンド・ザ・フォービドゥン・ジャーニー™",
    "Harry Potter and the Forbidden Journey™ ": "ハリー・ポッター・アンド・ザ・フォービドゥン・ジャーニー™",
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

# エリアとアトラクションの紐付け（並び替え・エリア整理用）
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

# 身長制限：132cm以上の乗り物（娘さんは安全のため除外）
OVER_132CM_RIDES = [
    "The Flying Dinosaur",
    "Hollywood Dream - The Ride",
    "Hollywood Dream -The Ride - Backdrop-"
]

# 各エリアのマスター座標データ
spots = {
    "パーク入口": {"lat": 34.6654, "lon": 135.4323},
    "スーパー・ニンテンドー・ワールド™": {"lat": 34.6687, "lon": 135.4301},
    "ウィザーディング・ワールド・オブ・ハリー・ポッター™": {"lat": 34.6677, "lon": 135.4338},
    "ミニオン・パーク": {"lat": 34.6660, "lon": 135.4303},
    "アミティ・ビレッジ(ジョーズ)": {"lat": 34.6662, "lon": 135.4344},
    "ジュラシック・パーク": {"lat": 34.6645, "lon": 135.4305}
}

# --- 3. 関数定義 ---

def calculate_distance(lat1, lon1, lat2, lon2):
    """ハバーサイン公式で2地点の直線距離(m)を正確に算出"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

@st.cache_data(ttl=180) # 3分間のAPIキャッシュ（アクセス過多・バッテリー消費防止）
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
        return f"AIへの通信エラーが発生しました。少し待ってから再度お試しください。({e})"

# --- 4. 画面構築 ---
st.title("🎢 USJ 最強ナビゲーター")
st.caption(f"最新の {DISPLAY_MODEL} が、あなたの現在地から最適なプランを提案します。")

# GPS取得
loc = get_geolocation()

spot_names = list(spots.keys())
if loc:
    gps_label = "📍 現在地 (GPS取得済み)"
    if gps_label not in spot_names:
        spot_names.insert(0, gps_label)
        spots[gps_label] = {"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']}

selected_spot = st.selectbox("📍 あなたの現在地はどこですか？", options=spot_names)

# タブ表示
tab1, tab2 = st.tabs(["✨ おすすめを教えて！", "⏱️ リアルタイム待ち時間"])

with tab1:
    if st.button("✨ 提案をリクエストする"):
        with st.spinner("最新の待ち時間をチェックして、最適なプランを練っています..."):
            rides_data = get_wait_times()
            
            if not rides_data:
                st.error("待ち時間データが取得できませんでした。時間をおいて再度お試しください。")
            else:
                current_coords = spots[selected_spot]
                wait_time_summary = ""
                
                # エリアごとに情報を整理
                for area_name, rides_in_area in AREA_MAPPING.items():
                    dist_info = ""
                    if area_name in spots:
                        t_coords = spots[area_name]
                        dist_m = calculate_distance(current_coords['lat'], current_coords['lon'], t_coords['lat'], t_coords['lon'])
                        walk_min = round(dist_m / 80) # 分速80m換算
                        dist_info = f"（現在地から約{int(dist_m)}m / 徒歩{walk_min}分）"
                    
                    wait_time_summary += f"\n### {area_name} {dist_info}\n"
                    
                    # 各エリアに属するアトラクションを抽出
                    for r in rides_data:
                        eng_name = r.get('name', 'Unknown')
                        
                        # 前後の空白を削ってマッチング（フォービドゥン・ジャーニー対策）
                        if eng_name.strip() in [name.strip() for name in rides_in_area]:
                            if eng_name.strip() in [name.strip() for name in OVER_132CM_RIDES]:
                                continue # 132cm未満制限の自動スキップ
                            
                            jp_name = NAME_MAP.get(eng_name, NAME_MAP.get(eng_name.strip(), eng_name))
                            wait = r.get('wait_time', 0)
                            status = "営業中" if r.get('is_open') else "休止中"
                            wait_time_summary += f"- {jp_name}: {wait}分 ({status})\n"

                # 3. AIへのプロンプト設定（トリプルクォート・インデント完全検証済）
                prompt = f"""
                あなたはUSJの超ベテランプロガイドです。
                
                【同行者情報】
                ・小学3年生の女の子（ハリー・ポッターが一択で大好き！）
                ・身長制限：132cm未満（制限を超えるアトラクションはデータから除外済み）
                
                【本日の戦略】
                ・午前中はハリー・ポッターエリアを完全に遊び尽くす予定です。
                
                【現在の状況】
                ・私の現在地: {selected_spot} (座標: {spots[selected_spot]})
                ・パーク内のリアルタイム状況（エリア別）:
                {wait_time_summary}
                
                【依頼】
                上記の戦略とリアルタイム混雑・移動距離を完璧に分析し、
                次に向かうべき最高の一手を1つだけ提案してください。
                
                【回答のルール】
                1. 最初に「ズバリこちらです！」と結論を伝える。
                2. 選んだ理由を3つのポイントで解説する（距離、待ち時間、そして何より娘さんのハリポタ愛の観点から具体的に）。
                3. 最後にプロらしいワクワクするアドバイスを添える。
                
                回答は日本語で、Markdown形式（太字や絵文字）を使ってスマホで見やすく出力してください。
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
                    eng_name = r.get('name', 'Unknown')
                    
                    # タブ2側でも空白除去マッチングを徹底してフォービドゥン・ジャーニーの未表示を防止
                    if eng_name.strip() in [name.strip() for name in rides_in_area]:
                        jp_name = NAME_MAP.get(eng_name, NAME_MAP.get(eng_name.strip(), eng_name))
                        wait = r.get('wait_time', 0)
                        status = f"🟢 {wait}分待ち" if r.get('is_open') else "🔴 休止中"
                        st.write(f"**{jp_name}** : {status}")
        else:
            st.error("待ち時間データを取得できませんでした。")

# フッター
st.divider()
st.caption("Here we go! 2026/6/1 最高の家族の思い出を！")
