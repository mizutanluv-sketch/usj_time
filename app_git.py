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
    "Hollywood Dream - The Ride ": "ハリウッド・ドリーム・ザ・ライド",
    "Hollywood Dream -The Ride": "ハリウッド・ドリーム・ザ・ライド",
    "Hollywood Dream -The Ride - Backdrop-": "ハリウッド・ドリーム・ザ・ライド ～バックドロップ～",
    "Hollywood Dream - The Ride - Backdrop-": "ハリウッド・ドリーム・ザ・ライド ～バックドロップ～",
    "Hollywood Dream - The Ride - Backdrop": "ハリウッド・ドリーム・ザ・ライド ～バックドロップ～",
    "The Ride": "ハリウッド・ドリーム・ザ・ライド",
    "Backdrop-": "ハリウッド・ドリーム・ザ・ライド ～バックドロップ～",
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
    "Snoopy's Sound Stage Adventure": "スヌーピーのサウンド・ステージ・アドベンチャー",
    "Frieren: Beyond Journey's End": "葬送のフリーレン",
    "Frieren": "葬送のフリーレン"
}

# エリアとアトラクションの紐付け基本マスター
AREA_MAPPING = {
    "ウィザーディング・ワールド・オブ・ハリー・ポッター™": [
        "Harry Potter and the Forbidden Journey™", "Flight of the Hippogriff™", "Ollivanders™",
        "ハリー・ポッター・アンド・ザ・フォービドゥン・ジャーニー™", "フライト・オブ・ザ・ヒッポグリフ™", "オリバンダーの店™"
    ],
    "スーパー・ニンテンドー・ワールド™": [
        "Mario Kart: Koopa's Challenge™", "Yoshi's Adventure™", "Mine Cart Madness™",
        "マリオカート ～クッパの挑戦状～™", "ヨッシー・アドベンチャー™", "ドンキーコングのクレイジー・トロッコ™"
    ],
    "ミニオン・パーク": [
        "Despicable Me Minion Mayhem", "Freeze Ray Sliders",
        "ミニオン・ハチャメチャ・ライド", "ミニオン・ハチャメチャ・アイス"
    ],
    "ジュラシック・パーク": [
        "The Flying Dinosaur", "Jurassic Park – The Ride™",
        "ザ・フライング・ダイナソー", "ジュラシック・パーク・ザ・ライド™"
    ],
    "アミティ・ビレッジ(ジョーズ)": [
        "JAWS™", "ジョーズ™"
    ],
    "ユニバーサル・ワンダーランド": [
        "Elmo's Go-Go Skateboard", "Elmo's Bubble Bubble", "Elmo's Little Drive",
        "Hello Kitty's Cupcake Dream", "Hello Kitty's Ribbon Collection",
        "Moppy's Balloon Trip", "Big Bird's Big Top Circus", "The Flying Snoopy",
        "Sesame's Big Drive", "Snoopy's Flying Ace Adventure", "Snoopy's Sound Stage Adventure",
        "エルモのゴーゴー・スケートボード", "エルモのバブル・バブル", "エルモのリトル・ドライブ",
        "ハローキティのカップケーキ・ドリーム", "ハローキティのリボン・コレクション",
        "モッピーのバルーン・トリップ", "ビッグバードのビッグトップ・サーカス", "フライング・スヌーピー",
        "セサミのビッグ・ドライブ", "スヌーピーのフライング・エース・アドベンチャー", "スヌーピーのサウンド・ステージ・アドベンチャー"
    ],
    "ハリウッド・エリア / ニューヨーク・エリア": [
        "Hollywood Dream - The Ride", "Hollywood Dream -The Ride - Backdrop-",
        "Space Fantasy – The Ride", "SING ON TOUR", "Detective Conan: The World",
        "Sesame Street 4-D Movie Magic™", "Shrek’s 4-D Adventure™", "Playing with Curious George™",
        "ハリウッド・ドリーム・ザ・ライド", "ハリウッド・ドリーム・ザ・ライド ～バックドロップ～",
        "スペース・ファンタジー・ザ・ライド", "シング・オン・ツアー", "名探偵コナン・ザ・ワールド",
        "セサミストリート 4-D ムービー・マジック™", "シュレック 4-D アドベンチャー™", "プレイング・ウィズ・おさるのジョージ™"
    ]
}

# 身長制限：132cm以上の乗り物（データ除外用）
OVER_132CM_RIDES = [
    "The Flying Dinosaur", "Hollywood Dream - The Ride", "Hollywood Dream -The Ride - Backdrop-",
    "ザ・フライング・ダイナソー", "ハリウッド・ドリーム・ザ・ライド", "ハリウッド・ドリーム・ザ・ライド ～バックドロップ～"
]

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
        rides = data.get('
