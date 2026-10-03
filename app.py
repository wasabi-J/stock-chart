import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas.tseries.offsets import BDay
from datetime import datetime, timezone, timedelta

# Streamlit CloudのサーバーはUTCで動くため、表示は必ずJSTへ明示変換する
JST = timezone(timedelta(hours=9))

st.set_page_config(page_title="大底・天井スコア", layout="wide")

GROUPS = {
    "📁 保有中": {
        "COIN（コインベース）": "COIN",
        "CPRI（カプリHD・逆張り柱）": "CPRI",
        "ESAB（溶接・切断機器・逆張り柱）": "ESAB",   # 2026-09-11に2株取得
        "GRAB（グラブ・逆張り柱）": "GRAB",           # 2026-09-16に22株取得
        "PFSI（ペニーマック・逆張り柱）": "PFSI",      # 2026-09-16に2株取得（ティアS）
        "TME（テンセントミュージック・逆張り柱）": "TME",  # 2026-09-14に8株取得
        "MSTR（マイクロストラテジー）": "MSTR",
        "1328（金ETF・日本）": "1328.T",
        "6963（ローム・モメンタム柱）": "6963.T",
    },
    "📁 監視": {
        "SHAK（シェイクシャック）": "SHAK",
        "JNJ（J&J・守り優等生）": "JNJ",
        "ALHC（アラインメントヘルスケア・医療保険MA）": "ALHC",  # 9/19に誤って削除→9/26復元（Q2黒字EPS+$0.17で落第根拠なし）
        "KRUS（くら寿司USA・2026-09に逆指値発動で売却済→監視）": "KRUS",
        "CRWD（クラウドストライク・2026-09-18登録）": "CRWD",
        "PG（P&G・守り）": "PG",
        "CRM（セールスフォース・攻め）": "CRM",
        "AVAV（エアロバイロンメント）": "AVAV",
        "BABA（アリババ・売却済→監視）": "BABA",
        "7325（アイリック・見送り→監視）": "7325.T",
        "3549（クスリのアオキ・優待）": "3549.T",
        "8136（サンリオ・優待バケット）": "8136.T",
        "MARA（マラソンデジタル）": "MARA",
        "CLSK（クリーンスパーク）": "CLSK",
        "NVDA（エヌビディア）": "NVDA",
        "TSLA（テスラ）": "TSLA",
        "GLD（金ETF米国）": "GLD",
        "SLV（銀ETF）": "SLV",
        "1673（銀ETF・日本/WisdomTree）": "1673.T",
        "SOFI（ソーファイ）": "SOFI",
        "EWZ（ブラジルETF）": "EWZ",
        "AMD": "AMD",
        "TTD（トレードデスク・広告）🔬対象外:バリュエーション型": "TTD",
        "RIVN（リビアン・EV）": "RIVN",
        "OLED（ユニバーサルディスプレイ）": "OLED",
        "MP（MPマテリアルズ・レアアース）": "MP",
        "TMF（米国債20年3倍・売却済→監視）": "TMF",
        "SOXL（半導体3倍）🔬検証済:対象外": "SOXL",
        "QS（クアンタムスケープ）🔬検証済:対象外": "QS",
        "TSLL（TSLA2倍ブル）🔬システム外": "TSLL",
        "XLE（エネルギーETF）": "XLE",
        "EC（エコペトロール・売却済）": "EC",
        # --- 2026-08-15 週次スクリーニングv2 審査通過（米国株13）---
        "ACM（エーコム・建設エンジ）": "ACM",
        "AMTM（アメンタム・政府サービス）": "AMTM",
        "APTV（アプティブ・自動車部品）": "APTV",
        "INTR（インテル&Co・ブラジル銀行）": "INTR",
        "LVS（ラスベガス・サンズ）": "LVS",
        "MMS（マキシマス・政府BPO）": "MMS",
        "NKE（ナイキ）": "NKE",
        "ONON（オン・スニーカー）": "ONON",
        "POST（ポストHD・シリアル）": "POST",
        "PPC（ピルグリムズプライド・鶏肉）": "PPC",
        "SGI（ソムニグループ・マットレス）": "SGI",
        "ZTS（ゾエティス・動物用医薬）": "ZTS",
        # --- 2026-08-15 週次スクリーニングv2 審査通過（日本株12）---
        "2216（カンロ・製菓）": "2216.T",
        "3692（FFRIセキュリティ）": "3692.T",
        "3836（アバントグループ）": "3836.T",
        "3905（データセクション）": "3905.T",
        "4569（キョーリン製薬HD）": "4569.T",
        "5214（日本電気硝子）": "5214.T",
        "6787（メイコー・プリント基板）": "6787.T",
        "7003（三井E&S）": "7003.T",
        "7157（ライフネット生命）": "7157.T",
        "7649（スギホールディングス）": "7649.T",
        "7760（IMV・振動試験装置）": "7760.T",
        "9024（西武ホールディングス）": "9024.T",
        # --- 2026-08-22 週次スクリーニングv2 審査通過（米国株14）---
        "FLO（フラワーズフーズ・製パン）": "FLO",
        "GAP（ギャップ・アパレル小売）": "GAP",
        "GME（ゲームストップ・現金9.7B）": "GME",
        "HDB（HDFC銀行・インド）": "HDB",
        "IPGP（IPGフォトニクス・レーザー）": "IPGP",
        "LII（レノックス・空調）": "LII",
        "MIR（ミリオン・放射線検出）": "MIR",
        "ROL（ロリンズ・害虫駆除）": "ROL",
        "SITE（サイトワン・造園資材卸）": "SITE",
        "SYM（シンボティック・物流ロボ）": "SYM",
        "TIMB（TIMブラジル・通信）": "TIMB",
        "WING（ウィングストップ・チキン）": "WING",
        # --- 2026-08-22 週次スクリーニングv2 審査通過（日本株9）---
        "1801（大成建設）": "1801.T",
        "1835（東鉄工業）": "1835.T",
        "1893（五洋建設）": "1893.T",
        "2980（SRE HD）": "2980.T",
        "4685（菱友システムズ）": "4685.T",
        "6088（シグマクシスHD）": "6088.T",
        "6269（三井海洋開発）": "6269.T",
        "6961（エンプラス・半導体系）": "6961.T",
        "7409（AeroEdge・PER予64倍）": "7409.T",
        # --- 2026-08-24 追加：銅の地形（COPXが買い対象・HG=Fは指数フォルダに地図として登録）---
        # CPERでなくCOPXを選んだ理由＝低ボラ銘柄はVIX30でも成績が改善しない（GLD/JNJ/PGがその側）。
        # CPERは銅価格をなぞるだけで同じ穴。COPXは鉱山株なので営業レバレッジが効き、下げも深く戻りも
        # 大きい＝ホームラン型が求める右の裾がある。深度-45%を満たすのは世界的な景気後退時のみで
        # 待ち時間は年単位。★金GLD・銀SLV・銅COPXが揃ったのでコモディティ同時売られ局面では
        # 3つ同時点灯がありうる＝その時は集中ルールで1つに絞る。
        "COPX（銅鉱山株ETF）": "COPX",
        # --- 2026-08-24 追加：以前追いかけていた10件（買い場が来たら目的をその時に決める）---
        "CPNG（クーパン・韓国EC）": "CPNG",
        "KTOS（クレイトス・無人機）": "KTOS",
        "LDOS（レイドス・防衛IT）": "LDOS",
        "MNDY（monday.com・SaaS）": "MNDY",
        "1345（Jリート指数ETF・低ボラ側）": "1345.T",
        "1458（楽天ETF日経レバ）🔬対象外:レバETF": "1458.T",
        "2869（iFreeETF NASDAQ100レバ）🔬対象外:レバETF": "2869.T",
        "4661（オリエンタルランド・優待あり）": "4661.T",
        "6920（レーザーテック・半導体検査）": "6920.T",
        "7615（京都きもの友禅HD・優待あり）": "7615.T",
        # --- 2026-08-29 週次スクリーニングv2 審査通過（米国株5・日本株2）---
        # ★深度-45%基準での初回。日本4件・米国18件でうち新規審査11件（先週26件から半減＝基準変更が効いている）。
        # ★落第4件は全て赤字（EOSE／OKLO／OPEN／QXO）。
        # ★BLDRは会計上は赤字だがIRS和解の一時費用によるもので営業利益は黒字→通過。
        #   「一時費用による赤字」と「本業の赤字」の線引きの実例なのだ（QXOは本業の赤字で落第）。
        "APP（アップラビン・広告テック）": "APP",
        "BLDR（ビルダーズFirstSource・建材流通）": "BLDR",
        "PNR（ペンテア・水処理）": "PNR",
        "TRIP（トリップアドバイザー）": "TRIP",
        "WD（ウォーカー&ダンロップ・商業不動産金融）": "WD",
        "8267（イオン）": "8267.T",
        "9412（スカパーJSAT）": "9412.T",
        # --- 2026-09-09 手動登録（週次スクリーナー経由ではない）---
        # ★ちいかわコラボの景品横領報道による下落を観察する目的。深度は-8%程度で-45%には遠く当面点灯しない。
        # ★★【KRUSと同じ会社への二重露出】KRUS（くら寿司USA・短期戦略で保有中）は2695の子会社。
        #   両方持つと分散にならないので、2695を買うならKRUSを閉じてからにする。
        "2695（くら寿司・KRUSの親会社）": "2695.T",
        # --- 2026-09-12 週次スクリーニングv2 審査通過（米国株7・日本株6）---
        # ★塊の確認：①【プリント基板が三つ巴】4971メック(基板用薬品)＋6278ユニオンツール(基板用ドリル)＋
        #   6787メイコー(基板本体)＝同じ川上川下で同時に売られる。②【半導体が五つ巴】6526ソシオネクストが
        #   6920/6963ローム(保有)/6961/6787に加わった。③【住宅ローン・不動産金融が三つ巴】RKT＋PFSI＋WD。
        #   ④TGLS(建築用ガラス)は建材塊＋3110日東紡(ガラス繊維)と近い。⑤BILIは中国ADR(BABA/TME)。
        #   ⑥INFYはインド(HDB)。⑦AEOは消費関連塊。⑧7220武蔵精密は自動車でAPTVと同じ。
        "AEO（アメリカンイーグル・アパレル）": "AEO",
        "BILI（ビリビリ・中国ADR）": "BILI",
        "INFY（インフォシス・インドIT）": "INFY",
        "LEU（セントラス・エナジー・ウラン濃縮）": "LEU",
        "RKT（ロケット・住宅ローン）": "RKT",
        "TGLS（テクノグラス・建築用ガラス）": "TGLS",
        "UTI（ユニバーサル・テクニカル・職業訓練）": "UTI",
        "4784（GMOインターネット・旧GMOアドパートナーズ）": "4784.T",
        # --- 2026-09-19 週次スクリーニングv2 審査通過（米国株12・日本株1）---
        # ★塊の確認：①【中国ADRが五つ巴】BIDU＋QFIN＋BABA＋TME＋BILI＝規制と地政学で同時に飛ぶ。
        #   ②【インドが三つ巴】WIT＋INFY＋HDB。③【エネルギーが四つ巴】CRK(天然ガス)＋NRG(電力)＋
        #   LEU(ウラン濃縮)＋XLE。④GPIは自動車ディーラーでAPTV/7220と同じ川。
        #   ⑤FN(光通信EMS)はIPGP(レーザー)と近い。⑥LEGNは中国系バイオで規制リスクを共有する。
        "BIDU（百度・中国ADR）": "BIDU",
        "BSX（ボストン・サイエンティフィック・医療機器）": "BSX",
        "CALX（カリックス・ブロードバンド機器）": "CALX",
        "CRK（コムストック・天然ガス）": "CRK",
        "FN（ファブリネット・光通信EMS）": "FN",
        "GPGI（旧CompoSecure・決済カード/樹脂成形）": "GPGI",
        "GPI（グループ1オートモーティブ・自動車ディーラー）": "GPI",
        "LEGN（レジェンド・バイオテック）": "LEGN",
        "NRG（NRGエナジー・電力）": "NRG",
        "QFIN（奇富科技・中国フィンテック）": "QFIN",
        "SRAD（スポートレーダー・スポーツデータ）": "SRAD",
        "WIT（ウィプロ・インドIT）": "WIT",
        "4107（伊勢化学工業・ヨウ素/天然ガス）": "4107.T",
        # --- 2026-09-26 週次スクリーニングv2 審査通過（米国株7・日本株2）---
        # ★塊：TCOMは中国ADR＋旅行(TRIP)の二重塊／4970は半導体材料で半導体塊／5706は極薄銅箔でプリント基板塊／
        #   CIGI・CSGPは不動産でWD/RKT/PFSIと同じ川／PODDはBSXと医療機器／DYはCALXと通信設備投資
        "CIGI（コリアーズ・不動産サービス）": "CIGI",
        "CSGP（コスター・不動産データ）": "CSGP",
        "DY（ダイコム・通信インフラ工事）": "DY",
        "GPK（グラフィック・パッケージング・紙容器）": "GPK",
        "PODD（インスレット・インスリンポンプ）": "PODD",
        "TCOM（トリップドットコム・中国ADR）": "TCOM",
        "UPWK（アップワーク・フリーランス仲介）": "UPWK",
        "4970（東洋合成工業・フォトレジスト材料）": "4970.T",
        "5706（三井金属・極薄銅箔）": "5706.T",
        # --- 2026-10-03 週次スクリーニングv2 審査通過（米国株4・日本株2）＋9/18決定分の登録漏れ3件 ---
        # ★塊：PDD＝中国ADR／GDX・NEM＝金鉱株でコモディティ（GLD/SLV/COPX/1328保有）／1885＝建設／
        #   FSLR・ENPH＝太陽光／HUM＝医療保険でALHCと同じ／OKTA＝セキュリティでCRWDと同じ
        # ★HUM・ENPH・OKTAは9/18に株式部屋で登録を決めたがアプリ部屋に届いておらず、10/03に追加
        "FSLR（ファーストソーラー・太陽光パネル）🆕": "FSLR",
        "PDD（PDDホールディングス・中国ADR）🆕": "PDD",
        "GDX（金鉱株ETF）🆕": "GDX",
        "NEM（ニューモント・金鉱株最大手）🆕": "NEM",
        "HUM（ヒューマナ・医療保険MA）🆕": "HUM",
        "ENPH（エンフェーズ・太陽光インバーター）🆕": "ENPH",
        "OKTA（オクタ・ID管理/セキュリティ）🆕": "OKTA",
        "1885（東亜建設工業・海洋土木）🆕": "1885.T",
        "7383（ネットプロテクションズHD・後払い決済）🆕": "7383.T",
        "4971（メック・プリント基板用薬品）": "4971.T",
        "6235（オプトラン・光学薄膜成膜装置）": "6235.T",
        "6278（ユニオンツール・基板用ドリル）": "6278.T",
        "6526（ソシオネクスト・半導体設計）": "6526.T",
        "7220（武蔵精密工業・自動車部品）": "7220.T",
        # --- 2026-09-05 週次スクリーニングv2 審査通過（米国株4・日本株3）---
        # ★塊の確認：AAONは空調でLII（レノックス）と同じ塊＝買うなら択一。
        #   6366千代田化工はプラントエンジでACM/AMTM/1801/1835/1893の建設塊に合流。
        #   LULUは消費関連塊（NKE/ONON/GAP等）に合流。TMEは中国ADRでBABAと同じ塊。
        "AAON（エーオン・空調機器）": "AAON",
        "FICO（フェアアイザック・信用スコア）": "FICO",
        "LULU（ルルレモン・アパレル）": "LULU",
        "3110（日東紡績・ガラス繊維）": "3110.T",
        "4516（日本新薬・医薬品）": "4516.T",
        "6366（千代田化工建設・プラントエンジ）": "6366.T",
    },
    "📁 指数・コモディティ": {
        "BTC（ビットコイン）": "BTC-USD",
        "米10年金利": "^TNX",
        "S&P500": "^GSPC",
        "NASDAQ": "^IXIC",
        "FANG+（NYSE FANG+）": "^NYFANG",
        "日経平均": "^N225",
        "金（ゴールド）": "GC=F",
        "銀（シルバー）": "SI=F",
        "銅（COMEX銅先物・地形観察用）": "HG=F",
        "原油WTI": "CL=F",
        "VIX（恐怖指数）": "^VIX",
    },
}
# === 銘柄の並び順を自動整列（米国株=ティッカーのアルファベット順 → 日本株=証券コードの昇順）===
# 手作業で並べ替えると銘柄追加のたびに崩れるため、辞書は追加順のまま持ち、ここで機械的に並べ直す。
# 指数・コモディティは意味のある並び（株価指数→金利→商品）なのでソート対象外にする。
_NO_SORT_GROUPS = {"📁 指数・コモディティ"}

def _name_sort_key(ticker):
    """米国株を先(0)、日本株を後(1)に置き、米国はティッカー順・日本は証券コードの数値順にする"""
    if ticker.endswith(".T"):
        code = ticker[:-2]
        return (1, int(code) if code.isdigit() else 0, ticker)
    return (0, 0, ticker)

for _gname in list(GROUPS.keys()):
    if _gname in _NO_SORT_GROUPS:
        continue
    GROUPS[_gname] = dict(sorted(GROUPS[_gname].items(), key=lambda kv: _name_sort_key(kv[1])))

# === 📁監視を米国株・日本株に分割（2026-08-29・TODO④）===
# 監視が96件に増え、1つのラジオボタンでは縦に長すぎて目的の銘柄に辿り着けなくなったため。
# ★辞書リテラル自体は1つのまま持ち、ここで機械的に割る。リテラルを2つに割ると銘柄追加のたびに
#   「どっちに入れるか」を人間が判断することになり、入れ間違いと重複の温床になる。
#   分割の基準はティッカーの.Tサフィックスだけなので、追加時は今までどおり📁監視に足せばよい。
# ★件数をグループ名に埋めるので、追加すれば表示も自動で追随する。
_watch = GROUPS.pop("📁 監視")
_watch_us = {k: v for k, v in _watch.items() if not v.endswith(".T")}
_watch_jp = {k: v for k, v in _watch.items() if v.endswith(".T")}
_reordered = {}
for _k, _v in GROUPS.items():
    _reordered[_k] = _v
    if _k == "📁 保有中":  # 監視は保有中の直後に戻す（📁短期戦略はKRUS売却で2026-09-18に廃止）
        _reordered[f"📁 監視・米国株（{len(_watch_us)}）"] = _watch_us
        _reordered[f"📁 監視・日本株（{len(_watch_jp)}）"] = _watch_jp
GROUPS = _reordered

ALL_TICKERS = [(label, tk) for g in GROUPS.values() for label, tk in g.items()]

# 🔬対象外＝スコアが点いても買い判断に使わない銘柄。バケットの件数から除外する
# （件数が水増しされると「今日は何件見るべきか」の体感が狂うため）。表示自体は参考枠で残す。
# TTD＝バリュエーション・リセット型には大底スコアが効かないと決着済み（5年で30回以上点いて全外れ）。
# 数字だけ見ると理想形（大底9・週足8🎯・PER16倍・深度-83.8%）なので、疲れている時に
# 背景を思い出せず手が出る危険がある。タグは人間の記憶を当てにしないための装置として置く。
# 教材としての観察は失われない（見るのはEPSと月足downの2点で大底スコアとは無関係）。
# ★2026-08-24に1458.T・2869.Tを追加。どちらも2倍レバレッジETFでTSLL・SOXLと同じ穴。
#   逆張りシステムと構造的に噛み合わない＝保有が年単位（+100/300/500%の段階利確）なのに、
#   レバETFは日次リバランスのボラティリティ減衰で横ばい相場にいるだけで価値が減る。
#   「大底で買って戻るまで待つ」が最も苦手とする商品。バックテスト237取引も個別株ベース。
#   地図として見るのは自由で、裁量枠で触るならTSLLと同じ扱い。
EXCLUDED_TICKERS = {"SOXL", "QS", "TSLL", "TTD", "1458.T", "2869.T"}

# === 企業アクションによる指標汚染（2026-09-18追加）===
# ★yfinanceのauto_adjustは配当と株式分割は調整するが【スピンオフは調整しない】
#   （切り出された会社が別ティッカーになるため機械的に処理できない）。
#   汚染される指標＝深度／MA200乖離／6ヶ月リターン／RSI系＝つまり大底スコアの土台が丸ごと歪む。
# ★これを画面に出す理由＝点灯のたびに調べ直すのは非効率で、忘れると事故になるから。
#   手がかりは「高値からの経過日数」が企業アクションの日付と近いこと。
# ★汚染が解けたら（期限経過等）この辞書から消すこと。期限も本文に書いておく。
CORPORATE_ACTIONS = {
    "APTV": "🚨 **深度が汚染されている**のだ。2026-04-01にEDS（電装部門）をVersigent PLCとして"
            "スピンオフしたが、yfinanceは調整しないのだ。52週高値$88.63はEDS込みの旧APTV、"
            "現在値はEDS抜きの新APTV＝**別会社どうしを比べている**のだ。"
            "**真の深度は-30%前後**で-45%基準を通らないのだ（2026-08-31の点灯はこれが決定打で見送り）。"
            "★2027-04まで汚染が続くのだ",
    "7649.T": "⚠️ 2026-08-27に1:2株式分割。yfinanceが調整するので**株価系列そのものは正しい**が、"
              "分割当日は1日の変化率ガードが誤発火するのだ",
    "CRWD": "⚠️ 2026-07-02に1:4株式分割（基準日6/25）。yfinanceが調整するので株価系列は正しいが、"
            "分割当日は変化率ガードが誤発火するのだ。★GAAP赤字だが正体はSBCで、"
            "営業CF年$1.61B・FCF$1.24B＝倒産リスクなしと判断して2026-09-18に登録したのだ",
    "GPGI": "🚨 **系列の連続性を必ず確認**するのだ。汚染が3つ重なっているのだ——"
            "①2026-01-23に社名とティッカーを変更（旧CompoSecure・旧ティッカーCMPO）"
            "②同時期にHusky Technologiesを買収して事業構成が別物になった"
            "③2026-06にデラウェア→ネバダへ再法人化。"
            "**52週高値$26.78は旧CMPO時代を含む**ので、深度・MA200乖離・RSIが繋がっているか点灯時に見るのだ。"
            "★Q1のGAAP純損失-$235.0Mは買収の一時費用で、Q2は+$50.3M・通期FCFガイダンス$275〜325M＝"
            "BLDR型として2026-09-19に通過したのだ",
    "5706.T": "🚨 **1:10株式分割**（基準日2026-09-30・効力発生10-01・権利落ち9/29見込み）。"
              "yfinanceが調整するまでの数日間は**名目-90%の暴落として記録され、深度・MA200乖離・RSIが全部壊れる**のだ。"
              "**10月頭の点灯は無視する**（2026-09-26株式部屋決定）。調整を確認したらこの警告を消して通常扱いに戻すのだ",
    "4107.T": "ℹ️ 2025-12-29付（基準日2025-12-31）で1株→10株の株式分割。yfinanceが調整するので"
              "**株価系列は正しい**が、52週の窓に分割日が入っているのだ",
    "2695.T": "ℹ️ 2026-05-01に1:2株式分割。yfinanceが調整するので**汚染なし**なのだ",
    "ESAB": "ℹ️ 2022-03-29にColfaxからスピンオフして新規上場。新ティッカーなので**データ自体の汚染はない**が、"
            "上場4年ルールの起点がこの日で2026-03-29に4年経過＝ギリギリ通過だったのだ",
}

# 保有銘柄のティッカー集合（フル点灯の強調判定に使う）
HELD_TICKERS = set(GROUPS["📁 保有中"].values())

# === モメンタム柱で保有中の銘柄（出口ステータスの常時表示用）===
# 出口は「日足MA200割れで即売り」これのみ。利確ラインなし。
# MA200は日々動くので損切りラインは固定せず毎回この表示で更新して確認する。
# 銘柄を売ったらこの辞書から外す。買ったら {ティッカー: "表示名"} を追加する。
MOMENTUM_HELD = {
    "6963.T": "6963 ローム",
}

# ★★★ RSI方式＝Wilder方式に統一（2026-08-22切替・株式部屋の決定）★★★
# 旧実装は単純移動平均方式（Cutler's RSI, rolling(14).mean()）だったが、Colabのバックテスト
# （237取引・EV+30%・大底9の買いライン・週足<5の足切り・7-8最良帯）は全てWilder方式の上で
# 校正されている。つまりアプリの「大底9」はバックテストの「大底9」と別物を表示していた。
# SMA方式は14本の窓から古い足が抜けた瞬間に値が跳ねるため安値圏の極値に届きやすく、
# 検証していない「ギリギリの点灯」を余分に拾っていた可能性が高い（限界的な点灯＝最も弱い打席）。
# ★切替後は点灯が【減る】のが正常。増えたら実装ミスを疑うこと。
# ★保有銘柄（CPRI/ローム）はエントリー根拠の再判定をしない。出口ルールで管理済み。
# ★★権威の序列（2026-08-22に訂正）：①Colabのバックテスト（Wilder方式）が正 ②アプリはそれに揃える
#   ③楽天は【参考値】であり、ズレてもアプリが誤りとは限らない。
#   旧ルール「楽天とズレたら楽天を正とする」は無効。理由＝楽天にはRSI1（Wilder系）とRSI2（Cutler系）の
#   2種類があり、iSPEEDがどちらを表示しているか不明。さらに期間デフォルトが14でなく9のケースがある。
#   方式も期間も特定できない相手を「正」には据えられない。検算は下の🔍RSI検算パネルで自己完結させる。
def wilder_rsi(s, period=14):
    """Wilder方式のRSI（平滑化係数1/period・指数平滑）。アプリ内の全RSIはこの関数を通す。"""
    d = s.diff()
    gain = d.clip(lower=0).ewm(alpha=1.0/period, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1.0/period, adjust=False).mean()
    return 100 - (100 / (1 + gain / loss))

def completed_weekly_closes(s):
    """週足の終値系列を返す。★進行中の週は必ず落とす（2026-08-22に定義を統一）。
    【「完成週」の定義＝その週の最終取引日の引けが済んでいること。カレンダー週ではない】
      ・土日 → 直前の金曜バーは完成済みなので【含める】
      ・月〜金の取引時間中 → 当該週はまだ動くので【除外し、前週の確定バーを使う】
    カレンダー週（日曜まで）で判定すると土曜朝に当該週が未完成扱いとなり、
    完成済みの金曜バーを捨てて1週間古いデータで週足を計算してしまう（UTC時代のバグの正体）。
    ★この関数を作った理由＝同じ「週足RSI」が2つの値を持っていたため。
      旧実装ではload_data側（画面表示＋大底スコアの条件『週足RSI≤30』）が進行中の週を含み、
      週足スコア10条件は完成週のみで計算していた。わさびが点灯相談をするのは平日の朝
      （米国引け後）であり、その時間帯は進行中の週が月曜1日分だけで週足バーを作るため値が最も歪む。
      つまり【危ない時間帯に危ない値が使われる】設計だった。土日は3値が一致するので問題が見えないだけ。
    """
    c = s.resample("W-FRI").last().dropna()
    if len(c) == 0:
        return c
    if c.index[-1].normalize() >= pd.Timestamp(datetime.now(JST).date()):
        c = c.iloc[:-1]
    return c

# === ギャンスイング（2026-09-18追加・★視覚補助のみ）===
# ★★この計算結果は大底/天井スコア・週足スコア・アラート・コピー用サマリーに一切入らない。
#   入れていないことがこの機能の前提条件なので、将来スコアに混ぜたくなったら必ず株式部屋で決めること。
# 【ルール】判定は終値・描画はヒゲ（High/Low）・スイング本数3。
#   up中に終値が3本連続で切り下がったらdownへ転換／down中に3本連続で切り上がったらupへ転換。
#   「連続」は直前バーとの比較で厳密に</>。同値が出たらカウントをリセットする。
#   転換時、直前の区間で最高値（最安値）を付けたバーのHigh（Low）をスイング点として確定する。
def calc_gann_swing(cd, n=3):
    """ギャンスイングの折れ点を返す。
    戻り値: (confirmed, pending)
      confirmed = [(日付, 価格, "H"/"L", バー位置), ...] 確定したスイング点（実線で結ぶ）
      pending   = (日付, 価格) or None 最後の確定点から現在バーまでの未確定脚の終点（点線で結ぶ）
    ★未確定脚を点線にするのは【過去チャートが「完璧に天底を当てている」ように見える錯覚】を防ぐため。
      確定したスイング点は「後から振り返れば天底だった」点であり、その時点で分かっていたものではない。
      未確定脚を実線で描くと、いま進行中の脚まで当たっているように見えてしまう。省略禁止。"""
    if cd is None or len(cd) < n + 2:
        return [], None
    close = cd["close"].values
    high = cd["high"].values
    low = cd["low"].values
    idx = cd.index
    state = None          # 'up' / 'down'
    up_cnt = dn_cnt = 0
    seg_start = 0         # 現在の区間の起点（最後に確定したスイング点のバー位置）
    points = []
    for i in range(1, len(close)):
        if close[i] > close[i-1]:
            up_cnt += 1
            dn_cnt = 0
        elif close[i] < close[i-1]:
            dn_cnt += 1
            up_cnt = 0
        else:                     # 同値はカウントをリセット（厳密に</>で判定する）
            up_cnt = dn_cnt = 0
        if state is None:
            # 初期状態＝最初に3本連続が成立した方向で開始する
            if up_cnt >= n:
                state, seg_start, up_cnt, dn_cnt = "up", i, 0, 0
            elif dn_cnt >= n:
                state, seg_start, up_cnt, dn_cnt = "down", i, 0, 0
            continue
        if state == "up" and dn_cnt >= n:
            p = seg_start + int(np.argmax(high[seg_start:i+1]))   # up区間の最高値バー
            points.append((idx[p], float(high[p]), "H", p))
            state, seg_start, up_cnt, dn_cnt = "down", p, 0, 0
        elif state == "down" and up_cnt >= n:
            p = seg_start + int(np.argmin(low[seg_start:i+1]))    # down区間の最安値バー
            points.append((idx[p], float(low[p]), "L", p))
            state, seg_start, up_cnt, dn_cnt = "up", p, 0, 0
    if state is None or not points:
        return points, None
    # 未確定脚＝最後の確定点から現在バーまで。終点は進行方向のヒゲを使う
    last = len(close) - 1
    pending = (idx[last], float(high[last] if state == "up" else low[last]))
    return points, pending

def calc_envelope_line(points, kind, last_pos):
    """包絡線法でトレンドラインを引く（2026-09-18追加・★視覚補助のみ）。
    【定義】高値側＝全スイング高値がその線【以下】に収まる直線のうち、最も傾きの緩いもの。
            安値側＝全スイング安値がその線【以上】に収まる直線のうち、最も傾きの緩いもの。
    【計算】★必ずlog(価格)空間で行う。株価は比率で動くため線形空間で引くと、
            価格が高い時期ほど線が実態より近く見え、安い時期ほど遠く見えてズレる。
            対数軸トグルのオン/オフでこの線の位置は変わらない（変わるのは軸の見え方だけ）。
    【一意性】最後のスイング点を支点にして回すと、有効な線（全点が収まる線）の傾きには上限
            （高値側）または下限（安値側）があり、その境界がそのまま「最も傾きの緩い線」になる。
            よって2点で接する直線が一意に決まる＝どれを選ぶかの恣意性がない。
    戻り値: (x0, y0, x1, y1) バー位置と実価格 / None（スイング点が2つ未満）"""
    pts = [(pos, price) for _, price, k, pos in points if k == kind and price > 0]
    if len(pts) < 2:
        return None
    xs = np.array([p[0] for p in pts], dtype=float)
    ys = np.log(np.array([p[1] for p in pts], dtype=float))
    xn, yn = xs[-1], ys[-1]
    slopes = [(yn - y) / (xn - x) for x, y in zip(xs[:-1], ys[:-1]) if x < xn]
    if not slopes:
        return None
    slope = min(slopes) if kind == "H" else max(slopes)
    x0 = float(xs[0])
    x1 = float(max(last_pos, xn))          # 現在バーまで延長する
    y0 = yn + slope * (x0 - xn)
    y1 = yn + slope * (x1 - xn)
    return x0, float(np.exp(y0)), x1, float(np.exp(y1))

def completed_bars_for_swing(df, tf):
    """ギャンスイング用に【完成バーのみ】のOHLCを作る。
    日足＝そのまま／週足＝completed_weekly_closes()に準拠して未完成週を除外／月足＝未完成月を除外。
    ★進行中のバーを入れるとスイング点が翌日には別の位置に動くため、確定点の意味が壊れる。"""
    if tf == "日足":
        return df[["open", "high", "low", "close"]]
    rule = "W-FRI" if tf == "週足" else "ME"
    o = df["open"].resample(rule).first()
    h = df["high"].resample(rule).max()
    lo = df["low"].resample(rule).min()
    c = df["close"].resample(rule).last()
    bars = pd.DataFrame({"open": o, "high": h, "low": lo, "close": c}).dropna(subset=["close"])
    if len(bars) == 0:
        return bars
    today = pd.Timestamp(datetime.now(JST).date())
    if tf == "週足":
        # completed_weekly_closes()と同じ判定＝ラベルの金曜が今日以降なら進行中
        if bars.index[-1].normalize() >= today:
            bars = bars.iloc[:-1]
    else:
        # 月足＝ラベル(月末)が今日以降なら進行中の月
        if bars.index[-1].normalize() >= today:
            bars = bars.iloc[:-1]
    return bars

@st.cache_data(ttl=3600)
def load_data(ticker, period="5y"):
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # OHLC（4本値）を保持してローソク足描画に使う。指標は終値ベース
    keep = {}
    for src, dst in [("Open", "open"), ("High", "high"), ("Low", "low"), ("Close", "close"), ("Volume", "volume")]:
        if src in df.columns:
            keep[dst] = df[src]
    df = pd.DataFrame(keep)
    if "close" not in df.columns:
        return None
    # OHLCが欠ける指標(金利等)は終値で代用
    for col in ["open", "high", "low"]:
        if col not in df.columns:
            df[col] = df["close"]
    df = df.dropna(subset=["close"])
    if len(df) < 260:
        return None
    df["sma25"] = df["close"].rolling(25).mean()
    df["sma75"] = df["close"].rolling(75).mean()
    df["sma200"] = df["close"].rolling(200).mean()
    # RSIはWilder方式（2026-08-22統一・詳細はwilder_rsiのコメント参照）
    df["rsi"] = wilder_rsi(df["close"])
    # 週足RSI＝【完成週のみ】で計算する（2026-08-22統一）。
    # この値は画面上部の表示と、大底スコアの条件『週足RSI≤30』の両方に使われる。
    wk = completed_weekly_closes(df["close"])
    df["w_rsi"] = wilder_rsi(wk).reindex(df.index, method="ffill")
    df["bb_mid"] = df["close"].rolling(20).mean()
    bb_std = df["close"].rolling(20).std()
    df["bb_upper"] = df["bb_mid"] + 2*bb_std
    df["bb_lower"] = df["bb_mid"] - 2*bb_std
    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    df["roll_high"] = df["close"].rolling(252, min_periods=1).max()
    df["roll_low"] = df["close"].rolling(252, min_periods=1).min()
    df["drawdown_pct"] = (df["close"] - df["roll_high"]) / df["roll_high"] * 100
    df["rally_pct"] = (df["close"] - df["roll_low"]) / df["roll_low"] * 100
    closes = df["close"].values
    n = len(closes)
    d_high = [0]*n; d_low = [0]*n
    for i in range(n):
        s = max(0, i-252)
        win = closes[s:i+1]
        d_high[i] = (len(win)-1) - int(win.argmax())
        d_low[i] = (len(win)-1) - int(win.argmin())
    df["days_from_high"] = d_high
    df["days_from_low"] = d_low
    df["ma200_dev"] = (df["close"] - df["sma200"]) / df["sma200"] * 100
    if "volume" in df.columns:
        df["turnover_ma20"] = (df["close"] * df["volume"]).rolling(20).mean()
    else:
        df["turnover_ma20"] = np.nan
    return df

# === PER・PBR取得（trailingPE優先＋株価÷EPSでクロスチェック）===
# 注意：yfinanceの.infoは「現在時点のスナップショット」であり過去PERは取得できない。
# 赤字銘柄はtrailingPEがNone/負になるためN/A扱いとし、PBRを併記して判断材料にする。
@st.cache_data(ttl=3600)
def get_per_pbr(ticker):
    """PER・PBRを取得。
    戻り値: (per, pbr, is_estimated) ※is_estimated=Trueは株価÷EPSの手計算フォールバック"""
    try:
        info = yf.Ticker(ticker).info
        per = info.get("trailingPE")
        pbr = info.get("priceToBook")
        eps = info.get("trailingEps")
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        is_estimated = False
        # trailingPEが欠損 or 異常値なら株価÷実績EPSで再計算
        if (per is None or per <= 0) and eps and price and eps > 0:
            per = price / eps
            is_estimated = True
        if per is not None and per <= 0:
            per = None  # 赤字＝N/A扱い
        return per, pbr, is_estimated
    except Exception:
        return None, None, False

def calc_annual_vol(df):
    """年率ボラティリティ(%)を計算。VIX30時の銘柄選定（45%以上を選ぶ）用。
    直近252営業日の日次リターン標準偏差 × √252"""
    try:
        r = df["close"].pct_change().dropna()
        if len(r) < 60:
            return None
        return float(r.iloc[-252:].std() * np.sqrt(252) * 100)
    except Exception:
        return None

def check_liquidity(df, ticker):
    """20日平均売買代金が閾値以上か判定。
    ★2026-08-22修正（重要）：日本株の閾値を¥10億→【¥1億】へ戻した。
      8/20に「週次スクリーナーは日米共通$7M＝¥10億相当」という誤った記録に基づいて
      日本株を¥10億に引き上げてしまったが、スクリーナーの実設定は
      【米国=時価総額$1B・売買代金$7M／日本=時価総額300億円・売買代金1億円】で日米別基準だった。
      ¥10億のままだと日本株が軒並み「💧薄商い・ダマシ注意」と誤表示される。米国$7Mは正しいので据え置き。
      教訓＝設定値は推定で一般化せず、実際の設定画面を確認した値だけを書く。
    戻り値: (売買代金, 閾値以上か, 通貨記号)"""
    try:
        to = df["turnover_ma20"].iloc[-1]
        if pd.isna(to):
            return None, None, ""
        is_jp = (".T" in ticker) or ticker.startswith("^N")
        thr = 100_000_000 if is_jp else 7_000_000
        sym = "¥" if is_jp else "$"
        return float(to), bool(to >= thr), sym
    except Exception:
        return None, None, ""

def calc_bottom_score(r):
    checks = [
        ("RSI≤30（日足）", bool(pd.notna(r["rsi"]) and r["rsi"] <= 30), f"現在{r['rsi']:.1f}" if pd.notna(r["rsi"]) else "-"),
        ("BB下限タッチ", bool(pd.notna(r["bb_lower"]) and r["close"] <= r["bb_lower"]*1.05), ""),
        ("MA25を下回る", bool(pd.notna(r["sma25"]) and r["close"] < r["sma25"]), ""),
        ("MA200を下回る", bool(pd.notna(r["sma200"]) and r["close"] < r["sma200"]), ""),
        ("MACDヒスト<0", bool(pd.notna(r["macd_hist"]) and r["macd_hist"] < 0), ""),
        ("高値から-30%以上", bool(r["drawdown_pct"] <= -30), f"現在{r['drawdown_pct']:.1f}%"),
        ("高値から60日以上", bool(r["days_from_high"] >= 60), f"現在{int(r['days_from_high'])}日"),
        ("週足RSI≤30", bool(pd.notna(r["w_rsi"]) and r["w_rsi"] <= 30), f"現在{r['w_rsi']:.1f}" if pd.notna(r["w_rsi"]) else "-"),
        ("52週安値から±5%以内", bool(r["rally_pct"] <= 5), f"現在+{r['rally_pct']:.1f}%"),
        ("MA200から-20%以上乖離", bool(pd.notna(r["ma200_dev"]) and r["ma200_dev"] <= -20), f"現在{r['ma200_dev']:.1f}%" if pd.notna(r["ma200_dev"]) else "-"),
    ]
    return sum(1 for _,ok,_ in checks if ok), checks

def calc_top_score(r):
    checks = [
        ("RSI≥70（日足）", bool(pd.notna(r["rsi"]) and r["rsi"] >= 70), f"現在{r['rsi']:.1f}" if pd.notna(r["rsi"]) else "-"),
        ("BB上限タッチ", bool(pd.notna(r["bb_upper"]) and r["close"] >= r["bb_upper"]*0.95), ""),
        ("MA25を上回る", bool(pd.notna(r["sma25"]) and r["close"] > r["sma25"]), ""),
        ("MA200を上回る", bool(pd.notna(r["sma200"]) and r["close"] > r["sma200"]), ""),
        ("MACDヒスト>0", bool(pd.notna(r["macd_hist"]) and r["macd_hist"] > 0), ""),
        ("安値から+50%以上", bool(r["rally_pct"] >= 50), f"現在+{r['rally_pct']:.1f}%"),
        ("安値から60日以上", bool(r["days_from_low"] >= 60), f"現在{int(r['days_from_low'])}日"),
        ("MA200から+30%以上乖離", bool(pd.notna(r["ma200_dev"]) and r["ma200_dev"] >= 30), f"現在{r['ma200_dev']:.1f}%" if pd.notna(r["ma200_dev"]) else "-"),
        ("週足RSI≥70", bool(pd.notna(r["w_rsi"]) and r["w_rsi"] >= 70), f"現在{r['w_rsi']:.1f}" if pd.notna(r["w_rsi"]) else "-"),
    ]
    return sum(1 for _,ok,_ in checks if ok), checks

def calc_weekly_bottom_score(df):
    """週足バーで大底10条件を計算（検証2026-07-03：週足<5は足切り・7-8は資金厚めの材料・9は満点警戒）。
    完成した週足バーのみ使用（進行中の週は除外＝ルックアヘッド防止）。上位足チェックは月足RSI≤30。
    ★RSIはWilder方式（2026-08-22統一）。
    戻り値: (週足スコア, 週足フル判定可能か)"""
    try:
        # ★完成週の判定はcompleted_weekly_closes()に一本化（2026-08-22）。
        #   load_data側の週足RSIと同じ系列を見るので、同じ「週足RSI」が2つの値を持つ状態は解消済み。
        c = completed_weekly_closes(df["close"])
        if len(c) < 60:
            return None, False
        w = pd.DataFrame({"close": c})
        w["sma25"] = w["close"].rolling(25).mean()
        w["sma200"] = w["close"].rolling(200).mean()
        w["rsi"] = wilder_rsi(w["close"])
        mid = w["close"].rolling(20).mean()
        sd = w["close"].rolling(20).std()
        w["bb_lower"] = mid - 2*sd
        e12 = w["close"].ewm(span=12).mean()
        e26 = w["close"].ewm(span=26).mean()
        w["macd_hist"] = (e12-e26) - (e12-e26).ewm(span=9).mean()
        w["roll_high"] = w["close"].rolling(52, min_periods=1).max()
        w["roll_low"] = w["close"].rolling(52, min_periods=1).min()
        w["dd"] = (w["close"]-w["roll_high"])/w["roll_high"]*100
        w["rally"] = (w["close"]-w["roll_low"])/w["roll_low"]*100
        vals = w["close"].values
        n = len(vals)
        wfh = [0]*n
        for i in range(n):
            win = vals[max(0,i-52):i+1]
            wfh[i] = (len(win)-1) - int(win.argmax())
        w["wfh"] = wfh
        w["dev"] = (w["close"]-w["sma200"])/w["sma200"]*100
        m = df["close"].resample("ME").last().dropna()
        w["m_rsi"] = wilder_rsi(m).reindex(w.index, method="ffill")
        r = w.iloc[-1]
        score = 0
        score += 1 if (pd.notna(r["rsi"]) and r["rsi"] <= 30) else 0
        score += 1 if (pd.notna(r["bb_lower"]) and r["close"] <= r["bb_lower"]*1.05) else 0
        score += 1 if (pd.notna(r["sma25"]) and r["close"] < r["sma25"]) else 0
        score += 1 if (pd.notna(r["sma200"]) and r["close"] < r["sma200"]) else 0
        score += 1 if (pd.notna(r["macd_hist"]) and r["macd_hist"] < 0) else 0
        score += 1 if (r["dd"] <= -30) else 0
        score += 1 if (r["wfh"] >= 12) else 0
        score += 1 if (pd.notna(r["m_rsi"]) and r["m_rsi"] <= 30) else 0
        score += 1 if (r["rally"] <= 5) else 0
        score += 1 if (pd.notna(r["dev"]) and r["dev"] <= -20) else 0
        w_full = pd.notna(r["sma200"])
        return score, bool(w_full)
    except Exception:
        return None, False

@st.cache_data(ttl=3600)
def scan_all():
    """全銘柄スキャン。結果に加えて【取得メタ情報】も返す。
    戻り値: (results, meta)
      meta = {fetched_at: 取得実行時刻(JST), us_last: 米国株の最終足, jp_last: 日本株の最終足}
    ★取得時刻は必ずこのキャッシュ関数の【内側】で生成すること。
      外側でdatetime.now()を呼ぶと、実データが1時間前のキャッシュでも「今」と表示され、
      画面が「最新を見ている」という致命的な嘘をつくことになる。"""
    results = []
    us_last, jp_last = None, None
    for label, tk in ALL_TICKERS:
        try:
            d = load_data(tk, "5y")
            if d is None:
                continue
            bs, _ = calc_bottom_score(d.iloc[-1])
            ts, _ = calc_top_score(d.iloc[-1])
            results.append((label, tk, bs, ts))
            # 最終足の日付は市場ごとに集計する（日本は15時に引けている一方、米国は前営業日どまり）
            # ※load_data内でdropna済みなので末尾の空行を拾う心配はない
            idx = d.index[-1]
            if tk.endswith(".T") or tk.startswith("^N"):
                jp_last = idx if jp_last is None or idx > jp_last else jp_last
            elif tk not in ("BTC-USD",):  # 暗号資産は24時間動くので市場判定から外す
                us_last = idx if us_last is None or idx > us_last else us_last
        except Exception:
            continue
    meta = {"fetched_at": datetime.now(JST), "us_last": us_last, "jp_last": jp_last}
    return results, meta

# === フル点灯（大底10/10・天井9/9）の履歴を全銘柄ぶん集計（直近1年）===
@st.cache_data(ttl=3600)
def scan_full_history(days_back=365):
    """全登録銘柄について、直近days_back日のフル点灯（大底10/10・天井9/9）を集める。
    連続点灯はクラスタ化して1イベント1行にまとめる。各クラスタは点灯した最初の日を代表とする。"""
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days_back)
    events = []  # (date, label, ticker, kind, is_held)
    for label, tk in ALL_TICKERS:
        try:
            d = load_data(tk, "5y")  # ★scan_all(5y)のキャッシュを再利用＝再ダウンロードしない
            if d is None:
                continue
            raw_b = []
            raw_t = []
            for idx in range(260, len(d)):
                r = d.iloc[idx]
                dt = d.index[idx]
                if dt < cutoff:
                    continue
                # 早期スキップ：フル点灯は必須条件を満たさない日は数学的に不可能
                # 大底10/10にはRSI≤30が必須、天井9/9にはRSI≥70が必須
                rsi_v = r["rsi"]
                can_bottom = pd.notna(rsi_v) and rsi_v <= 30
                can_top = pd.notna(rsi_v) and rsi_v >= 70
                if not can_bottom and not can_top:
                    continue
                if can_bottom:
                    bs, _ = calc_bottom_score(r)
                    if bs >= 10:
                        raw_b.append(idx)
                if can_top:
                    ts, _ = calc_top_score(r)
                    if ts >= 9:
                        raw_t.append(idx)
            def clusterize(raw):
                if not raw:
                    return []
                clusters = []
                cur = [raw[0]]
                for x in raw[1:]:
                    if x - cur[-1] <= 10:
                        cur.append(x)
                    else:
                        clusters.append(cur)
                        cur = [x]
                clusters.append(cur)
                return [c[0] for c in clusters]
            is_held = tk in HELD_TICKERS
            for idx in clusterize(raw_b):
                events.append((d.index[idx], label, tk, "大底10/10", is_held))
            for idx in clusterize(raw_t):
                events.append((d.index[idx], label, tk, "天井9/9", is_held))
        except Exception:
            continue
    events.sort(key=lambda e: e[0], reverse=True)
    return events
# === モメンタムシグナル一覧（expander展開時のみ計算）===
@st.cache_data(ttl=3600)
def scan_momentum():
    """全登録銘柄のモメンタム判定を集計。判定に必要なのは6ヶ月上昇率とMA200のみなので
    直近200日あれば足りる。
    ★2026-08-29修正1（TODO③）：EXCLUDED_TICKERSを除外するようにした。
      旧実装は^VIXと^TNXしか弾いておらず、SOXL/TSLL/1458/2869のレバETFが買い一覧に並んでいた。
      レバETFは6ヶ月+50%を構造的に達成しやすいので上位を占め、逆張り側のバケットでは
      除外されているのにモメンタム側だけ素通りという非対称な状態だった。
      レバETFは日次リバランスのボラ減衰があり「MA200割れまで持つ」出口と噛み合わない。
    ★2026-08-29修正3：データ期間を2y→5yに変えた。ポップアップ実装で起動時に必ず走るようになったため、
      scan_all（5y）がダウンロード済みのキャッシュを再利用する必要がある。2yのままだと113銘柄を
      もう一度落としに行き起動が倍かかる。判定に使うのは直近200日なので結果は完全同一。
    ★2026-08-29修正2（TODO⑤）：MA200乖離率を戻り値に追加した。
      入口ルールの②【MA200乖離+18%以内】を画面側で判定するため。
      検証：乖離+18%以内でEV+23.0%・ペイオフ7.23倍（フィルターなしはEV+19.7%）。
    戻り値: (買いリスト, 売りリスト)
      買い=(label, ticker, 6ヶ月上昇率, is_held, MA200乖離率) ※乖離昇順（入口に適した順）
      売り=(label, ticker, 6ヶ月上昇率, is_held, MA200乖離率) ※保有を先頭"""
    buys, sells = [], []
    for label, tk in ALL_TICKERS:
        if tk in ("^VIX", "^TNX") or tk in EXCLUDED_TICKERS:
            continue
        try:
            d = load_data(tk, "5y")
            if d is None or len(d) < 200:
                continue
            c = d["close"]
            ma200 = c.rolling(200).mean().iloc[-1]
            price = c.iloc[-1]
            if pd.isna(ma200) or ma200 == 0 or len(c) < 127:
                continue
            ret_6m = (price - c.iloc[-127]) / c.iloc[-127] * 100
            dev = (price - ma200) / ma200 * 100
            is_held = tk in HELD_TICKERS
            if ret_6m >= 50 and price > ma200:
                buys.append((label, tk, ret_6m, is_held, dev))
            elif price < ma200:
                sells.append((label, tk, ret_6m, is_held, dev))
        except Exception:
            continue
    # ★並び順は【MA200乖離の小さい順】。上昇率降順にしないのは、上昇率が高い銘柄ほど
    #   MA200から離れており入口として不適だから（一番上に一番買ってはいけないものが来る）。
    buys.sort(key=lambda x: x[4])
    sells.sort(key=lambda x: (not x[3]))    # 保有を先頭に
    return buys, sells

# トレンドラインが効かない銘柄（暗号資産・高ボラ株）。これらはトレンド方向フィルター対象外
TREND_EXCLUDE = {"COIN","MSTR","MARA","CLSK","RIOT","BTDR","SOXL","QS","SOFI"}

@st.cache_data(ttl=3600)
def monthly_trend_direction(ticker, period="max"):
    """月足の移動チャネル（窓18ヶ月・相関0.3以上）で、直近のトレンド方向を判定。
    戻り値: 'up'（上昇）/ 'down'（下降）/ 'range'（レンジ）/ None（対象外・データ不足）
    ★2026-08-19のv2検証（3年レンズ・実測）：up +50.4% / range +54.2% / down +41.9%。
    　結論は【downを弱く減点するだけ。upを要求せず、rangeは満額で買ってよい】。
    　旧docstringの「EV+34.8%・勝率47%」はサンプルが薄く（up側n=4）、桁も実測と合わないため撤回した。
    　この関数の出力は見送りの決定打には使わないこと。"""
    if ticker in TREND_EXCLUDE:
        return None  # 暗号資産・高ボラ株はトレンドライン無効
    try:
        d = load_data(ticker, period)
        if d is None:
            return None
        s = d["close"].resample("ME").last().dropna()
        vals = s.values
        window = 18
        if len(vals) < window + 1:
            return None
        seg = vals[-window:]
        x = np.arange(len(seg))
        corr = np.corrcoef(x, seg)[0, 1]
        a, _ = np.polyfit(x, seg, 1)
        slope_pct = a / seg.mean() * 100
        if abs(corr) < 0.3:
            return "range"
        if slope_pct > 0.5:
            return "up"
        if slope_pct < -0.5:
            return "down"
        return "range"
    except Exception:
        return None

# === (え) モメンタム判定 ===
# 検証：暗号資産・高ボラ株で「過去6ヶ月+50%上昇かつMA200より上」が買い、「MA200割れ」が売り
# 全銘柄でフラットに表示（効かない銘柄も含めて経験として学ぶ方針）
def momentum_signal(df):
    """モメンタムシグナルを判定。★2026-09-18：引数をticker→dfに変えた。
    旧実装はload_data(ticker,"max")を呼んでおり、"5y"でダウンロード済みの銘柄を
    キャッシュキー違いでもう一度丸ごと落としていた（判定に使うのは直近200日だけなのに）。
    戻り値: 'buy'（6ヶ月+50%上昇かつMA200上）/ 'sell'（MA200割れ）/ None"""
    try:
        c = df["close"]
        if len(c) < 200:
            return None
        ma200 = c.rolling(200).mean().iloc[-1]
        price = c.iloc[-1]
        if pd.isna(ma200) or len(c) < 127:
            return None
        ret_6m = (price - c.iloc[-127]) / c.iloc[-127] * 100
        if ret_6m >= 50 and price > ma200:
            return "buy"
        if price < ma200:
            return "sell"
        return None
    except Exception:
        return None

@st.cache_data(ttl=3600)
def momentum_exit_status(ticker):
    """モメンタム柱の保有銘柄について、出口(日足MA200割れ)までの距離を算出。
    戻り値: dict{price, ma200, dev(乖離率%), dist(損切りまで何%下がるか), date} / None
    ※MA200は日々動くため損切りラインは固定せず、この表示で毎回更新して確認する。"""
    try:
        d = load_data(ticker, "5y")  # ★2y→5y。scan_allのキャッシュを再利用して二重取得を避ける
        if d is None or len(d) < 200:
            return None
        c = d["close"]
        ma200 = c.rolling(200).mean().iloc[-1]
        price = c.iloc[-1]
        if pd.isna(ma200) or ma200 == 0:
            return None
        dev = (price - ma200) / ma200 * 100      # MA200からの乖離率
        dist = (ma200 - price) / price * 100     # 現在値から損切りまでの下落幅
        return {"price": float(price), "ma200": float(ma200),
                "dev": float(dev), "dist": float(dist), "date": d.index[-1]}
    except Exception:
        return None

def calc_ret_6m(df):
    """6ヶ月（126営業日）上昇率。サマリー出力にモメンタムの実数を載せる用"""
    try:
        c = df["close"]
        if len(c) < 127:
            return None
        return float((c.iloc[-1] - c.iloc[-127]) / c.iloc[-127] * 100)
    except Exception:
        return None

# === (お) ダイバージェンス判定 ===
# 強気ダイバージェンス＝株価は安値更新だがRSI(14)は切り上げ かつ RSI<45
# 検証：月足=勝率79%（超強気の買い場サイン）、日足=勝率74%（補助）。週足は日足と大差なく不採用
# 重要：「待つサイン」ではなく「もう底・買い場のサイン」
# ★RSIはWilder方式に統一（2026-08-22）
def _detect_divergence(s):
    """直近で強気ダイバージェンスが発生しているか判定。発生していればTrue"""
    r = wilder_rsi(s)
    vals = s.values
    rvals = r.values
    n = len(vals)
    if n < 30:
        return False
    w = 3
    lows = []
    for i in range(max(w, n - 60), n - w):  # 直近60本以内の局所安値
        if vals[i] == vals[i - w:i + w + 1].min():
            lows.append(i)
    for k in range(1, len(lows)):
        ip, ic = lows[k - 1], lows[k]
        if np.isnan(rvals[ip]) or np.isnan(rvals[ic]):
            continue
        # 株価は安値更新（下げ）だがRSIは切り上げ かつ RSI<45
        if vals[ic] < vals[ip] and rvals[ic] > rvals[ip] and rvals[ic] < 45:
            return True
    return False

def divergence_signals(df):
    """月足・日足の強気ダイバージェンスを判定。★2026-09-18：引数をticker→dfに変えた
    （momentum_signalと同じく"max"の二重ダウンロードを廃止するため）。
    戻り値: dict {'monthly': bool, 'daily': bool}"""
    result = {"monthly": False, "daily": False}
    try:
        c = df["close"]
        result["daily"] = _detect_divergence(c)
        result["monthly"] = _detect_divergence(c.resample("ME").last().dropna())
    except Exception:
        pass
    return result

# === ここぞ判定（最強条件アラート用）===
# 検証で最強だった3つの強化条件：VIX30以上(EV+56%)・高ボラ(暗号資産EV+67%)・月足ダイバージェンス(勝率79%)
# 大底8以上を必須に、3つ揃う=案A(🔥確定演出)、2つ揃う=案B(⭐ここぞ)
def is_high_vol(df):
    """直近20日ボラが60日平均より高いか。★2026-09-18：引数をticker→dfに変えた"""
    try:
        c = df["close"]
        vol20 = c.pct_change().rolling(20).std()
        vol_ma = vol20.rolling(60).mean()
        v, vm = vol20.iloc[-1], vol_ma.iloc[-1]
        if pd.isna(v) or pd.isna(vm):
            return False
        return bool(v > vm)
    except Exception:
        return False

@st.cache_data(ttl=3600)
def get_vix_level():
    """現在のVIX水準を取得"""
    try:
        d = load_data("^VIX", "5y")
        return float(d["close"].iloc[-1]) if d is not None else None
    except Exception:
        return None

# ※旧check_strongest()はバケット表示への統合により廃止した。
# 🔥確定演出の判定（大底8＋VIX30＋高ボラ）はバケット振り分けの中で直接行っている。

# === 点灯銘柄の一括出力（複数選択→Markdownテーブル）===
# 母集団166銘柄では一斉点灯が起こりうるため、選んだ銘柄をまとめて表に出して相談を1往復で終わらせる。
# 短縮版＝PER点灯記録ログの列と完全一致（そのまま貼れる）、全項目版＝判断に使う指標を全部出す。
def _cluster_signals(d, kind="bottom", thr=9, gap=10):
    """点灯日をクラスタ化して「1山＝1イベント」に畳む共通処理。
    ★2026-08-20：同じ銘柄で点灯回数が2つの箇所で食い違う不具合を潰すため、
      数え方をここに一本化した（旧_count_bottom9_clustersは全集約、旧calc_signal_historyは
      フル点灯だけ集約せず個別に残していたので、CPRIのような常連銘柄で回数がズレていた）。
      検証4（初点灯か否か）は資金配分の根拠なので、回数のブレは判断のブレに直結する。
    戻り値: [(日付, 代表価格, そのクラスタ内の最高スコア), ...] 日付昇順
      代表価格＝大底なら最安値・天井なら最高値の日。最高スコアを持つので💎判定もできる。"""
    raw = []
    for idx in range(260, len(d)):
        r = d.iloc[idx]
        s = calc_bottom_score(r)[0] if kind == "bottom" else calc_top_score(r)[0]
        if s >= thr:
            raw.append((idx, d.index[idx], float(r["close"]), s))
    if not raw:
        return []
    clusters = []
    cur = [raw[0]]
    for item in raw[1:]:
        if item[0] - cur[-1][0] <= gap:
            cur.append(item)
        else:
            clusters.append(cur)
            cur = [item]
    clusters.append(cur)
    out = []
    for c in clusters:
        best = min(c, key=lambda x: x[2]) if kind == "bottom" else max(c, key=lambda x: x[2])
        out.append((best[1], best[2], max(x[3] for x in c)))
    out.sort(key=lambda x: x[0])
    return out

def _count_bottom9_clusters(d):
    """その銘柄で大底9以上が過去に何回点灯したかを数える（10営業日以内の連続は1回に集約）。
    検証4「その銘柄で初の大底9か」の自動判定に使う。★数え方は_cluster_signalsに統一済み。"""
    return len(_cluster_signals(d, kind="bottom", thr=9))

@st.cache_data(ttl=3600)
def bulk_signal_row(ticker, period="5y"):
    """一括出力テーブル1行分のデータをまとめて取得する。
    戻り値: dict / None（データ不足）"""
    try:
        d = load_data(ticker, period)
        if d is None:
            return None
        r = d.iloc[-1]
        bs, _ = calc_bottom_score(r)
        ts, _ = calc_top_score(r)
        ws, _ = calc_weekly_bottom_score(d)
        per, pbr, per_est = get_per_pbr(ticker)
        trend = monthly_trend_direction(ticker, "5y")  # ★"max"だと二重ダウンロードになる
        div = divergence_signals(d)
        to, liq, tsym = check_liquidity(d, ticker)
        n9 = _count_bottom9_clusters(d)
        return {
            "date": d.index[-1].strftime("%Y-%m-%d"),
            "price": float(r["close"]), "sym": tsym or ("¥" if ".T" in ticker else "$"),
            "bs": bs, "ts": ts, "ws": ws,
            "per": per, "pbr": pbr, "per_est": per_est,
            "trend": trend, "div_m": div["monthly"], "div_d": div["daily"],
            "dd": float(r["drawdown_pct"]), "dev": float(r["ma200_dev"]) if pd.notna(r["ma200_dev"]) else None,
            "rally": float(r["rally_pct"]), "dfh": int(r["days_from_high"]),
            "avol": calc_annual_vol(d), "ret6": calc_ret_6m(d),
            "to": to, "liq": liq,
            "n9": n9, "highvol": is_high_vol(d),
        }
    except Exception:
        return None

@st.cache_data(ttl=3600)
def bucket_row_info(ticker):
    """バケット表示の1行に出す4項目（週足スコア・月足トレンド・年率ボラ）を取得。
    判断を決めているのは実質この4つ（買いライン大底9・足切り週足5・決定打は月足・VIX30時はボラ45%以上）。
    ※月足トレンドは5yデータで判定する（窓18ヶ月なので十分・maxを使うと二重ダウンロードになり遅い）"""
    try:
        d = load_data(ticker, "5y")
        if d is None:
            return {"ws": None, "trend": None, "avol": None}
        ws, _ = calc_weekly_bottom_score(d)
        return {"ws": ws,
                "trend": monthly_trend_direction(ticker, "5y"),
                "avol": calc_annual_vol(d),
                "highvol": is_high_vol(d)}   # ★高ボラ判定もここに畳んだ（旧is_high_vol(ticker)の重複呼び出しを廃止）
    except Exception:
        return {"ws": None, "trend": None, "avol": None, "highvol": False}

def _fmt_ws(ws):
    """週足スコアを帯の意味つきで文字列化（<5💧足切り／7-8🎯最良帯／9⚠️満点警戒）"""
    if ws is None:
        return "-"
    if ws < 5:
        return f"{ws}💧"
    if ws >= 9:
        return f"{ws}⚠️"
    if ws >= 7:
        return f"{ws}🎯"
    return str(ws)

st.title("📈 大底・天井スコア")
st.caption("大底10条件・天井9条件 | 買い:スコア9+ 売り:天井8+ | RSI=Wilder方式（2026-08-22統一）")

# === 更新ボタン（放置でフリーズ・文字が白くなる対策）===
# 押すとキャッシュを全クリアして最新データで再実行する
if st.button("🔄 データ更新（最新の株価を取り直す）", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

with st.expander("📖 運用ルール（必ず確認）"):
    st.markdown("""
**シグナル点灯時**: まず売買せずClaudeに相談。買いは3分割(0/+15/+30営業日)各1/3。損切りSL-15%固定、利確は値幅段階+100/300/500%(守り銘柄のみTP+50%)、保有は年単位(長いほどEVが高い)。★180日撤退は旧ルールで廃止済み。
**出口の序列**: 暗号資産系=恩株化(+46%) / 指数優良株=値幅段階利確 / モメンタム柱=日足MA200割れ終値のみ(天井シグナルも利確ラインもなし) / KRUS等チャネル系=地形の上辺で売る。
**集中リスク**: 暗号資産系(COIN/MSTR/MARA/CLSK)は1銘柄まで。半導体系は**柱ごとに1銘柄まで**（2026-09-26統一）。★モメンタム柱＝6963ローム保有中で**埋まっている**のだ。★逆張り柱＝**空き**。SOXL／NVDA／AMD／6920レーザーテック／6961エンプラス／6787メイコー／6526ソシオネクスト／4970東洋合成の中から**どれか1つだけ**買えるのだ。★【防衛が三つ巴】KTOS／LDOS／AVAV＝同じく1つだけ。★**「1銘柄まで」の上限があるのはこの3つ（暗号資産・半導体・防衛）だけ**なのだ。下の「同じ塊」は上限ではなく注意なのだ。
**低ボラ側(資金を厚くしない)**: GLD/JNJ/PG/1345(Jリート指数ETF)は💎検証で「VIX30でも成績が改善しない」側。登録は自由だが厚く張る対象ではない。
**優待銘柄(別財布)**: 8136サンリオ／3549クスリのアオキ／4661オリエンタルランド／7615京都きもの友禅HD。買う目的が優待なら逆張りシステムの土俵外＝大底スコア/月足トレンド/損切り-15%/利確ラインは適用しない。
**未検証(⚠️)**: SOFIは売買対象外・参考表示のみ。上場4年未満も対象外。
**🔬対象外と落第履歴は別物**: 🔬対象外=**登録済みだが買わないと決めた（恒久）**／落第履歴=**審査して登録しなかった（再審査ありうる）**。性質が違うので混ぜないのだ。落第履歴は株式部屋が持つのだ。
**赤字の判定は経常損益で見る**: 純損益だけ見ると一時費用で赤字の優良企業を落としてしまうのだ。★BLDR型=本業が黒字で、その下の一時費用（IRS和解の税費用$43.9M）で赤字→**通過**。★7412アトム型=営業+25百万だが**経常-22百万で赤字**、そこに減損677百万が乗って純損失15.07億→**落第**。★QXO型=営業段階で赤字→**落第**。判定は経常損益が実務的なのだ。
**検証済(対象外)**: SOXL/QS/TSLL/TTD/1458/2869は🔬対象外＝バケットの件数と一括出力に含めない。SOXL=レバETFゆえ🔥確定演出級のみC枠SL必須・VIX<25の点灯は無視（VIX≥25限定で9戦7勝EV+36.7%／VIX<25は4戦全敗）。QS=赤字構造でSTEP2弾き。TSLL=システム外の裁量枠（別財布）で登録目的は$7割れの検知のみ。TTD=バリュエーション・リセット型（PER297倍→17倍の縮小がそのまま-89%の株価下落に一致）で大底スコアが効かないと決着済み・観察はEPSと月足downの2点のみ。
**MP（レアアース）**: 通常より厳しい買い条件＝大底9＋できればVIX25以上。地形は整いつつあり押しを待つ段階。★月足upの要求は撤回済み（v2検証でrange≧upと判明したため）。
**優待バケット(8136サンリオ/3549クスリのアオキ)**: 逆張りシステムの土俵外・別財布。大底スコア/月足トレンド/損切り-15%/利確ラインは適用しない（売らずに握るので出口が存在しない）。8136のトリガーは800円台・指値は置かず監視のみ。
**モメンタム柱**: 出口はMA200割れで即売りのみ。利確ラインなし。最上部の出口ステータスで損切りラインを毎回更新して確認する。
**🆕銘柄**: 2026-10-03の週次スクリーニング通過組（6件）＋9/18決定分の登録漏れ3件（HUM/ENPH/OKTA）。プール入場審査は通過済みだが実弾は点灯待ち。★BLDR（8/29組）はIRS和解の一時費用で会計上は赤字だが営業利益は黒字＝「一時費用による赤字」と「本業の赤字」は別物として通した実例。
**同じ塊に注意（分散したつもりで分散できていない）**: ①消費関連=FLO/GAP/WING/GME/NKE/ONON/ZTS/POST/PPC/TRIP/LULU/AEO/8267　②建材・住宅・建設=BLDR/SITE/LII/PNR/AAON/ACM/AMTM/TGLS/1801/1835/1885/1893/6366　③コモディティ=GLD/SLV/COPX/GDX/NEM（＋1328保有）　④中国ADR=BABA/TME/BILI/BIDU/QFIN/TCOM/PDD（LEGNも中国系バイオで規制リスクを共有・TCOMはTRIPとも旅行で重なる）　⑤プリント基板=4971メック(薬品)/6278ユニオンツール(ドリル)/5706三井金属(極薄銅箔)/6787メイコー(基板本体)＝川上から川下まで同じ需要で動く　⑥住宅ローン・不動産=RKT/PFSI/WD/CIGI/CSGP　⑦インド=HDB/INFY/WIT　⑧エネルギー=XLE/CRK(天然ガス)/NRG(電力)/LEU(ウラン濃縮)　⑨自動車=APTV/7220武蔵精密/GPI(ディーラー)　⑩光通信=IPGP/FN　⑪医療機器=BSX/PODD　⑫通信設備投資=CALX(機器)/DY(工事)　⑬太陽光=FSLR/ENPH　⑭医療保険=ALHC/HUM　⑮セキュリティ=CRWD/OKTA。★空調はLIIとAAONが直接の競合なのだ。**これらは上限ではなく注意**＝VIX30では塊ごと同時点灯するので、複数買うと分散したつもりで分散になっていないのだ（2026-09-26に記述を是正）。
**★★2695くら寿司とKRUSは親子会社**: KRUSは2695の子会社。両方持つのは分散ではなく同じ会社への二重露出なのだ。★KRUSは2026-09に逆指値発動で売却済みなので、現在この衝突は解消しているのだ（📁短期戦略はこれに伴い廃止）。
**企業アクション汚染**: APTV/GPGI/5706/7649/CRWD/4107/2695/ESABは企業アクションの影響を受けているのだ。該当銘柄を開くと画面に警告が出るのだ。★特にAPTVはスピンオフをyfinanceが調整しないため**深度が丸ごと嘘**で、真の深度は-30%前後なのだ（2027-04まで）。
**週次スクリーナー条件(2026-08-22改定)**: RSI(14)31〜45 / 52週高値から【-45%以上】/ MA200乖離-15%以下 / 米国=時価総額$1B・売買代金$7M / 日本=時価総額300億円・売買代金1億円。深度を-30%→-45%に締めたのは-50〜-30%が3年到達率17.3%の最弱帯だったため。
**銘柄の保有/監視の移動**: 売買したらClaudeに相談ついでに伝えてコードを直してもらう運用。
""")

with st.spinner("登録銘柄をスキャン中（初回は85秒ほど）..."):
    scan, scan_meta = scan_all()

# === データの鮮度表示（2026-08-18追加）===
# 目的は「ズレを埋めること」ではなく【ズレていることが分かる状態にすること】。
# アプリは確定した日足で動かすのが正しく、ザラ場データを入れるとスコアが分刻みで揺れる
# （8/17にMMSが数分で大底9→8、ACMが週足4→8に振れた実例あり）。リアルタイム化は判断を悪くする。
# ここで確認したいのは【見たかった終値がちゃんと入っているか】＝朝6時に開いた画面が
# 前日の引けなのか前々日どまりなのかを区別できること。
_fa = scan_meta.get("fetched_at")
_us, _jp = scan_meta.get("us_last"), scan_meta.get("jp_last")
_freshness = f"🕒 取得 {_fa.strftime('%m-%d %H:%M')} JST" if _fa is not None else "🕒 取得時刻 -"
_freshness += f"　／　最終足 米国 {_us.strftime('%m-%d')}引け" if _us is not None else "　／　最終足 米国 -"
_freshness += f"・日本 {_jp.strftime('%m-%d')}引け" if _jp is not None else "・日本 -"
st.caption(_freshness)

# 米国市場の取引時間中（日本時間22:30〜翌5:00）は確定値ではない旨を警告する。
# 「判断は米国市場の引け後（日本時間の朝）に行う」という運用ルールを画面側で担保する装置。
_now_jst = datetime.now(JST)
_hm = _now_jst.hour * 60 + _now_jst.minute
if _hm >= 22 * 60 + 30 or _hm < 5 * 60:
    st.warning("⚠️ 今は米国市場の取引時間中なのだ。表示中の米国株スコアは**前営業日の確定値**で、"
               "今まさに動いている値動きは反映されていないのだ。判断は米国の引け後（日本時間の朝）に行うのだ")

# === 最上段：大底スコア別バケット表示（2026-08-18に全面統合）===
# 背景：母集団166銘柄では凪でも点灯が画面を埋め、VIX30の暴落時は数十件になって破綻する。
# よって点灯を「一覧」でなく「スコア別の束」にした。点灯銘柄は該当バケットに自動で積まれるので
# 枠を作る作業は不要（VIX30で30件来たら大底9の枠が伸びるだけ）。
# 旧「ここぞアラート枠」と「通常点灯枠」で同じ銘柄を2箇所に出していた二重表示はこれで解消。
_FONT_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Mochiy+Pop+One&display=swap');
.kakutei-box{background:linear-gradient(135deg,#3a0a0a,#6e1010);border:1.5px solid #ff4040;
 border-radius:9px;padding:9px 12px;margin-bottom:6px;box-shadow:0 0 10px rgba(255,50,50,0.4);
 font-family:'Mochiy Pop One',sans-serif;}
.kakutei-ttl{font-size:17px;color:#fff;text-shadow:0 0 6px #ff4040;margin-bottom:3px;}
.kakutei-bdy{font-size:12px;line-height:1.45;color:#ffd8d8;}
.kakutei-ev{color:#ffd040;}
.held-tag{background:#1a4a2a;color:#5fe;font-size:10px;padding:0 5px;border-radius:3px;margin-right:4px;}
.mom-box{background:linear-gradient(135deg,#0a2a1a,#10502e);border:1.5px solid #34d399;
 border-radius:9px;padding:9px 12px;margin-bottom:6px;box-shadow:0 0 10px rgba(52,211,153,0.35);
 font-family:'Mochiy Pop One',sans-serif;}
.mom-ttl{font-size:16px;color:#fff;text-shadow:0 0 6px #34d399;margin-bottom:3px;}
.mom-bdy{font-size:12px;line-height:1.45;color:#d8ffe8;}
.mom-ev{color:#ffd040;}
</style>"""

_vix_now = get_vix_level()
_vix30 = (_vix_now is not None and _vix_now >= 30)

# --- バケットへの振り分け ---
# 🔥確定演出（大底8＋VIX30＋高ボラの両方）は最上段の別枠に出し、バケットからは除外＝二重表示を防ぐ
_kakutei = []
_buckets = {10: [], 9: [], 8: []}
_excluded_lit = []
for _lb, _tk, _bs, _ts in scan:
    if _bs < 8 or _tk in ("^VIX", "^TNX"):
        continue
    _short = _lb.split("（")[0].strip()
    _info = bucket_row_info(_tk)
    _conds = []
    if _vix30:
        _conds.append("VIX30")
    if _info.get("highvol"):
        _conds.append("高ボラ")
    _row = {"short": _short, "tk": _tk, "bs": _bs, "conds": _conds,
            "held": _tk in HELD_TICKERS, "info": _info}
    if _tk in EXCLUDED_TICKERS:
        _excluded_lit.append(_row)
        continue
    if len(_conds) >= 2:
        _kakutei.append(_row)
        continue
    _buckets[10 if _bs >= 10 else _bs].append(_row)

# 並び順：各バケット内で週足スコア降順 → 同点は名前順（米国=アルファベット／日本=コード順）
# 名前順を最優先にしない理由＝点灯枠の用途は「探す」でなく「どれを見るべきか」だから。
# 同点を名前順にすると毎回同じ並びになり前日との見比べもしやすい。
def _bucket_sort(rows):
    return sorted(rows, key=lambda r: (-(r["info"]["ws"] if r["info"]["ws"] is not None else -1),
                                       _name_sort_key(r["tk"])))

_TREND_MARK = {"up": "up📈", "down": "down📉", "range": "range➡️"}

def _render_row(r):
    """1行＝銘柄／週足／月足／年率ボラ。⭐は独立アラートを廃止して行内バッジに格下げした。
    理由＝VIX30が来ない限り⭐は実質「高ボラ単独」で点いており、これはただの属性だから。"""
    i = r["info"]
    ws = _fmt_ws(i["ws"])
    tr = _TREND_MARK.get(i["trend"], "対象外")
    av = f"{i['avol']:.0f}%" if i["avol"] is not None else "-"
    tags = ""
    if r["held"]:
        tags += " `保有`"
    if r["tk"] in CORPORATE_ACTIONS:
        # 🚨（深度が実際に歪んでいる）だけ一覧に出す。ℹ️と⚠️は個別画面で見れば足りる
        tags += " `🚨企業アクション`" if CORPORATE_ACTIONS[r["tk"]].startswith("🚨") else " `⚠️企業アクション`"
    if r["conds"]:
        tags += f" `⭐{'/'.join(r['conds'])}`"
    return f"- **{r['short']}**　週足 {ws}　月足 {tr}　ボラ {av}{tags}"

# --- 🔥確定演出（常時最上段・別枠）---
if _kakutei:
    _parts = [_FONT_CSS]
    for r in _bucket_sort(_kakutei):
        hm = '<span class="held-tag">保有</span>' if r["held"] else ""
        _parts.append(f'<div class="kakutei-box"><div class="kakutei-ttl">🔥 確定演出：{hm}{r["short"]}（大底{r["bs"]}）</div>'
            f'<div class="kakutei-bdy">VIX30＋高ボラが揃った → 歴史的暴落の底。'
            f'<span class="kakutei-ev">検証EV+45%(暗号資産+84%)</span>。損切りライン決めて即行動を検討！</div></div>')
    st.markdown("".join(_parts), unsafe_allow_html=True)
    st.toast("🔥 確定演出！買い場確定！", icon="🔥")
    st.caption("※確定演出の銘柄は下のバケットからは除外して表示しているのだ（二重表示を防ぐため）")

# --- スコア別バケット ---
_n10, _n9, _n8 = len(_buckets[10]), len(_buckets[9]), len(_buckets[8])
_vix_txt = f"VIX {_vix_now:.1f}" if _vix_now is not None else "VIX -"
st.markdown(f"<div style='font-size:0.82em;font-weight:700;margin:4px 0;'>🚨 大底スコア別バケット（{_vix_txt}／{len(scan)}銘柄スキャン済み）</div>", unsafe_allow_html=True)

if _n10 + _n9 + _n8 + len(_kakutei) == 0:
    st.success("✅ 本日の点灯なし（大底8以上ゼロ）。凪の日は出番なしで正常運転なのだ")
else:
    # 💎大底10（満点）＝展開。※満点は大底9より-11ptなので「深いほど良い」ではない点に注意
    if _n10:
        with st.expander(f"💎 大底10（{_n10}件）", expanded=True):
            for r in _bucket_sort(_buckets[10]):
                st.markdown(_render_row(r))
            st.caption("満点10は大底9より-11pt（💎の用途は視認性のみ）。買いラインはあくまで9なのだ")
    # 🎯大底9（買いライン）＝展開
    if _n9:
        with st.expander(f"🎯 大底9（{_n9}件）＝買いライン", expanded=True):
            for r in _bucket_sort(_buckets[9]):
                st.markdown(_render_row(r))
            st.caption("買いラインはここ。週足<5は足切り・VIX30時はボラ45%以上を取るのだ。"
                       "月足downは**弱い減点**にとどめる（3年EV+41.9%＝見送りの決定打にはしないのだ）")
    # 大底8（未達）＝折りたたみ
    if _n8:
        with st.expander(f"大底8（{_n8}件）＝買いライン未達", expanded=False):
            for r in _bucket_sort(_buckets[8]):
                st.markdown(_render_row(r))
            st.caption("大底8は定義上まだ未達。週足スコアの改善追跡と再点灯候補の発掘に使うのだ")

# --- 🔬対象外の点灯（件数には含めない参考枠）---
if _excluded_lit:
    with st.expander(f"🔬 対象外銘柄の点灯（参考・{len(_excluded_lit)}件）", expanded=False):
        for r in _bucket_sort(_excluded_lit):
            st.markdown(_render_row(r))
        st.caption("SOXLはVIX≥25限定で検討可・QSとTSLLとTTDは買い判断に使わないのだ"
                   "（TSLLは$7割れの検知用／TTDはバリュエーション・リセット型で大底スコアが効かないと決着済み）")

# === 🚀 モメンタム買いシグナルのポップアップ（2026-08-29追加・TODO②⑤）===
# 逆張り柱は大底バケットで毎朝目に入るのに、モメンタム柱は折りたたみの中にあり
# 「開かなければ気づかない」状態だった。柱が2本ある以上、点灯の可視性も2本とも同じにする。
# ★ここに出すのは【入口ルール②MA200乖離+18%以内】を満たすものだけ。
#   検証：乖離+18%以内でEV+23.0%・ペイオフ7.23倍（フィルターなしはEV+19.7%）。
#   +18%を超えたものは折りたたみの一覧には残るが、ポップアップでは呼ばない
#   （名前を毎朝見せられると「そろそろ押した頃では」と手が出るため＝感情トレードの型②）。
_mom_buys_top, _mom_sells_top = scan_momentum()
_mom_ok = [b for b in _mom_buys_top if b[4] <= 18 and not b[3]]
if _mom_ok:
    _mp = [_FONT_CSS]
    for _lb, _mtk2, _r6, _hd, _dev in _mom_ok[:5]:
        _mp.append(
            f'<div class="mom-box"><div class="mom-ttl">🚀 モメンタム買い点灯：{_lb.split("（")[0].strip()}</div>'
            f'<div class="mom-bdy">6ヶ月 <b>{_r6:+.0f}%</b>　MA200乖離 <b>{_dev:+.1f}%</b> ✅+18%以内　'
            f'<span class="mom-ev">検証EV+23.0%・ペイオフ7.23倍</span></div></div>')
    st.markdown("".join(_mp), unsafe_allow_html=True)
    st.toast(f"🚀 モメンタム買い点灯（適格{len(_mom_ok)}件）", icon="🚀")
    st.caption("※買う前に残りの入口ルールを確認するのだ：③黒字　④集中ルール非抵触　⑤決算をまたがない　"
               "⑥終値ベース　⑦1銘柄¥1〜2万（Tier C）　⑧同時保有2銘柄まで。"
               "中央値はほぼゼロで利益は右の裾から来るホームラン型なのだ")

# --- ⛔天井シグナル（保有銘柄でのみ意味を持つ）---
_tops = []
for _lb, _tk, _bs, _ts in scan:
    if _ts >= 7 and _tk not in ("^VIX", "^TNX"):
        _tops.append((_lb.split("（")[0].strip(), _tk, _ts, _tk in HELD_TICKERS))
if _tops:
    _tops.sort(key=lambda x: (-x[2], _name_sort_key(x[1])))
    _held_top = [t for t in _tops if t[3]]
    with st.expander(f"⛔ 天井シグナル（{len(_tops)}件"
                     + (f"・うち保有{len(_held_top)}件" if _held_top else "") + "）", expanded=bool(_held_top)):
        for _s, _tk, _ts, _hd in _tops:
            _mk = "⛔フル" if _ts >= 9 else ("🔴売り" if _ts == 8 else "⚠️警戒")
            if _hd:
                st.markdown(f"- **{_s}**　{_mk}（{_ts}/9）　`保有`")
            else:
                st.markdown(f"- {_s}　{_mk}（{_ts}/9）")
        st.caption("天井のビタ当ては不可能(AUC0.549)で天井売りは早売り。モメンタム柱の出口はMA200割れのみ、"
                   "逆張りは含み益＋天井の時だけ意味を持つのだ")

# === モメンタム柱の出口ステータス（常時表示）===
# 出口はMA200割れで即売り、これのみ。利確ラインなし。
# MA200は日々動くので損切りラインは固定せず、ここで毎回更新して確認する。
# 監視頻度＝乖離が大きいうちは週次、MA200に近づいたら日次に切り替える二段構え。
if MOMENTUM_HELD:
    st.divider()
    st.markdown("<div style='font-size:0.85em;font-weight:700;margin:2px 0;'>🚀 モメンタム柱の出口ステータス（出口はMA200割れのみ）</div>", unsafe_allow_html=True)
    for _mtk, _mname in MOMENTUM_HELD.items():
        _ms = momentum_exit_status(_mtk)
        if _ms is None:
            st.warning(f"{_mname}：データ取得に失敗したのだ（次の更新で再取得される）")
            continue
        _msym = "¥" if (".T" in _mtk or _mtk.startswith("^N")) else "$"
        _mc = st.columns(4)
        _mc[0].metric(f"{_mname} 現在値", f"{_msym}{_ms['price']:,.0f}")
        _mc[1].metric("日足MA200（損切りライン）", f"{_msym}{_ms['ma200']:,.0f}")
        _mc[2].metric("MA200乖離率", f"{_ms['dev']:+.1f}%")
        _mc[3].metric("損切りまで", f"{_ms['dist']:+.1f}%")
        if _ms["dev"] < 0:
            st.error(f"🚨 **{_mname}：MA200を割れた（乖離{_ms['dev']:+.1f}%）→ 出口条件成立。即売りを執行するのだ**")
        elif _ms["dev"] < 10:
            st.warning(f"⚠️ {_mname}：MA200まであと{_ms['dist']:.1f}%＝接近中。**監視を日次に切り替え**るのだ")
        elif _ms["dev"] < 20:
            st.info(f"📊 {_mname}：MA200まであと{_ms['dist']:.1f}%。そろそろ日次監視への切り替えを意識するのだ")
        else:
            st.caption(f"✅ {_mname}：乖離{_ms['dev']:+.1f}%と余裕あり＝**週次監視で十分**なのだ（データ最終日 {_ms['date'].strftime('%Y-%m-%d')}）")

# === 点灯銘柄の一括出力（複数選択→Markdownテーブル）===
# 一斉点灯時に1銘柄ずつ相談すると往復が増えるため、選んだ銘柄をまとめて表に出す。
# ★🔬対象外（SOXL/QS/TSLL/TTD/1458.T/2869.T）はここにも出さない＝構造的な土俵外なので選択肢に並べない。
#   （旧「分析済みチェック」は相談対象を大底9以上に絞ったことで不要になったため廃止した。
#     恒久的に外したい銘柄はEXCLUDED_TICKERSで扱うのが正しい＝一時的な作業印と構造的除外は別物。）
_lit = [(lb, tk, bs, ts) for lb, tk, bs, ts in scan
        if bs >= 8 and tk not in ("^VIX", "^TNX") and tk not in EXCLUDED_TICKERS]
_lit.sort(key=lambda x: -x[2])  # 大底スコア降順

with st.expander(f"📋 点灯銘柄の一括出力（大底8以上 {len(_lit)}銘柄・タップで開く）"):
    if not _lit:
        st.caption("大底8以上の点灯はなしなのだ。凪の日は出番なしで正常なのだ。")
    else:
        _opts = [f"{lb.split('（')[0].strip()}（大底{bs}）" for lb, tk, bs, ts in _lit]
        _map = {o: t for o, t in zip(_opts, _lit)}
        # デフォルトは【大底9以上】＝買いラインに達したものだけ。
        # 大底8は定義上まだ未達（8/14〜17の22件中19件が大底8の自動見送りだった）。
        _def = [o for o, (lb, tk, bs, ts) in zip(_opts, _lit) if bs >= 9]

        if "bulk_sel" not in st.session_state:
            st.session_state["bulk_sel"] = _def
        else:
            # ★2026-08-20修正：翌日に点灯銘柄が変わると、session_stateに残った古い選択値が
            #   選択肢に存在せずStreamlitが例外を投げてアプリ全体が落ちる。
            #   「昨日ACMを選んだ→今日ACMは消灯」で発生する。毎朝開く運用なので現実に起きる。
            #   multiselectを描画する前に、有効な選択肢だけへ絞り込んでおく。
            _kept = [o for o in st.session_state["bulk_sel"] if o in _opts]
            st.session_state["bulk_sel"] = _kept if _kept else _def

        def _sel_all():
            st.session_state["bulk_sel"] = _opts

        def _sel_nine():
            st.session_state["bulk_sel"] = _def

        _bc1, _bc2 = st.columns(2)
        with _bc1:
            st.button("全選択（大底8も含む）", use_container_width=True,
                      key="bulk_all", on_click=_sel_all,
                      help="週次ルーチン用。週足スコアの改善追跡やINTR/ZTS型の再点灯候補の発掘に使うのだ")
        with _bc2:
            st.button("大底9以上のみ", use_container_width=True,
                      key="bulk_nine", on_click=_sel_nine,
                      help="買いラインに達したものだけに戻すのだ")

        _sel = st.multiselect("出力する銘柄（デフォルト＝大底9以上）", _opts, key="bulk_sel")

        _mode = st.radio("出力フォーマット",
                         ["短縮版（PER点灯記録ログ用）", "全項目版（判断材料フル）"],
                         index=0, horizontal=True, key="bulk_mode")

        if st.button("📝 テーブルを生成", use_container_width=True, key="bulk_go"):
            st.session_state["bulk_ready"] = True

        if st.session_state.get("bulk_ready"):
            _picked = [_map[o] for o in _sel if o in _map]
            if not _picked:
                st.caption("銘柄が選ばれていないのだ。")
            else:
                _vix_s = f"{_vix_now:.1f}" if _vix_now is not None else "-"
                _rows = []
                with st.spinner(f"{len(_picked)}銘柄を集計中（初回は1銘柄あたり数秒かかるのだ）..."):
                    for lb, tk, bs, ts in _picked:
                        _r = bulk_signal_row(tk)
                        if _r is None:
                            continue
                        _r["label"] = lb.split("（")[0].strip()
                        _rows.append(_r)

                if not _rows:
                    st.warning("データ取得に失敗したのだ。🔄データ更新を押して再試行してほしいのだ。")
                else:
                    # PERとPBRの整形。★赤字と取得失敗を必ず区別する。
                    # 取得失敗を「N/A(赤字)」と記録すると前向き検証のデータが汚れるため、
                    # ログ用の短縮版では【空欄のまま】出す（あとで手で埋められる）。
                    def _pf(r, blank_on_fail=False):
                        if r["per"] is not None:
                            return f"{r['per']:.1f}倍" + ("*" if r["per_est"] else "")
                        if r["pbr"]:
                            return "N/A(赤字)"
                        return "" if blank_on_fail else "⚠️取得失敗"
                    def _bf(r):
                        return f"{r['pbr']:.2f}倍" if r["pbr"] else "-"
                    # 検証4の自動判定（今回の点灯を含めて1回目なら初点灯）
                    def _v4(r):
                        if r["bs"] >= 9 and r["n9"] <= 1:
                            return "◎初点灯"
                        if r["bs"] >= 9:
                            return f"✕消化済({r['n9']}回目)"
                        return "-(大底8)"
                    _tmap = {"up": "up📈", "down": "down📉", "range": "range➡️"}

                    if _mode.startswith("短縮版"):
                        _h = "| 日付 | 銘柄 | シグナル | 週足 | 検証4 | PER | PBR | VIX | 判断 | 結果 |"
                        _s = "|---|---|---|---|---|---|---|---|---|---|"
                        _body = [
                            f"| {r['date']} | {r['label']} | 大底{r['bs']}"
                            f"{'💎フル' if r['bs'] >= 10 else ''} | {_fmt_ws(r['ws'])} | {_v4(r)} | "
                            f"{_pf(r, blank_on_fail=True)} | {_bf(r)} | {_vix_s} |  |  |"
                            for r in _rows
                        ]
                        _note = ("※そのままPER点灯記録ログに貼れるのだ（判断・結果の欄は相談後に埋めるのだ）。"
                                 "PERの*は株価÷EPSの概算なのだ。**PER欄が空欄なのは取得失敗**で、赤字ではないのだ"
                                 "（赤字ならPBRが併記されるのだ）。空欄のまま残すか、必要なら手で埋めるのだ。")
                    else:
                        # 天井シグナルは列から外した（天井で売る銘柄が現状ゼロで判断が変わらないため）。
                        # アプリ画面上の天井バッジ表示は残してある。
                        _h = ("| 銘柄 | 大底 | 週足 | 月足 | ダイバ月/日 | PER | PBR | 深度 | "
                              "MA200乖離 | 年率ボラ | 6ヶ月 | 流動性 | 検証4 | VIX |")
                        _s = "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
                        _body = []
                        for r in _rows:
                            _liq_m = "OK" if r["liq"] else "薄💧"
                            _dev_s = f"{r['dev']:+.1f}%" if r["dev"] is not None else "-"
                            _av_s = f"{r['avol']:.0f}%" if r["avol"] is not None else "-"
                            _r6_s = f"{r['ret6']:+.0f}%" if r["ret6"] is not None else "-"
                            _dv = ("有" if r["div_m"] else "無") + "/" + ("有" if r["div_d"] else "無")
                            _body.append(
                                f"| {r['label']} | {r['bs']}{'💎' if r['bs'] >= 10 else ''} | "
                                f"{_fmt_ws(r['ws'])} | {_tmap.get(r['trend'], '対象外')} | {_dv} | "
                                f"{_pf(r)} | {_bf(r)} | {r['dd']:.1f}% | {_dev_s} | {_av_s} | {_r6_s} | "
                                f"{_liq_m} | {_v4(r)} | {_vix_s} |"
                            )
                        _note = ("※深度は-70〜-50%が最良帯・-50〜-30%が最弱帯。年率ボラ45%以上がVIX30弾の適格ライン。"
                                 "月足は3年レンズでrange+54.2%＞up+50.4%＞down+41.9%＝**downも弱い減点にとどめる**のだ。"
                                 "PERが⚠️取得失敗でも判定（大底9・週足5以上）は一切変わらないのだ。")

                    st.code("\n".join([_h, _s] + _body), language=None)
                    st.caption(_note)

# === モメンタムシグナル一覧（折りたたみ・買い/売りの2枠）===
with st.expander("🚀 モメンタムシグナル一覧（タップで開く｜買い=6ヶ月+50%かつMA200上／売り=MA200割れ）"):
    with st.spinner("モメンタム判定中..."):
        mom_buys, mom_sells = scan_momentum()
    st.markdown("#### 🚀 モメンタム買い点灯中（MA200乖離の小さい順）")
    if mom_buys:
        for label, tk, r6, is_held, dev in mom_buys:
            hm = "【保有】" if is_held else ""
            # ★入口ルール②＝MA200乖離+18%以内（EV+23.0%・ペイオフ7.23倍）。
            #   超過は「上昇率が高い＝良い」ではなく【伸びきっていて入口に適さない】の意味なのだ。
            mk = "✅+18%以内" if dev <= 18 else "⚠️+18%超（入口不適）"
            st.markdown(f"- {hm}**{label}**　6ヶ月 **{r6:+.0f}%**　MA200乖離 **{dev:+.1f}%**　{mk}")
        _n_ok = sum(1 for b in mom_buys if b[4] <= 18)
        st.caption(f"✅適格{_n_ok}件／⚠️不適{len(mom_buys)-_n_ok}件。"
                   "1銘柄¥1〜2万（Tier C）・同時保有2銘柄まで・黒字・集中ルール非抵触・決算をまたがない、が入口ルールなのだ。"
                   "🔬対象外（レバETF等）はこの一覧から除外済みなのだ")
    else:
        st.caption("モメンタム買いの点灯はなしなのだ。")
    st.markdown("#### 📉 モメンタム売り点灯中（MA200割れ＝トレンド終了）")
    if mom_sells:
        for label, tk, r6, is_held, dev in mom_sells:
            hm = "【保有】" if is_held else ""
            if is_held:
                st.error(f"{hm}**{label}**　6ヶ月 {r6:+.0f}%　MA200乖離 {dev:+.1f}%　→ モメンタム保有なら売り検討")
            else:
                st.markdown(f"- {label}　6ヶ月 {r6:+.0f}%　MA200乖離 {dev:+.1f}%")
    else:
        st.caption("モメンタム売りの点灯はなしなのだ。")

# === フル点灯の履歴（折りたたみ・直近1年・保有銘柄を強調）===
with st.expander("🏆 フル点灯の履歴（直近1年・大底10/10・天井9/9のみ）"):
    st.caption("多忙・体調不良で見逃した時の回収用。保有銘柄を最上部に強調表示。")
    with st.spinner("履歴を集計中..."):
        full_events = scan_full_history(365)
    if not full_events:
        st.info("直近1年でフル点灯（満点）はなかったのだ。")
    else:
        held_events = [e for e in full_events if e[4]]
        other_events = [e for e in full_events if not e[4]]
        # 枠1：保有銘柄（直近1年すべて）
        st.markdown("#### ⭐ 保有銘柄のフル点灯（直近1年）")
        if held_events:
            for dt, label, tk, kind, _ in held_events:
                mark = "💎" if "大底" in kind else "⛔"
                st.markdown(f"- **{dt.strftime('%Y-%m-%d')}**　{mark} **{label}**　{kind}")
        else:
            st.caption("保有銘柄のフル点灯はなかったのだ。")
        # 枠2：それ以外の銘柄（直近10件だけ）
        st.markdown("#### 監視・その他銘柄のフル点灯（直近10件）")
        if other_events:
            for dt, label, tk, kind, _ in other_events[:10]:
                mark = "💎" if "大底" in kind else "⛔"
                st.markdown(f"- {dt.strftime('%Y-%m-%d')}　{mark} {label}　{kind}")
            if len(other_events) > 10:
                st.caption(f"（ほか{len(other_events)-10}件は省略。直近10件のみ表示）")
        else:
            st.caption("該当なしなのだ。")

# === 📋 登録銘柄リストの書き出し（2026-09-12追加・週次ルーチン用）===
# 背景＝株式部屋のメモリーが持つ登録リストは更新を忘れると古くなる（9/5時点で止まり、9/9に手動追加した
# 2695が抜けていたため、9/12の週次で既登録の3件を重複登録しかける事故が起きた）。
# ★このリストはGROUPSから機械的に生成するので【コードが正】であり、写し間違いも更新漏れも起こらない。
# ★運用＝週次ルーチンを始める前にここを開いてコピーし、株式部屋の冒頭に貼る。
#   これで株式部屋は「今アプリに何が入っているか」を推測せずに済む（推測で埋めたのが事故の原因だった）。
with st.expander("📋 登録銘柄リストの書き出し（★週次ルーチンの第1手順なのだ）"):
    st.warning("⚠️ **週次ルーチンは必ずここから始めるのだ。** 下のリストをコピーして株式部屋の冒頭に貼るのだ。"
               "これを飛ばすと株式部屋は「今アプリに何が入っているか」を推測で埋めることになり、"
               "既登録銘柄を重複登録する事故が起きるのだ（2026-09-12に実際に発生した）。"
               "★点灯相談の時は不要なのだ＝アプリが点灯を検知している時点で登録済みは自明だからなのだ")
    _dt_now = datetime.now(JST).strftime("%Y-%m-%d")
    _total_reg = sum(len(v) for v in GROUPS.values())
    _reg_lines = [f"【アプリ登録銘柄・全{_total_reg}（{_dt_now}時点・アプリから自動生成）】"]
    for _gn, _gd in GROUPS.items():
        _tk_txt = "／".join(
            (t[:-2] if t.endswith(".T") else t) + ("(🔬)" if t in EXCLUDED_TICKERS else "")
            for t in _gd.values())
        _reg_lines.append(f"{_gn}＝{_tk_txt}")
    _reg_lines.append("🔬対象外＝" + "／".join(sorted(EXCLUDED_TICKERS))
                      + "（登録済みだが買わないと決めた＝恒久。審査して登録しなかった『落第履歴』とは別物なのだ）")
    st.code("\n".join(_reg_lines), language=None)
    st.caption("右上のコピーアイコンで全文コピーできるのだ。**コードが正**なので、"
               "株式部屋のメモリーと食い違ったらこちらを信じるのだ")

st.divider()

col_g, col_t = st.columns([1,2])
with col_g:
    group_name = st.radio("グループ", list(GROUPS.keys()))
with col_t:
    ticker_name = st.radio("銘柄を選択", list(GROUPS[group_name].keys()))

# === 直接入力＋✖️クリアボタン ===
# 文字が残ると登録銘柄の選択を上書きし続けるため、ワンタップで消せるようにした。
# ★重要：クリアは必ずon_clickコールバックで行う。
# ボタンのifブロック内でst.session_state["custom_ticker"]=""を実行する書き方は動かない
# （text_inputが先に描画済みのためその回のrunでは反映されず、Streamlitがウィジェット生成後の
#   同キー書き換えを拒否して例外を投げる場合もある）。コールバックはrerunの前に走るので、
# ウィジェットはクリア後の値を読んで正しく空になる。
def _clear_custom_ticker():
    st.session_state["custom_ticker"] = ""

col_in, col_x = st.columns([5,1])
with col_in:
    st.text_input("直接入力（米国株:AAPL / 日本株:4桁数字でOK 例:7203）", key="custom_ticker")
with col_x:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.button("✖️", key="clear_custom", help="入力をクリアして登録銘柄の表示に戻す",
              on_click=_clear_custom_ticker)

_c = st.session_state.get("custom_ticker", "").strip()
ticker = (_c + ".T" if _c.isdigit() and len(_c) == 4 else _c.upper()) if _c else GROUPS[group_name][ticker_name]
period = st.radio("データ期間（スコア計算用・5y推奨）", ["2y","5y","10y","max"], index=1, horizontal=True)

if _c:
    st.warning("⚠️ 直接入力銘柄は未検証です。スコアは参考表示のみとし、売買前に検証を依頼してください。（✖️で入力をクリアすると登録銘柄に戻る）")
with st.spinner("データ取得中..."):
    df = load_data(ticker, period)

if df is None:
    st.error("データ不足です。期間を長くするかティッカーを確認してください（最低260営業日必要）。")
    st.stop()

latest = df.iloc[-1]
prev = df.iloc[-2]
change = float(latest["close"]) - float(prev["close"])
change_pct = change / float(prev["close"]) * 100
symbol = "¥" if (".T" in ticker or ticker.startswith("^N")) else "$"

bottom_score, bottom_checks = calc_bottom_score(latest)
top_score, top_checks = calc_top_score(latest)
w_score, _ = calc_weekly_bottom_score(df)

st.markdown(f"### {ticker}")
c1,c2,c3,c4 = st.columns(4)
c1.metric("現在値", f"{symbol}{float(latest['close']):,.2f}", f"{change:+,.2f}（{change_pct:+.2f}%）")
c2.metric("日足RSI / 週足RSI", f"{float(latest['rsi']):.1f} / {float(latest['w_rsi']):.1f}" if pd.notna(latest['w_rsi']) else f"{float(latest['rsi']):.1f} / -")
c3.metric("大底スコア", f"{bottom_score}/10")
c4.metric("天井スコア", f"{top_score}/9")

# === PER・PBR表示 ===
# ★「赤字」と「取得失敗」を必ず区別する（2026-08-18のyfinance障害で両者が同じ表示になり混乱した）。
# 赤字ならPBRは必ず併記されるはずなので、PBRまで空なら赤字ではなく取得失敗と判定できる。
# yfinanceはYahooのウェブ用エンドポイントを読んでおり、非市場データ（PER/PBR等）は暗号化されていて
# 鍵の場所が変わるたびに壊れる。株価・出来高は別経路なのでスコアだけは無傷、という症状になる。
# ★重要：PERは買いラインの判定に一度も入っていない（判定は大底9・週足5以上・月足upで完結）。
# PERが壊れても売買判断は一切変わらない。用途は前向き検証の記録と、PER3桁の足切りのみ。
_per, _pbr, _per_est = get_per_pbr(ticker)
if _per is not None:
    _per_txt = f"{_per:.1f}倍" + ("（株価÷EPS概算）" if _per_est else "")
elif _pbr:
    _per_txt = "N/A（赤字）"
else:
    _per_txt = "⚠️取得失敗（yfinance側の問題・判定に影響なし）"
_pbr_txt = f"{_pbr:.2f}倍" if _pbr else "-"
st.caption(f"📐 PER {_per_txt}　｜　PBR {_pbr_txt}　※現在値のスナップショット（過去PERは取得不可）")

if w_score is not None:
    if w_score >= 5:
        st.caption(f"📅 週足スコア {w_score}/10（日足={bottom_score}）｜7-8=資金厚めの材料・9は満点警戒。日足シグナルの確認バッジ")
    else:
        st.caption(f"💧 週足スコア {w_score}/10（日足={bottom_score}）｜週足<5=浅い底で見送り寄り")
_to, _liq, _tsym = check_liquidity(df, ticker)
if _to is not None:
    _to_disp = f"{_to/1e8:.1f}億" if _tsym == "¥" else f"{_to/1e6:.0f}百万"
    if _liq:
        st.caption(f"💰 20日平均売買代金 {_tsym}{_to_disp}/日｜流動性OK（テクニカルが機能する水準）")
    else:
        st.caption(f"💧 20日平均売買代金 {_tsym}{_to_disp}/日｜薄商い（テクニカルがダマシになりやすい・7325型）")

_p = float(latest["close"])
st.caption(f"🎯 今買うなら｜損切り-15%＝{symbol}{_p*0.85:,.2f}｜+50%＝{symbol}{_p*1.5:,.2f}｜+100%＝{symbol}{_p*2:,.2f}｜+300%＝{symbol}{_p*4:,.2f}｜+500%＝{symbol}{_p*6:,.2f}（※3分割後は平均取得単価が基準）")

# === 企業アクションによる指標汚染の警告（点灯を評価する前に必ず目に入る位置に置く）===
if ticker in CORPORATE_ACTIONS:
    _ca = CORPORATE_ACTIONS[ticker]
    if _ca.startswith("🚨"):
        st.error(f"**企業アクション：{_ca}**")
    elif _ca.startswith("⚠️"):
        st.warning(f"**企業アクション：{_ca}**")
    else:
        st.info(f"企業アクション：{_ca}")

if ticker == "^VIX":
    st.info("ℹ️ VIXは読み替え注意：VIXの天井=恐怖最大=株の買い場 / VIXの底=楽観=株の天井警戒")

if bottom_score >= 10:
    st.error(f"💎🚨 **大底フル点灯（{bottom_score}/10 満点）**")
    _t1 = pd.Timestamp.today()
    _t2 = (_t1 + BDay(15)).strftime("%m/%d")
    _t3 = (_t1 + BDay(30)).strftime("%m/%d")
    st.markdown(f"""**📋 大底ホームラン戦略（全237取引：勝率30% ペイオフ9.2倍 EV+30%）**
- 第1回買い: 本日（資金の1/3）
- 第2回買い: {_t2}頃（+15営業日、1/3）
- 第3回買い: {_t3}頃（+30営業日、1/3）
- 損切: 平均取得単価 **-15%**（固定）
- 利確: **値幅段階利確 +100% / +300% / +500%**（守り銘柄のみTP+50%）
- 保有: **年単位**（長く持つほどEVが上がる＝5年で+49%）。180日で切らないのだ
- ⚠️ 満点10は大底9より-11pt。「深いほど良い」ではないのだ
- ⚠️ ファンダメンタル（財務健全性＝倒産リスク）の確認を忘れずに""")
elif bottom_score == 9:
    st.error(f"🟢 **買いシグナル点灯（大底スコア{bottom_score}/10）**")
    _t1 = pd.Timestamp.today()
    _t2 = (_t1 + BDay(15)).strftime("%m/%d")
    _t3 = (_t1 + BDay(30)).strftime("%m/%d")
    st.markdown(f"""**📋 大底ホームラン戦略（全237取引：勝率30% ペイオフ9.2倍 EV+30%）**
- 第1回買い: 本日（資金の1/3）
- 第2回買い: {_t2}頃（+15営業日、1/3）
- 第3回買い: {_t3}頃（+30営業日、1/3）
- 損切: 平均取得単価 **-15%**（固定）
- 利確: **値幅段階利確 +100% / +300% / +500%**（守り銘柄のみTP+50%）
- 保有: **年単位**（長く持つほどEVが上がる＝5年で+49%）。180日で切らないのだ
- ⚠️ 7回負けて3回大きく勝つ設計なのだ。負けが続くのは仕様通りなのだ
- ⚠️ ファンダメンタル（財務健全性＝倒産リスク）の確認を忘れずに""")
elif bottom_score == 8:
    st.warning(f"⚠️ 買いゾーン接近（大底スコア{bottom_score}/10）：あと1条件で買いシグナル")
elif bottom_score >= 6:
    st.info(f"📊 大底圏（{bottom_score}/10）：監視継続")

# === トレンド方向フィルター（常時表示・閾値撤廃）===
# ★2026-08-19のv2検証で数値を実測し直した（3年レンズ）：up+50.4% / range+54.2% / down+41.9%。
# 旧文言の「up=EV+34.8%・range=EV+16%・down=EV+12%」は出典が古く、rangeとdownを過小評価していた。
# 【結論：月足フィルターは「downを弱く減点する」だけ。upを要求しないし、rangeは満額で買ってよい】
# 実際CPRIは月足rangeで買った銘柄であり、旧文言を素直に読むと見送ってしまう危険があった。
# ※monthly_trend_directionは5y指定で呼ぶ（判定窓は18ヶ月なので結果は同じ・maxだと二重ダウンロードになる）
trend = monthly_trend_direction(ticker, "5y")
if bottom_score >= 8:
    if trend == "up":
        st.success("📈 **月足トレンド：上昇中** → 3年レンズでEV+50.4%。良い地形なのだ（ただしrangeとほぼ同等で、upを買いの条件にはしないのだ）")
    elif trend == "down":
        st.warning("📉 **月足トレンド：下降中** → 3年レンズでEV+41.9%。up/rangeより弱いが**弱い減点にとどめる**のだ。見送りの決定打にはしないのだ")
    elif trend == "range":
        st.info("➡️ **月足トレンド：レンジ** → 3年レンズでEV+54.2%＝**3つの中で最良**。満額で買ってよいのだ")
    else:
        st.caption("ℹ️ この銘柄はトレンド方向フィルター対象外（暗号資産・高ボラ株はトレンドラインが効かないため）")
else:
    _tmap = {"up": "📈 月足トレンド：上昇中（3年EV+50.4%）",
             "down": "📉 月足トレンド：下降中（3年EV+41.9%・弱い減点にとどめる）",
             "range": "➡️ 月足トレンド：レンジ（3年EV+54.2%＝最良・満額可）"}
    st.caption(_tmap.get(trend, "ℹ️ 月足トレンド：対象外（暗号資産・高ボラ株はトレンドラインが効かない）"))

if top_score >= 9:
    st.error(f"⛔🚨 **天井フル点灯（{top_score}/9 満点）**：保有していれば利確・リスク管理を検討")
elif top_score == 8:
    st.error(f"🔴 **売りシグナル点灯（天井スコア{top_score}/9）**：保有していれば利確・リスク管理を検討")
elif top_score == 7:
    st.warning(f"⚠️ 天井警戒（天井スコア{top_score}/9）")

# === (お) ダイバージェンス表示 ===
# 月足=超強気の買い場サイン（勝率79%）、日足=補助（勝率74%）。「もう底・買い場」の意味
_div = divergence_signals(df)
if _div["monthly"]:
    st.success("‼️‼️‼️ **月足ダイバージェンス発生** ‼️‼️‼ → 超強気の買い場サイン（検証勝率79%・最強格）。株価は安値更新だがRSIは底打ち＝もう底が近い。待たずに買い場として検討")
if _div["daily"]:
    st.info("🔎 **日足ダイバージェンス発生** → 「そろそろ底・買い場が近い」の補助サイン（株価は下げているがRSIは下げ渋り）。待つより買い場として意識（取得単価を下げたいなら分割買い）")

# === (え) モメンタムシグナル表示（全銘柄フラット）===
# 買い=6ヶ月+50%上昇かつMA200上、売り=MA200割れ。買う買わないはわさびが都度判断
_mom = momentum_signal(df)
if _mom == "buy":
    # ★入口ルール②のMA200乖離+18%以内をここでも判定する（一覧とポップアップだけでなく個別画面でも）
    _mdev = float(latest["ma200_dev"]) if pd.notna(latest["ma200_dev"]) else None
    if _mdev is not None and _mdev <= 18:
        st.success(f"🚀 **モメンタム買いシグナル** → 6ヶ月+50%以上かつMA200上。"
                   f"MA200乖離 **{_mdev:+.1f}%** ✅+18%以内で入口適格なのだ（EV+23.0%・ペイオフ7.23倍）。"
                   "1銘柄¥1〜2万（Tier C）・同時保有2銘柄まで・黒字・集中ルール非抵触・決算をまたがない")
    elif _mdev is not None:
        st.warning(f"🚀 モメンタム買いシグナルだが **MA200乖離 {_mdev:+.1f}%＝+18%超で入口不適** なのだ。"
                   "伸びきっていて入口に適さないという意味で、押し目を待つ対象なのだ")
    else:
        st.success("🚀 **モメンタム買いシグナル** → 6ヶ月+50%以上かつMA200上（MA200乖離は算出不可）")
elif _mom == "sell":
    st.warning("📉 **モメンタム売りシグナル** → MA200を割れた（順張りトレンド終了）。モメンタムで保有していれば売り検討")

with st.expander("📋 スコア詳細（タップで開閉）", expanded=False):
    col_b, col_t2 = st.columns(2)
    with col_b:
        st.markdown(f"**大底スコア {bottom_score}/10**")
        for label, ok, detail in bottom_checks:
            st.markdown(f"{'✅' if ok else '❌'} {label}　{detail}")
    with col_t2:
        st.markdown(f"**天井スコア {top_score}/9**")
        for label, ok, detail in top_checks:
            st.markdown(f"{'✅' if ok else '❌'} {label}　{detail}")

# === 🔍 RSI検算パネル（2026-08-22追加）===
# 目的＝【アプリの実装が正しいかをアプリ単体で証明できるようにする】。
# 楽天と見比べても楽天側の方式（RSI1=Wilder系/RSI2=Cutler系）と期間（9 or 14）が特定できないため、
# 外部との突き合わせでは切り分けにならない。そこで生の終値から手計算した値を並べて出す。
# 判定：手計算とアプリ表示が一致すれば実装は正しく、楽天との差は「方式差」で説明がついたことになる。
#      一致しなければアプリのバグ。
def _textbook_wilder_rsi(s, period=14):
    """教科書どおりのWilder RSI（最初のperiod本はSMAで種を作り、以降を平滑化）。
    アプリ本体のwilder_rsi()はewm(adjust=False)で最初の1本から平滑化を始める簡略版のため、
    両者を並べて出して差が実務上ゼロに収束していることを確認する。"""
    d = s.diff().dropna()
    if len(d) < period + 1:
        return None
    up = d.clip(lower=0)
    dn = -d.clip(upper=0)
    ag = float(up.iloc[:period].mean())
    al = float(dn.iloc[:period].mean())
    for i in range(period, len(d)):
        ag = (ag * (period - 1) + float(up.iloc[i])) / period
        al = (al * (period - 1) + float(dn.iloc[i])) / period
    if al == 0:
        return 100.0
    return 100 - 100 / (1 + ag / al)

with st.expander("🔍 RSI検算パネル（Wilder実装の自己検証・タップで開く）", expanded=False):
    st.caption("アプリの表示値と、生の終値から手計算した値を突き合わせるのだ。"
               "**一致＝実装は正しい**（楽天との差は方式差で説明がつく）。**不一致＝アプリのバグ**なのだ。")

    # --- 日足 ---
    _tb_d = _textbook_wilder_rsi(df["close"])
    _ew_d = float(wilder_rsi(df["close"]).iloc[-1])
    _dc1, _dc2, _dc3 = st.columns(3)
    _dc1.metric("日足RSI（アプリ表示）", f"{float(latest['rsi']):.2f}")
    _dc2.metric("ewm簡略版（実装と同一）", f"{_ew_d:.2f}")
    _dc3.metric("教科書版Wilder", f"{_tb_d:.2f}" if _tb_d is not None else "-")
    if _tb_d is not None and abs(_tb_d - float(latest["rsi"])) < 0.5:
        st.success(f"✅ 日足は一致なのだ（差 {abs(_tb_d - float(latest['rsi'])):.3f}pt）。実装は正しいのだ")
    elif _tb_d is not None:
        st.error(f"🚨 日足が {abs(_tb_d - float(latest['rsi'])):.2f}pt ズレているのだ。実装を疑うのだ")

    # --- 週足（★2026-08-22に定義を【完成週のみ】へ統一）---
    # 8/21の「週足バー判定をUTC→JST」の変更はバグではなく修正だった。
    # UTC時代は日本時間の土曜朝に開くとUTC上はまだ金曜のため、完成済みの金曜バーを
    # 「進行中」と誤判定して捨てていた＝週足スコアを1週間古いデータで計算していた。
    # 日足と方向が逆に動いたのは、日足がWilder化のみ・週足はWilder化＋参照バーが1本増えるという
    # 二重の変更を受けていたため。
    _wk_raw = df["close"].resample("W-FRI").last().dropna()
    _wk_done = completed_weekly_closes(df["close"])
    _in_prog = len(_wk_done) < len(_wk_raw)
    _wk_all_rsi = float(wilder_rsi(_wk_raw).iloc[-1])
    _wk_done_rsi = float(wilder_rsi(_wk_done).iloc[-1]) if len(_wk_done) > 15 else None
    _wc1, _wc2, _wc3 = st.columns(3)
    _wc1.metric("週足RSI（アプリ表示・統一後）", f"{float(latest['w_rsi']):.2f}" if pd.notna(latest["w_rsi"]) else "-")
    _wc2.metric("完成週のみ（=正）", f"{_wk_done_rsi:.2f}" if _wk_done_rsi is not None else "-")
    _wc3.metric("進行中の週を含む（旧・参考）", f"{_wk_all_rsi:.2f}")
    st.caption(f"最新の週足バー {_wk_raw.index[-1].strftime('%Y-%m-%d')} は "
               f"{'**進行中（除外中）→ 使うのは前週の確定バー**' if _in_prog else '**完成済み（算入中）**'} なのだ。"
               "完成の定義は『その週の最終取引日の引けが済んでいるか』であってカレンダー週ではないのだ")

    # 統一が効いているかの自己検査（画面表示・大底スコアの条件・週足スコアが同じ系列を見ているか）
    if _wk_done_rsi is not None and pd.notna(latest["w_rsi"]):
        _gap = abs(_wk_done_rsi - float(latest["w_rsi"]))
        if _gap < 0.01:
            st.success(f"✅ 週足も一致なのだ（差 {_gap:.4f}pt）。画面表示・大底スコアの『週足RSI≤30』・"
                       "週足スコアの3つが同じ完成週の系列を見ているのだ")
        else:
            st.error(f"🚨 週足が {_gap:.2f}pt ズレているのだ。定義統一が効いていない＝実装ミスの合図なのだ")

    # --- 生データ（手で検算したい時・Claudeに貼りたい時用）---
    _tail = df[["close"]].tail(16).copy()
    _tail["日足RSI"] = df["rsi"].tail(16)
    _lines = ["日付        終値        日足RSI"]
    for _ix, _rw in _tail.iterrows():
        _lines.append(f"{_ix.strftime('%Y-%m-%d')}  {_rw['close']:>10,.2f}  {_rw['日足RSI']:>7.2f}")
    _lines.append("")
    _lines.append("週足バー（直近6本）")
    for _ix, _v in _wk_raw.tail(6).items():
        _lines.append(f"{_ix.strftime('%Y-%m-%d')}  {_v:>10,.2f}")
    st.code("\n".join(_lines), language=None)
    st.caption("この生データをClaudeに貼れば、こちらでも同じ計算をして突き合わせられるのだ。")

# === 過去のシグナル点灯日を計算（クラスタリングで1山1マーカー）===
# ※コピー用サマリーでも点灯履歴を使うため、チャートより手前で計算しておく
# ★2026-08-20修正1：引数にperiodを追加した。_dfは先頭アンダースコアでハッシュ対象外のため、
#   旧実装はキャッシュキーが銘柄名だけになっており、期間を5y→maxに変えても古い結果が返っていた。
#   検証4の判定根拠なので、期間を変えたのに回数が変わらないのは致命的だった。
# ★2026-08-20修正2：数え方を_cluster_signalsに統一（フル点灯だけ個別に残す例外を廃止）。
#   これで一括出力の点灯回数とサマリーの点灯回数が必ず一致する。
#   💎マーカーはクラスタ内の最高スコアで判定するので、フル点灯の視認性は失われない。
@st.cache_data(ttl=3600)
def calc_signal_history(_df, ticker_key, period):
    bottom_days = _cluster_signals(_df, kind="bottom", thr=9)
    top_days = _cluster_signals(_df, kind="top", thr=8)
    return bottom_days, top_days

sig_bottoms, sig_tops = calc_signal_history(df, ticker, period)

# === コピー用サマリー（Claude相談用・画面に出ている情報を全部入り）===
with st.expander("📄 コピー用サマリー（Claude相談用・タップで開く）", expanded=False):
    _vix_now = get_vix_level()
    _ret6 = calc_ret_6m(df)
    _avol = calc_annual_vol(df)

    # ここぞ判定（個別銘柄版・check_strongestと同じロジック）
    _conds = []
    if _vix_now is not None and _vix_now >= 30:
        _conds.append("VIX30")
    if is_high_vol(df):
        _conds.append("高ボラ")
    if bottom_score >= 8 and len(_conds) >= 2:
        _kokozo = f"🔥確定演出（{' + '.join(_conds)}）"
    elif bottom_score >= 8 and len(_conds) == 1:
        _kokozo = f"⭐ここぞ（{_conds[0]}のみ）"
    else:
        _kokozo = f"該当なし（成立条件: {'・'.join(_conds) if _conds else 'なし'}）"

    # 週足スコアの帯
    if w_score is None:
        _wtxt = "算出不可"
    elif w_score < 5:
        _wtxt = f"{w_score}/10 💧足切り"
    elif w_score >= 9:
        _wtxt = f"{w_score}/10 ⚠️満点警戒"
    elif w_score >= 7:
        _wtxt = f"{w_score}/10 🎯最良帯"
    else:
        _wtxt = f"{w_score}/10"

    _trend_txt = {"up": "上昇(up)", "down": "下降(down)", "range": "レンジ(range)"}.get(trend, "対象外(暗号資産・高ボラ)")
    _mom_txt = {"buy": "🚀買い", "sell": "📉売り"}.get(_mom, "なし")
    _mom_txt += f"（6ヶ月 {_ret6:+.1f}%）" if _ret6 is not None else ""

    # 大底9以上の点灯履歴（検証4＝初点灯かの判定材料）
    if sig_bottoms:
        _b_dates = [d.strftime("%Y-%m-%d") for d, p, s in sig_bottoms]
        _hist_txt = f"データ期間({period})内 {len(sig_bottoms)}回 / 最終 {_b_dates[-1]}"
        _hist_txt += f" / 初回 {_b_dates[0]}"
    else:
        _hist_txt = f"データ期間({period})内 0回 ← 初点灯なら◎高信頼(的中率99%)"

    if _to is not None:
        _liq_disp = f"{_tsym}{_to/1e8:.1f}億/日" if _tsym == "¥" else f"{_tsym}{_to/1e6:.0f}百万/日"
        _liq_disp += "（流動性OK）" if _liq else "（薄商い・ダマシ注意）"
    else:
        _liq_disp = "取得不可"

    _summary = f"""【{ticker}】{df.index[-1].strftime('%Y-%m-%d')}
株価: {symbol}{_p:,.2f}（{change:+,.2f} / {change_pct:+.2f}%）
PER: {_per_txt} ｜ PBR: {_pbr_txt}
--- スコア（RSIはWilder方式・2026-08-22統一）---
大底スコア: {bottom_score}/10
天井スコア: {top_score}/9
週足スコア: {_wtxt}
月足トレンド: {_trend_txt}
ダイバージェンス: 月足={'あり(勝率79%)' if _div['monthly'] else 'なし'} / 日足={'あり(勝率74%)' if _div['daily'] else 'なし'}
モメンタム: {_mom_txt}
ここぞ判定: {_kokozo}
VIX: {f'{_vix_now:.1f}' if _vix_now is not None else '取得不可'}
--- 補助指標 ---
MA200乖離: {f"{latest['ma200_dev']:+.1f}%" if pd.notna(latest['ma200_dev']) else '-'}
下落深度(52週高値から): {latest['drawdown_pct']:.1f}%
高値からの経過: {int(latest['days_from_high'])}日
52週安値から: {latest['rally_pct']:+.1f}%{' ← 新安値更新中' if latest['rally_pct'] <= 5 else ''}
年率ボラ: {f'{_avol:.1f}%' if _avol is not None else '-'}{'（VIX30時の適格ライン45%以上）' if _avol is not None and _avol >= 45 else ''}
売買代金(20日平均): {_liq_disp}
大底9以上の点灯履歴: {_hist_txt}
--- ライン ---
SL-15%: {symbol}{_p*0.85:,.2f}
+50%: {symbol}{_p*1.5:,.2f} / +100%: {symbol}{_p*2:,.2f} / +300%: {symbol}{_p*4:,.2f} / +500%: {symbol}{_p*6:,.2f}"""

    st.code(_summary, language=None)
    st.caption("右上のコピーアイコンで全文コピーできるのだ。そのままClaudeに貼れば相談が一発なのだ。")

# === 〽️ スイング点の数値出力（2026-09-18追加・視覚補助の数値版）===
# ★足種はここで独立に選ぶ（下のチャートの時間軸とは連動させない）。
#   チャートは日足で見ながら週足のスイングを確認する、という使い方をするため。
with st.expander("〽️ ギャンスイングの数値（日付 / H・L / 価格）", expanded=False):
    _sw_tf = st.radio("足種", ["日足", "週足", "月足"], index=0, horizontal=True, key="swing_tf")
    _sw_b = completed_bars_for_swing(df, _sw_tf)
    _sw_pts, _sw_pend = calc_gann_swing(_sw_b)
    if not _sw_pts:
        st.caption("確定したスイング点がまだないのだ（3本連続の転換が成立していないのだ）。")
    else:
        _sw_lines = ["| 日付 | H/L | 価格 |", "|---|---|---|"]
        for _d, _p, _k, _pos in _sw_pts[-40:]:
            _sw_lines.append(f"| {_d.strftime('%Y-%m-%d')} | {_k} | {symbol}{_p:,.2f} |")
        if _sw_pend is not None:
            _sw_lines.append(f"| {_sw_pend[0].strftime('%Y-%m-%d')} | （未確定） | {symbol}{_sw_pend[1]:,.2f} |")
        st.code("\n".join(_sw_lines), language=None)
        st.caption(f"{_sw_tf}で確定{len(_sw_pts)}点（直近40点まで表示）。"
                   "**最終行の（未確定）は転換がまだ成立していない脚**で、後から別の位置に動くのだ。"
                   "確定点も「後から振り返れば天底だった」点であって、その時点で分かっていたものではないのだ")

tf = st.radio("チャート時間軸", ["日足","週足","月足"], index=0, horizontal=True)

def make_chart_frame(df, tf):
    if tf == "日足":
        cd = pd.DataFrame({
            "open": df["open"], "high": df["high"],
            "low": df["low"], "close": df["close"],
        })
    else:
        rule = "W-FRI" if tf == "週足" else "ME"
        try:
            o = df["open"].resample(rule).first()
            h = df["high"].resample(rule).max()
            lo = df["low"].resample(rule).min()
            c = df["close"].resample(rule).last()
        except ValueError:
            rule = "W-FRI" if tf == "週足" else "M"
            o = df["open"].resample(rule).first()
            h = df["high"].resample(rule).max()
            lo = df["low"].resample(rule).min()
            c = df["close"].resample(rule).last()
        cd = pd.DataFrame({"open": o, "high": h, "low": lo, "close": c}).dropna(subset=["close"])
    cd["sma25"] = cd["close"].rolling(25).mean()
    cd["sma75"] = cd["close"].rolling(75).mean()
    cd["sma200"] = cd["close"].rolling(200).mean()
    cd["rsi"] = wilder_rsi(cd["close"])  # チャートのRSIもWilder方式に統一（2026-08-22）
    cd["bb_mid"] = cd["close"].rolling(20).mean()
    s = cd["close"].rolling(20).std()
    cd["bb_upper"] = cd["bb_mid"] + 2*s
    cd["bb_lower"] = cd["bb_mid"] - 2*s
    e12 = cd["close"].ewm(span=12).mean()
    e26 = cd["close"].ewm(span=26).mean()
    cd["macd"] = e12 - e26
    cd["macd_signal"] = cd["macd"].ewm(span=9).mean()
    cd["macd_hist"] = cd["macd"] - cd["macd_signal"]
    return cd

cframe = make_chart_frame(df, tf)

# === チャート表示設定（2026-09-18・トグルを1箇所に集約）===
# ★key=を付けるとStreamlitがsession_stateで状態を保持するので、銘柄を切り替えてもチェックが外れない。
# ★トグル操作はre-runを起こすが、load_dataに@st.cache_data(ttl=3600)が付いているので
#   yfinanceへの再取得は発生しない（1時間以内なら再計算のみ＝待ち時間なし）。
with st.expander("▶ チャート表示設定", expanded=False):
    st.checkbox("📈 価格軸を対数にする", value=False, key="cs_log",
        help="価格パネルのみ対数。RSIとMACDは線形のまま（0〜100の有界指標と振動指標なので対数の意味がない）のだ")
    st.checkbox("〽️ ギャンスイングを表示", value=False, key="cs_gann",
        help="終値3本連続で転換を判定し、転換時に区間の高値/安値（ヒゲ）を結ぶジグザグ線。"
             "★視覚補助のみでスコアやアラートには一切影響しないのだ。未確定の脚は点線で描くのだ")
    st.checkbox("📐 トレンドライン（包絡線法）を表示", value=False, key="cs_trend",
        help="スイング高値が全て下に収まる線／スイング安値が全て上に収まる線を、log価格空間で引くのだ。"
             "ギャンスイングがオフでも単体で表示できるのだ")
    st.divider()
    st.checkbox("📍 過去のシグナル点灯位置をチャートに表示", value=True, key="cs_signals",
        help="日足で大底9以上/天井8以上が点灯した日を価格チャート上に▲▼(フル点灯は💎⛔)で表示")
    st.checkbox("➖ 過去高値/安値の水平ラインを表示", value=False, key="cs_hlines",
        help="意識されやすい過去の高値(赤)・安値(水色)に水平線を引く")
    st.checkbox("🏷️ チャート上部の線の説明（凡例）を表示", value=False, key="cs_legend")

show_log = st.session_state.get("cs_log", False)
show_gann = st.session_state.get("cs_gann", False)
show_trend = st.session_state.get("cs_trend", False)
show_signals = st.session_state.get("cs_signals", True)
show_hlines = st.session_state.get("cs_hlines", False)
show_legend = st.session_state.get("cs_legend", False)

period_options = {"6ヶ月":180,"1年":365,"2年":730,"全期間":99999}
disp = st.radio("表示期間", list(period_options.keys()), index=1, horizontal=True)
days = period_options[disp]
chart_df = cframe if days >= 99999 else cframe[cframe.index >= pd.Timestamp.now() - pd.Timedelta(days=days)]
if len(chart_df) < 5:
    chart_df = cframe

fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                    row_heights=[0.55,0.25,0.20], vertical_spacing=0.03)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["bb_upper"],
    line=dict(color="rgba(100,100,255,0.2)",width=1), showlegend=False), row=1, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["bb_lower"],
    fill="tonexty", fillcolor="rgba(100,100,255,0.05)",
    line=dict(color="rgba(100,100,255,0.2)",width=1), showlegend=False), row=1, col=1)
fig.add_trace(go.Candlestick(x=chart_df.index,
    open=chart_df["open"], high=chart_df["high"],
    low=chart_df["low"], close=chart_df["close"],
    name="株価", increasing_line_color="#ef4444", decreasing_line_color="#3a8fff",
    increasing_fillcolor="#ef4444", decreasing_fillcolor="#3a8fff",
    line=dict(width=1)), row=1, col=1)

# === ギャンスイング／トレンドラインの描画（視覚補助のみ）===
# 確定スイング＝実線、未確定脚＝点線＋薄色。表示期間の外の点は描画範囲でクリップする。
if show_gann or show_trend:
    _sw_bars = completed_bars_for_swing(df, tf)
    _gann_pts, _gann_pending = calc_gann_swing(_sw_bars)
    _xmin, _xmax = chart_df.index.min(), chart_df.index.max()

if show_gann and _gann_pts:
    # 表示範囲の左端をまたぐ脚を切らないため、範囲外の直前1点も残して線をつなぐ
    _vis = [(d, p) for d, p, k, pos in _gann_pts if _xmin <= d <= _xmax]
    _before = [(d, p) for d, p, k, pos in _gann_pts if d < _xmin]
    if _before:
        _vis = [_before[-1]] + _vis
    if len(_vis) >= 2:
        fig.add_trace(go.Scatter(x=[d for d, p in _vis], y=[p for d, p in _vis],
            mode="lines+markers", name="ギャンスイング（確定）",
            line=dict(color="#facc15", width=1.6),
            marker=dict(size=5, color="#facc15"),
            hovertext=[f"スイング {p:,.2f}" for d, p in _vis], hoverinfo="text+x"), row=1, col=1)
    if _gann_pending is not None and _vis:
        # ★未確定脚は必ず点線。実線にすると「進行中の脚まで天底を当てている」ように見える
        fig.add_trace(go.Scatter(x=[_vis[-1][0], _gann_pending[0]], y=[_vis[-1][1], _gann_pending[1]],
            mode="lines", name="ギャンスイング（未確定）",
            line=dict(color="rgba(250,204,21,0.45)", width=1.4, dash="dot"),
            hovertext=["未確定の脚（転換していないのだ）"] * 2, hoverinfo="text+x"), row=1, col=1)

if show_trend and _gann_pts and len(_sw_bars) > 0:
    # 包絡線法。バー位置→日付の変換に_sw_barsのindexを使う（休場日を跨いでも線が歪まない）
    _last_pos = len(_sw_bars) - 1
    for _kind, _nm, _col in [("H", "トレンドライン（高値側）", "#f43f5e"),
                             ("L", "トレンドライン（安値側）", "#22d3ee")]:
        _ln = calc_envelope_line(_gann_pts, _kind, _last_pos)
        if _ln is None:
            continue
        _x0, _y0, _x1, _y1 = _ln
        _i0, _i1 = int(max(0, min(_x0, _last_pos))), int(max(0, min(_x1, _last_pos)))
        fig.add_trace(go.Scatter(x=[_sw_bars.index[_i0], _sw_bars.index[_i1]], y=[_y0, _y1],
            mode="lines", name=_nm,
            line=dict(color=_col, width=1.3, dash="dash"),
            hovertext=[_nm] * 2, hoverinfo="text+x"), row=1, col=1)

# === 過去高値/安値の水平ライン（意識される価格帯）===
if show_hlines and len(chart_df) > 20:
    piv_w = 15
    cl = chart_df["close"].values
    highs = []
    lows = []
    for i in range(piv_w, len(cl)-piv_w):
        win = cl[i-piv_w:i+piv_w+1]
        if cl[i] == win.max():
            highs.append(cl[i])
        if cl[i] == win.min():
            lows.append(cl[i])
    def thin(levels, n=4):
        if not levels:
            return []
        levels = sorted(set(round(v,2) for v in levels))
        if len(levels) <= n:
            return levels
        step = len(levels) / n
        return [levels[int(k*step)] for k in range(n)]
    for lv in thin(highs):
        fig.add_hline(y=lv, line_dash="dot", line_color="rgba(244,63,94,0.75)",
                      line_width=1.5, row=1, col=1)
    for lv in thin(lows):
        fig.add_hline(y=lv, line_dash="dot", line_color="rgba(34,211,238,0.75)",
                      line_width=1.5, row=1, col=1)

if show_signals:
    x_min = chart_df.index.min()
    x_max = chart_df.index.max()
    # フル点灯(大底10/天井9)とそれ未満を分離。フルは💎⛔、未満は▲▼
    b_reg = [(d,p,s) for d,p,s in sig_bottoms if x_min <= d <= x_max and s < 10]
    b_full = [(d,p,s) for d,p,s in sig_bottoms if x_min <= d <= x_max and s >= 10]
    t_reg = [(d,p,s) for d,p,s in sig_tops if x_min <= d <= x_max and s < 9]
    t_full = [(d,p,s) for d,p,s in sig_tops if x_min <= d <= x_max and s >= 9]
    if b_reg:
        fig.add_trace(go.Scatter(x=[d for d,p,s in b_reg], y=[p for d,p,s in b_reg],
            mode="markers", name="大底点灯",
            marker=dict(symbol="triangle-up", size=11, color="#22d3ee",
                        line=dict(color="white", width=1)),
            text=[f"大底{s}/10" for d,p,s in b_reg], hoverinfo="text+x"), row=1, col=1)
    if t_reg:
        fig.add_trace(go.Scatter(x=[d for d,p,s in t_reg], y=[p for d,p,s in t_reg],
            mode="markers", name="天井点灯",
            marker=dict(symbol="triangle-down", size=11, color="#f43f5e",
                        line=dict(color="white", width=1)),
            text=[f"天井{s}/9" for d,p,s in t_reg], hoverinfo="text+x"), row=1, col=1)
    if b_full:
        fig.add_trace(go.Scatter(x=[d for d,p,s in b_full], y=[p for d,p,s in b_full],
            mode="text", name="大底フル点灯",
            text=["💎" for _ in b_full], textposition="bottom center",
            textfont=dict(size=20),
            hovertext=[f"大底フル{s}/10" for d,p,s in b_full], hoverinfo="text+x"), row=1, col=1)
    if t_full:
        fig.add_trace(go.Scatter(x=[d for d,p,s in t_full], y=[p for d,p,s in t_full],
            mode="text", name="天井フル点灯",
            text=["⛔" for _ in t_full], textposition="top center",
            textfont=dict(size=20),
            hovertext=[f"天井フル{s}/9" for d,p,s in t_full], hoverinfo="text+x"), row=1, col=1)

fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["sma25"],
    name="MA25", line=dict(color="#f59e0b",width=1,dash="dash")), row=1, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["sma75"],
    name="MA75", line=dict(color="#a78bfa",width=1,dash="dash")), row=1, col=1)
if not chart_df["sma200"].isna().all():
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["sma200"],
        name="MA200", line=dict(color="#f87171",width=1,dash="dot")), row=1, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["rsi"],
    name=f"RSI（{tf}）", line=dict(color="#34d399",width=1.5)), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
colors_hist = ["#4ade80" if v>=0 else "#f87171" for v in chart_df["macd_hist"].fillna(0)]
fig.add_trace(go.Bar(x=chart_df.index, y=chart_df["macd_hist"],
    marker_color=colors_hist, showlegend=False), row=3, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["macd"],
    name="MACD", line=dict(color="#3a8fff",width=1)), row=3, col=1)
fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["macd_signal"],
    name="シグナル", line=dict(color="#f87171",width=1)), row=3, col=1)
fig.update_layout(height=700, paper_bgcolor="#070f18", plot_bgcolor="#0c1a28",
    font=dict(color="#c8d8e8"), legend=dict(orientation="h", y=1.02, font=dict(color="#ffffff")),
    showlegend=show_legend, margin=dict(t=10,b=10),
    xaxis_rangeslider_visible=False)
fig.update_xaxes(gridcolor="#1a2a3a")
fig.update_yaxes(gridcolor="#1a2a3a")
# === 価格軸の対数切り替え（row1のみ）===
# ★RSI(row2)とMACD(row3)は線形のまま。RSIは0〜100の有界指標、MACDはゼロをまたぐ差分なので
#   そもそも対数を取れない（負値でlogが定義されない）。対数にしてよいのは正の価格だけなのだ。
if show_log:
    # plotlyの対数軸は放置すると 1e+2 のような指数表記になるため、tickformatで通常表記に固定する。
    # 桁に応じて小数を出し分ける＝日本株(¥数千)はカンマ区切り、低位株($2台)は小数2桁まで出す。
    _pmax = float(chart_df["high"].max())
    if _pmax >= 100:
        _tickfmt = ",.0f"
    elif _pmax >= 10:
        _tickfmt = ",.1f"
    else:
        _tickfmt = ",.2f"
    fig.update_yaxes(type="log", tickformat=_tickfmt, exponentformat="none", row=1, col=1)
else:
    fig.update_yaxes(type="linear", tickformat=",.2f", row=1, col=1)
fig.update_yaxes(title_text="RSI", row=2, col=1)
fig.update_yaxes(title_text="MACD", row=3, col=1)
st.plotly_chart(fig, use_container_width=True,
    config={"staticPlot": False, "scrollZoom": True, "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"]})

st.caption(f"出典: yfinance | データ最終日: {df.index[-1].strftime('%Y-%m-%d')} | RSI=Wilder方式(2026-08-22統一) | スコアは常に日足データで計算（チャート時間軸とは独立）| 出口: 3分割買い＋SL-15%＋値幅段階利確+100/300/500%・保有は年単位（全237取引 勝率30% EV+30%）")
