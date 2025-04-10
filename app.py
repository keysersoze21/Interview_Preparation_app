import streamlit as st
import google.generativeai as genai
import time
import json
from questions import QUESTION_DICT  # 別ファイルからインポート

# Gemini API設定（APIキーは環境変数やsecretsに保存して使ってください）
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# Geminiモデルの準備
model_genai = genai.GenerativeModel("gemini-1.5-flash")

# 想定の質問リストのkey
QUESTION_LIST = [QUESTION_DICT[key]['question'] for key in QUESTION_DICT]
# 選択された想定の質問リストの情報を取得するためのkey
QUESTION_text_to_data = {data["question"]: data for data in QUESTION_DICT.values()}

def main():
    if "display_text" not in st.session_state:
        question = ""
        select_question = QUESTION_LIST[0]
        response = ""
    if "select_question" not in st.session_state:
        select_question = QUESTION_LIST[0]
    if "show_selectbox" not in st.session_state:
        st.session_state.show_selectbox = False

    st.markdown("<h1 style='text-align: center;'>1次面接フィードバッカー</h1>", 
                unsafe_allow_html=True)

    # --- Step 1: 質問の選択 ---

    # 2つのボタンをそれぞれ真ん中に配置
    _, col1, col2, _ = st.columns(4)

    with col1:
        if st.button("質問を生成する"):
            question_data = generate_question_with_labels()
            st.session_state["question_data"] = question_data
            question = question_data["question"]
            st.session_state.show_selectbox = False
            select_question = QUESTION_LIST[0]
        # 質問データの保持
        if "question_data" not in st.session_state:
            st.session_state["question_data"] = generate_question_with_labels()
        question_data = st.session_state["question_data"] 

    with col2:
        # 想定された質問の表示
        if st.button("定番の質問を選ぶ"):
            st.session_state.show_selectbox = True
    # 「リストから質問を選ぶ」が実行されたときに表示する
    if st.session_state.show_selectbox:
        question = ""
        default_index = QUESTION_LIST.index(select_question)
        selected = st.selectbox("次に面接質問を選んでください", QUESTION_LIST, index=default_index)
        select_question = selected

    # 選択された質問の表示
    if question:
        question_data = st.session_state["question_data"]
    elif select_question != QUESTION_LIST[0]:
        question_data = QUESTION_text_to_data[select_question]
    st.write("**【質問】**", question_data['question'])
    
    # フィードバックのレベルを選択
    select_level = st.radio(label='面接官の難易度を選択してください',
                            options=('厳しいって(泣)', 'ガチで危機感持った方がいい'),
                            index=0,
                            horizontal=True)
    if select_level == '厳しいって(泣)':
        select_level_word = '評価は優しめでお願いします。よほど酷いものでなければ褒めてあげてください。'
    elif select_level == 'ガチで危機感持った方がいい':
        select_level_word = '評価は厳しめでお願いします。厳しさの中にも少し優しさを出してください。'

    # --- Step 2: 回答入力 ---
    answer = st.text_area("この質問に対するあなたの回答を入力してください", height=300)

    # --- Step 3: 回答を分析するボタン ---
    # 回答を分析するボタンを右詰めに配置
    _, col3 = st.columns([3, 1])

    with col3:
        if st.button("回答を分析する"):
            # 【A】Geminiを用いて評価する
            question_feedback = f'''
                    あなたは面接官です。「{question_data["question"]}」という質問に対して「{answer}」と答えられました。
                    就活生に向けてフィードバックを簡潔にお願いします。
                    {select_level_word}
                    また空欄の場合はフィードバックはできないと答えてください。
                    評価の基準は以下の2つです。
                    ・回答のジャンルが質問で要求しているジャンル「{question_data['correct_genre_labels']}」に含まれているか？
                        回答のジャンルが質問で要求しているジャンルに含まれていない例)
                            Q:「昼ごはんは何食べたい？」
                            A:「さくらチョコチップフラペチーノ」
                            昼ごはんはごはんに含まれるが，さくらチョコチップフラペチーノはごはんに含まれない
                        回答のジャンルが質問で要求しているジャンルに含まれている例)
                            Q:「昼ごはんは何食べたい？」
                            A:「チャーハン」
                            昼ごはんはごはんに含まれており，チャーハンはごはんに含まれいる 
                    ・質問の前提「{question_data['correct_assumption_labels']}」と回答の前提が一致しているか？
                            質問の前提と回答の前提が一致していない例)
                            Q:「昼ごはんはTDSのどこで食べたい？」
                            A:「マクドナルド」
                            QはTDSの中で食べる前提で話しているが、Aはその点を考慮していない
                        質問の前提と回答の前提が一致している例)
                            Q:「昼ごはんはTDSのどこで食べたい？」
                            A:「リストランテ ディ カナレット」
                            QはTDSの中で食べる前提で話しており、Aはその点を考慮している
                                '''
            response = model_genai.generate_content(question_feedback)
    
    # 【B】文章の長さチェック
    if response:
        word_count = len(answer)
        st.write("")
        st.write("---")
        st.write(f"回答文字数: **{word_count}** 語")
        if word_count < 150:
            st.info("回答が短めです。もう少し具体例を加えると良いかもしれません。")
        elif word_count > 250:
            st.info("回答が長すぎる可能性があります。要点を簡潔にまとめましょう。")

        st.write("---")
        st.write("**フィードバック**")
        st.write(response.text)

# Gemini APIで質問生成
def generate_question_with_labels():
    prompt = """
            次のフォーマットに従って、就活面接の練習用の質問を1つ作成してください。
            - question: 実際の面接で聞かれそうなカジュアルな質問（例：「昼ごはんはTDSのどこで食べたい？」）
            - correct_genre_labels: 回答のジャンル（例：「ごはん」）
            - correct_assumption_labels: 回答に含まれるべき前提（例：「TDS内」）
            - emphasis: 面接官が評価したい観点（例：「チームワーク力」「論理的思考」など）
            出力形式は次のようにしてください（Pythonの辞書形式）:
            {
            "question": "...",
            "correct_genre_labels": ["..."],
            "correct_assumption_labels": ["..."],
            "emphasis": "..."
            }
            """
    
    response = model_genai.generate_content(prompt)
    lines = response.text.splitlines()
    json_str = "\n".join(lines[1:len(lines)-1]).strip()
    # responseを辞書に変更
    question_data = json.loads(json_str)

    try:
        return question_data
    except Exception as e:
        st.error("質問の自動生成に失敗しました: " + str(e))
        return {
            "question": "昼ごはんはTDSのどこで食べたい？",
            "correct_genre_labels": ["ごはん"],
            "correct_assumption_labels": ["TDS内"],
            "emphasis": "チームワーク力"
        }

if __name__ == '__main__':
    main()
