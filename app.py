import streamlit as st
from sentence_transformers import SentenceTransformer, util
import google.generativeai as genai
import json

# 文章の類似度判定用にSentence-BERTモデルをロード
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Gemini API設定（APIキーは環境変数やsecretsに保存して使ってください）
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# Geminiモデルの準備
model_genai = genai.GenerativeModel("gemini-1.5-flash")

# あらかじめ用意しておく想定の質問リスト
QUESTION_DICT = {
    'question1': {
        'question': '自己PRをお願いします', 
        'correct_genre_labels': '...', 
        'correct_assumption_labels': '...', 
        'emphasis': '...'},
    'question2':{
        "question": "学生時代に頑張ったことは何ですか？",
        "correct_genre_labels": "...",
        "correct_assumption_labels": "...",
        "emphasis": "..."
    },
    'question3':{
        "question": "あなたの強みと弱みを教えてください",
        "correct_genre_labels": "...",
        "correct_assumption_labels": "...",
        "emphasis": "..."
    },
    'question4':{
        "question": "将来どのようなキャリアを築きたいですか？",
        "correct_genre_labels": "...",
        "correct_assumption_labels": "...",
        "emphasis": "..."
    },
    'question5':{
        "question": "志望動機を教えてください",
        "correct_genre_labels": "...",
        "correct_assumption_labels": "...",
        "emphasis": "...",
    }
}

def main():
    st.title("面接コミュニケーション養成アプリ")

    # --- Step 1: 質問の選択 ---
    if st.button("質問を生成する"):
        question_data = generate_question_with_labels()
        st.session_state["question_data"] = question_data
    # 質問データの保持
    if "question_data" not in st.session_state:
        st.session_state["question_data"] = generate_question_with_labels()
    question_data = st.session_state["question_data"]
    question = question_data["question"]
    st.write("【質問】", question_data["question"])
    #st.write("【重視点】", question_data["emphasis"])    

    if st.button("リストから質問を選ぶ"):
        question = st.selectbox("面接質問を選んでください", QUESTION_DICT.values())

    # --- Step 2: 回答入力 ---
    answer = st.text_area("この質問に対するあなたの回答を入力してください")

    # --- Step 3: 回答を分析するボタン ---
    if st.button("回答を分析する"):
        # 【A】Sentence-BERTを使った簡易的な類似度分析
        q_embedding = model.encode(question_data["question"], convert_to_tensor=True)
        a_embedding = model.encode(answer, convert_to_tensor=True)
        similarity = util.cos_sim(q_embedding, a_embedding)[0][0].item()

        st.write(f"**質問との類似度スコア (Sentence-BERT)**: {similarity:.2f}")

        # 類似度に基づく超簡易フィードバック
        if similarity > 0.5:
            st.success("質問にある程度沿った回答ができています！")
        else:
            st.warning("回答が質問からズレている可能性があります。")

        # 文章の長さチェック
        word_count = len(answer)
        st.write(f"回答文字数: {word_count} 語")
        if word_count < 250:
            st.info("回答が短めです。もう少し具体例を加えると良いかもしれません。")
        elif word_count > 350:
            st.info("回答が長すぎる可能性があります。要点を簡潔にまとめましょう。")

        st.write("---")

        # Gemini
        question_feedback = f'''
                            あなたは面接官です。「{question}」という質問に対して「{answer}」と答えられました。これに関してフィードバックを簡潔にお願いします。
                            評価の基準は以下の5つです。
                            ・質問のジャンル「{question_data['correct_genre_labels']}」に即しているか？
                            ・回答に含まれるべき前提「{question_data['correct_assumption_labels']}」を満たしているか？
                            ・面接官が評価したい観点「{question_data['emphasis']}」について十分に言及されているか？
                            ・文章構成が結論、理由になっているか？
                            ・誤字脱字がないきちんとした文章であるか？
                            '''
        response = model_genai.generate_content(question_feedback)
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

if __name__ == '__main__':
    main()
