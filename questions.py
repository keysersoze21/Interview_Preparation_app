'''
    あらかじめ用意しておく想定の質問リスト
    フォーマットは下記の通りです。
    - question: 実際の面接で聞かれそうなカジュアルな質問（例：「昼ごはんはTDSのどこで食べたい？」）
    - correct_genre_labels: 回答のジャンル（例：「ごはん」）
    - correct_assumption_labels: 回答に含まれるべき前提（例：「TDS内」）
    - emphasis: 面接官が評価したい観点（例：「チームワーク力」「論理的思考」など）
'''
QUESTION_DICT = {
    'question0': {
        'question': '---', 
        'correct_genre_labels': '...', 
        'correct_assumption_labels': '...', 
        'emphasis': '...'},
    'question1': {
        'question': '自己PRをお願いします', 
        'correct_genre_labels': '自己紹介', 
        'correct_assumption_labels': '成果', 
        'emphasis': '人柄'},
    'question2':{
        "question": "学生時代に頑張ったことは何ですか？",
        "correct_genre_labels": "経験",
        "correct_assumption_labels": "行動",
        "emphasis": "主体性"
    },
    'question3':{
        "question": "あなたの強みと弱みを教えてください",
        "correct_genre_labels": "特性",
        "correct_assumption_labels": "改善",
        "emphasis": "適応力"
    },
    'question4':{
        "question": "将来どのようなキャリアを築きたいですか？",
        "correct_genre_labels": "展望",
        "correct_assumption_labels": "目標",
        "emphasis": "志向性"
    },
    'question5':{
        "question": "志望動機を教えてください",
        "correct_genre_labels": "理由",
        "correct_assumption_labels": "共感",
        "emphasis": "適合度",
    }
}