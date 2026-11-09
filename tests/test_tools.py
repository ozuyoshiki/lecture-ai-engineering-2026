"""ツールのテスト（LLMもAPIキーも使わない）。"""

import json

from app import tools


def test_glossary_ids_are_unique_and_related_links_exist():
    terms = tools.load_glossary()
    ids = [t["id"] for t in terms]
    assert len(ids) == len(set(ids))
    for t in terms:
        for r in t["related"]:
            assert r in ids, f"{t['id']} の related に存在しない id: {r}"


def test_search_finds_term_by_name_and_alias():
    for query in ["LoRA", "lora", "Low-Rank Adaptation"]:
        hits = json.loads(tools.search_glossary(query))
        assert hits[0]["term"] == "LoRA", query


def test_search_finds_course_specific_term():
    hits = json.loads(tools.search_glossary("lecNN-start"))
    assert hits[0]["term"] == "lecNN-start タグ"


def test_search_limits_number_of_results():
    hits = json.loads(tools.search_glossary("エージェント"))
    assert 1 <= len(hits) <= tools.MAX_RESULTS


def test_search_reports_not_found():
    assert "見つかりませんでした" in tools.search_glossary("存在しない用語xyz")


def test_lecture_summary():
    assert "エージェント" in tools.get_lecture_summary(3)
    assert "まだありません" in tools.get_lecture_summary(99)


def test_make_quiz_uses_term_from_requested_lecture():
    quiz = json.loads(tools.make_quiz(2))
    terms = [term for term in tools.load_glossary() if term["lecture"] == 2]

    assert any(
        quiz["question"] == f"「{term['term']}」の意味は？"
        and quiz["answer"] == term["definition"]
        for term in terms
    )


def test_make_quiz_reports_when_lecture_has_no_terms():
    assert "用語が用語集にない" in tools.make_quiz(0)


def test_save_learning_log_appends_to_daily_file(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path)

    first_result = tools.save_learning_log("今日の学習内容")
    second_result = tools.save_learning_log("次の学習内容")

    log_files = list(tmp_path.glob("*.md"))
    assert len(log_files) == 1
    contents = log_files[0].read_text(encoding="utf-8")
    assert "今日の学習内容" in contents
    assert "次の学習内容" in contents
    assert first_result == second_result


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"
