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
    "Yoshi's Adventure™": "ヨッシー・アドベンチャー™",
    "WaterWorld": "ウォーターワールド",
    "Universal Monsters Live Rock and Roll Show": "ユニバーサル・モンスター・ライブ・ロックンロール・ショー",
    "Snoopy's Flying Ace Adventure": "スヌーピーのフライング・エース・アドベンチャー",
    "Snoopy's Sound Stage Adventure": "スヌーピーのサウンド・ステージ・アドベンチャー"
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

# 期間限定や部分一致を含め、アトラクションを賢く正しいエリアに分類する関数
def get_assigned_area(name_str):
    if "Space Fantasy" in name_str or "スペース・ファンタジー" in name_str:
        return "ハリウッド・エリア / ニューヨーク・エリア"
    if "ミニオン" in name_str or "Minion" in name_str:
        return "ミニオン・パーク"
    if "呪術廻戦" in name_str or "4-D" in name_str or "コナン" in name_str or "Conan" in name_str or "シュレック" in name_str or "セサミストリート" in name_str:
        return "ハリウッド・エリア / ニューヨーク・エリア"
    if "ハリー・ポッター" in name_str or "ヒッポグリフ" in name_str or "オリバンダー" in name_str or "Harry Potter" in name_str:
        return "ウィザーディング・ワールド・オブ・ハリー・ポッター™"
    if "マリオ" in name_str or "ヨッシー" in name_str or "Yoshi" in name_str or "Mario" in name_str or "クッパ" in name_str or "トロッコ" in name_str or "ドンキーコング" in name_str:
        return "スーパー・ニンテンドー・ワールド™"
    if "ザ・フライング・ダイナソー" in name_str or "ジュラシック" in name_str or "Dinosaur" in name_str:
        return "ジュラシック・パーク"
    if "ジョーズ" in name_str or "JAWS" in name_str:
        return "アミティ・ビレッジ(ジョーズ)"
    if "エルモ" in name_str or "キティ" in name_str or "スヌーピー" in name_str or "モッピー" in name_str or "ビッグバード" in name_str:
        return "ユニバーサル・ワンダーランド"
    
    # 完全一致チェック
    for area_name, rides_in_area in AREA_MAPPING.items():
        if name_str in rides_in_area:
            return area_name
    return "その他・期間限定・ショー"

# コントロールパネル用のマスタリスト
SELECTABLE_RIDES = sorted(list(set([
    "ハリー・ポッター・アンド・ザ・フォービドゥン・ジャーニー™", "フライト・オブ・ザ・ヒッポグリフ™", "オリバンダーの店™",
    "マリオカート ～クッパの挑戦状～™", "ヨッシー・アドベンチャー™", "ドンキーコングのクレイジー・トロッコ™",
    "ミニオン・ハチャメチャ・ライド", "ミニオン・ハチャメチャ・アイス", "ミニオン・ハチャメチャ・ミッション ～大悪党への道～",
    "ザ・フライング・ダイナソー", "ジュラシック・パーク・ザ・ライド™", "ジョーズ™",
    "ハリウッド・ドリーム・ザ・ライド", "ハリウッド・ドリーム・ザ・ライド ～バックドロップ～",
    "スペース・ファンタジー・ザ・ライド", "スペース・ファンタジー・ザ・ライド ～CLUB ZEDD REMIX～",
    "シング・オン・ツアー", "名探偵コナン・ザ・ワールド", "呪術廻戦・ザ・リアル 4-D ～廻る時計台～",
    "セサミストリート 4-D ムービー・マジック™", "シュレック 4-D アドベンチャー™", "プレイング・ウィズ・おさるのジョージ™",
    "エルモのゴーゴー・スケートボード", "エルモのバブル・バブル", "エルモのリトル・ドライブ",
    "ハローキティのカップケーキ・ドリーム", "ハローキティのリボン・コレクション",
    "モッピーのバルーン・トリップ", "ビッグバードのビッグトップ・サーカス", "フライング・スヌーピー",
    "スヌーピーのフライング・エース・アドベンチャー", "スヌーピーのサウンド・ステージ・アドベンチャー"
])))

# --- 4. サイドバー構築（当日ノーコード管理パネル） ---
with st.sidebar:
    st.header("⚙️ 当日コントロールパネル")
    debug_mode = st.checkbox("🔍 API生データ表示（デバッグ）", value=False)
    
    st.markdown("---")
    st.subheader("⚠️ 緊急ステータス上書き")
    st.caption("公式アプリと表示がズレている場合、ここで選択したアトラクションはPC不要で即座に「🔴 休止中 / 0分」に上書きされ、AIの提案ロジックからも除外されます。")
    
    selected_closed_jps = st.multiselect(
        "🚫 強制休止にするアトラクション",
        options=SELECTABLE_RIDES
    )

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
            # 1. 事前に期間限定のスペースファンタジーが配信されているかスキャン
            has_limited_spafan = False
            for r in rides:
                raw_n = r.get('name', '')
                disp_n = raw_n.split(" - ", 1)[1].strip() if " - " in raw_n else raw_n.strip()
                if ("スペース・ファンタジー" in disp_n and disp_n != "スペース・ファンタジー・ザ・ライド") or ("Space Fantasy" in disp_n and disp_n != "Space Fantasy – The Ride"):
                    has_limited_spafan = True
                    break
            
            # 各エリアの表示バッファ
            area_displays = {area: [] for area in AREA_MAPPING.keys()}
            area_displays["その他・期間限定・ショー"] = []
            
            for r in rides:
                raw_name = r.get('name', 'Unknown')
                is_open = r.get('is_open', False)
                wait = r.get('wait_time', 0)
                raw_open, raw_wait = is_open, wait
                
                # 【プレフィックス削除】"エリア名 - アトラクション名" からアトラクション名だけを抽出
                if " - " in raw_name:
                    display_name = raw_name.split(" - ", 1)[1].strip()
                else:
                    display_name = raw_name.strip()
                    
                # 【ユーザー要望】期間限定版がある場合、通常版の「スペース・ファンタジー・ザ・ライド」はスキップ（上のは削除）
                if has_limited_spafan and (display_name == "スペース・ファンタジー・ザ・ライド" or display_name == "Space Fantasy – The Ride"):
                    continue
                    
                jp_name = NAME_MAP.get(display_name, display_name)
                
                # 緊急ステータス上書きチェック
                if (raw_name in selected_closed_jps) or (display_name in selected_closed_jps) or (jp_name in selected_closed_jps):
                    is_open = False
                    wait = 0
                    
                status = f"🟢 {wait}分待ち" if is_open else "🔴 休止中"
                debug_info = f" `(API生データ: {raw_name}, is_open={raw_open}, wait={raw_wait})`" if debug_mode else ""
                
                # 部分一致を考慮した自動エリア分類
                assigned_area = get_assigned_area(jp_name)
                area_displays[assigned_area].append(f"**{jp_name}** : {status}{debug_info}")
            
            # エリアごとにまとめてスッキリ描画
            for area_name in AREA_MAPPING.keys():
                lines = area_displays[area_name]
                if lines:
                    st.subheader(f"📍 {area_name}")
                    for line in lines:
                        st.write(line)
                        
            # その他・期間限定アトラクションの描画
            if area_displays["その他・期間限定・ショー"]:
                st.subheader("📍 その他・期間限定・ショー")
                for line in area_displays["その他・期間限定・ショー"]:
                    st.write(line)
        else:
            st.error("待ち時間データを取得できませんでした。")

with tab2:
    if st.button("✨ 提案をリクエストする"):
        with st.spinner("最新の待ち時間をチェックして、2パターンの最適プランを練っています..."):
            rides_data = get_wait_times()
            
            if not rides_data:
                st.error("待ち時間データが取得できませんでした。")
            else:
                current_coords = spots[selected_spot]
                wait_time_summary = ""
                
                # 期間限定スペースファンタジーの有無をチェック
                has_limited_spafan = False
                for r in rides_data:
                    raw_n = r.get('name', '')
                    disp_n = raw_n.split(" - ", 1)[1].strip() if " - " in raw_n else raw_n.strip()
                    if ("スペース・ファンタジー" in disp_n and disp_n != "スペース・ファンタジー・ザ・ライド") or ("Space Fantasy" in disp_n and disp_n != "Space Fantasy – The Ride"):
                        has_limited_spafan = True
                        break
                
                area_summaries = {area: "" for area in AREA_MAPPING.keys()}
                area_summaries["その他・期間限定・ショー"] = ""
                
                for r in rides_data:
                    raw_name = r.get('name', 'Unknown')
                    
                    if " - " in raw_name:
                        display_name = raw_name.split(" - ", 1)[1].strip()
                    else:
                        display_name = raw_name.strip()
                        
                    if has_limited_spafan and (display_name == "スペース・ファンタジー・ザ・ライド" or display_name == "Space Fantasy – The Ride"):
                        continue
                        
                    jp_name = NAME_MAP.get(display_name, display_name)
                    
                    # 身長制限132cm以上の除外判定
                    if jp_name in OVER_132CM_RIDES or display_name in OVER_132CM_RIDES:
                        continue
                        
                    is_open = r.get('is_open', False)
                    wait = r.get('wait_time', 0)
                    
                    if (raw_name in selected_closed_jps) or (display_name in selected_closed_jps) or (jp_name in selected_closed_jps):
                        is_open = False
                        wait = 0
                        
                    status = "営業中" if is_open else "休止中"
                    assigned_area = get_assigned_area(jp_name)
                    area_summaries[assigned_area] += f"- {jp_name}: {wait}分 ({status})\n"
                    
                for area_name in list(AREA_MAPPING.keys()) + ["その他・期間限定・ショー"]:
                    summary_text = area_summaries[area_name]
                    if summary_text:
                        dist_info = ""
                        if area_name in spots:
                            t_coords = spots[area_name]
                            dist_m = calculate_distance(current_coords['lat'], current_coords['lon'], t_coords['lat'], t_coords['lon'])
                            walk_min = round(dist_m / 80)
                            dist_info = f"（現在地から約{int(dist_m)}m / 徒歩{walk_min}分）"
                        wait_time_summary += f"\n### {area_name} {dist_info}\n" + summary_text

                # f-stringのパースエラー（SyntaxError）を100%防ぐための変数完全分離
                spot_lat = current_coords['lat']
                spot_lon = current_coords['lon']
                
                prompt = f"""
                あなたはUSJの超ベテランプロガイドです。
                
                【同行者情報】
                ・小学3年生の女の子（ハリー・ポッターが一択で大、大、大好き！）
                ・身長制限：132cm未満（制限を超える132cm以上のアトラクションはデータから除外済み）
                
                【本日の戦略】
                ・「午前中にハリー・ポッターエリアを完全に遊び尽くしてクリアする」という超重要ミッションがあります！
                
                【現在の状況】
                ・私の現在地: {selected_spot} (座標: 緯度{spot_lat}, 経度{spot_lon})
                ・パーク内のリアルタイム状況（エリア別）:
                {wait_time_summary}
                
                【依頼】
                上記の戦略、リアルタイム混雑、移動距離を完璧に分析し、当日の状況に合わせて選べるよう、以下の【2つのパターン】で次に向かうべき最高の一手をそれぞれ1つずつ提案してください。
                
                ---
                
                ### ① 【ハリー・ポッターエリア以外メイン】のおすすめ
                午前中にハリポタエリアを無事クリアした後に向かうべき、あるいは現在エリア外にいる場合の「ハリー・ポッターエリア以外」での最高の一手を1つ選んでください。
                
                ### ② 【ハリー・ポッターエリア内】のおすすめ
                午前中にハリー・ポッターエリア内を100%効率よく遊び尽くすために、今「ハリー・ポッターエリア内」で向かうべき最高の一手を1つ選んでください。
                
                ---
                
                【回答のルール】
                1. 必ず上記の「①ハリー・ポッターエリア以外メイン」と「②ハリー・ポッターエリア内」の2つの見出しを分けて明確に出力してください。
                2. それぞれのパターンで、最初に「ズバリこちらです！」と結論の乗り物名を伝える。
                3. 選んだ理由を3つのポイントで解説する（距離、現在の待ち時間、そして小3の娘さんが最高に楽しめるかという観点から具体的に）。
                4. それぞれの最後に、プロらしいワクワクするアドバイス（エリア移動のコツや、ハリポタのディープな楽しみ方など）を添える。
                
                回答は日本語で、Markdown形式を使ってスマホで見やすく元気いっぱいに構成してください。
                """
                answer = ask_gemini_v3(prompt)
                st.success("AIガイドからの2大最適プラン")
                st.markdown(answer)

st.divider()
st.caption("Here we go! 2026/6/1 最高の家族の思い出を！")
