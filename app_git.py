import streamlit as st
import requests
from streamlit_js_eval import get_geolocation

# --- 1. 初期設定とモデル定義 ---
st.set_page_config(page_title="USJ 最強ナビゲーター", page_icon="🎢")

# API設定
#GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# APIモデル設定（ここでも変数を使うと管理が楽になります）
#MODEL_ID = "gemini-robotics-er-1.5-preview"
MODEL_ID = "gemini-3.1-flash-lite-preview"
#MODEL_ID = "gemini-3-flash-preview"
DISPLAY_MODEL = MODEL_ID.replace("-", " ").title()

# --- 2. 日本語変換用の辞書 (最終完成版) ---
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

# --- 3. 関数定義 ---
def get_wait_times():
    url = "https://queue-times.com/parks/284/queue_times.json"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers)
        data = res.json()
        rides = data.get('rides', [])
        if not rides:
            for land in data.get('lands', []):
                rides.extend(land.get('rides', []))
        return rides
    except:
        return []

def ask_gemini_v3(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=60)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "AIが混雑しています。少し待ってから再度お試しください。"

# --- 4. 画面構築 ---
st.title("🎢 USJ 最強ナビゲーター")
st.caption(f"最新の {DISPLAY_MODEL} が、あなたの現在地から最適なプランを提案します。")

# GPS取得
loc = get_geolocation()

# 座標リスト
spots = {
    "パーク入口": {"lat": 34.6654, "lon": 135.4323},
    "スーパー・ニンテンドー・ワールド™": {"lat": 34.6687, "lon": 135.4301},
    "ウィザーディング・ワールド・オブ・ハリー・ポッター™": {"lat": 34.6677, "lon": 135.4338},
    "ミニオン・パーク": {"lat": 34.6660, "lon": 135.4303},
    "アミティ・ビレッジ(ジョーズ)": {"lat": 34.6662, "lon": 135.4344},
    "ジュラシック・パーク": {"lat": 34.6645, "lon": 135.4305}
}

spot_names = list(spots.keys())
if loc:
    gps_label = "📍 現在地 (GPS取得済み)"
    spot_names.insert(0, gps_label)
    spots[gps_label] = {"lat": loc['coords']['latitude'], "lon": loc['coords']['longitude']}

selected_spot = st.selectbox("📍 あなたの現在地はどこですか？", options=spot_names)

# タブ表示
tab1, tab2 = st.tabs(["✨ おすすめを教えて！", "⏱️ リアルタイム待ち時間"])

with tab1:
    if st.button("✨ 提案をリクエストする"):
        with st.spinner("AIガイドが思考中..."):
            # 復活させたお気に入りのプロンプト
            prompt = f"""
            あなたはUSJのプロガイドです。
            現在、私はパーク内の「{selected_spot}」（座標: {spots[selected_spot]}）にいます。
            
            この位置情報を踏まえて、次に向かうべきおすすめのアトラクションやエリアを1つ提案してください。
            
            【回答のルール】
            1. 最初に「ズバリこちらです！」と結論を伝える。
            2. 選んだ理由を3つのポイントで解説する（距離の近さや、現在の待ち時間や想定混雑を考慮して）。
            3. 最後にプロらしいワクワクするアドバイスを添える。
            
            回答は日本語で、Streamlitで見やすいようにMarkdown形式（太字や絵文字）を多用して出力してください。
            """
            
            answer = ask_gemini_v3(prompt)
            st.success("AIガイドからの提案")
            st.markdown(answer)

with tab2:
    if st.button("🔄 情報を更新する"):
        rides = get_wait_times()
        if rides:
            for r in rides:
                eng_name = r.get('name', 'Unknown')
                jp_name = NAME_MAP.get(eng_name, eng_name)
                wait = r.get('wait_time', 0)
                status = f"🟢 {wait}分待ち" if r.get('is_open') else "🔴 休止中"
                st.write(f"**{jp_name}** : {status}")
        else:
            st.error("待ち時間データを取得できませんでした。")

# フッター
st.divider()
st.caption("Here we go! 最高のUSJ体験を！")
