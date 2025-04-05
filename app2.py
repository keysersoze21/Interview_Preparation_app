import time
import numpy as np
import streamlit as st
import google.generativeai as genai
import json

# Gemini API設定（APIキーは環境変数やsecretsに保存して使ってください）
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# Geminiモデルの準備
model = genai.GenerativeModel("gemini-1.5-flash")

# ソフトマックス関数
def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

# 正解ラベルとの一致確率を評価
def calculate_match_probability(answer, correct_labels):
    score = sum(answer.count(label) for label in correct_labels)
    scores = np.array([score, len(correct_labels) - score])
    prob = softmax(scores)[0]
    return prob

# クローズドな質問を処理
def check_closed_question(question, answer):
    if "どっち" in question and "と" in question:
        parts = question.split("どっち")[0].split("と")
        if len(parts) >= 2:
            option1 = parts[-2].strip()
            option2 = parts[-1].strip()
            return option1 in answer or option2 in answer
    return True

# 回答を評価
def evaluate_answer(answer, question_data, emphasis_text, idle_time, delete_count):
    errors = []
    if len(answer) > 250:
        errors.append("回答が250文字を超えています")
    if not check_closed_question(question_data["question"], answer):
        errors.append("クローズドな質問の選択肢が回答に含まれていません")
    genre_prob = calculate_match_probability(answer, question_data["correct_genre_labels"])
    assumption_prob = calculate_match_probability(answer, question_data["correct_assumption_labels"])
    if genre_prob < 0.8:
        errors.append("回答のジャンルが要求に一致していません")
    if assumption_prob < 0.8:
        errors.append("回答の前提条件が一致していません")
    if question_data.get("emphasis"):
        if question_data["emphasis"] not in answer and question_data["emphasis"] not in emphasis_text:
            errors.append("重視している事柄が評価されていません")
    return errors, genre_prob, assumption_prob

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
    response = model.generate_content(prompt)
    lines = response.text.splitlines()
    json_str = "\n".join(lines[1:len(lines)-1]).strip()
    # d:responseを辞書に変更
    d = json.loads(json_str)
    try:
        return d
    except Exception as e:
        st.error("質問の自動生成に失敗しました: " + str(e))
        return {
            "question": "昼ごはんはTDSのどこで食べたい？",
            "correct_genre_labels": ["ごはん"],
            "correct_assumption_labels": ["TDS内"],
            "emphasis": "チームワーク力"
        }

st.title("就職活動一次面接コミュニケーション評価ツール")
# --- 自動生成ボタン ---
if st.button("新しい質問を自動生成"):
    question_data = generate_question_with_labels()
    st.session_state["question_data"] = question_data
# 質問データの保持
if "question_data" not in st.session_state:
    st.session_state["question_data"] = generate_question_with_labels()
question_data = st.session_state["question_data"]
st.write("【質問】", question_data["question"])
st.write("【重視点】", question_data["emphasis"])
# 回答入力
st.subheader("回答入力")
answer = st.text_area("回答を入力してください（250文字以内）", height=150)
emphasis_text = st.text_area("重視している事柄についての補足（任意）", height=70)
# ダミー入力
st.markdown("**※本来はJSで計測するが、ここではダミー入力項目として実装しています。**")
idle_time = st.number_input("【入力停止時間】（秒）", value=0.0, step=0.1)
delete_count = st.number_input("【デリートキー使用回数】", value=0, step=1)
# 評価ボタン
if st.button("評価実施"):
    errors, genre_prob, assumption_prob = evaluate_answer(answer, question_data, emphasis_text, idle_time, delete_count)
    st.subheader("評価結果")
    if errors:
        st.error("不正解：" + "、".join(errors))
    else:
        st.success("正解です！")
    st.write("【問題】", question_data["question"])
    st.write("【回答ラベル】（推定）")
    st.write("　- ジャンル一致確率：", np.round(genre_prob, 2))
    st.write("　- 前提条件一致確率：", np.round(assumption_prob, 2))
    st.write("【正解ラベル】 ジャンル：", question_data["correct_genre_labels"], "　前提条件：", question_data["correct_assumption_labels"])
    st.write("【入力停止時間】", idle_time, "秒")
    st.write("【デリートキー使用回数】", delete_count)
# 掘り下げ質問
if answer:
    st.subheader("追加質問（掘り下げ）")
    follow_up = st.text_input("回答内容について、さらに詳しく教えてください（例：チームワーク力をどのように活かしたかなど）")
    if follow_up:
        st.write("あなたの追加質問：", follow_up)