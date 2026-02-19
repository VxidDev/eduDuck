import pytest
from flask import Flask
from routes.noteAnalyzer import ParseNoteAnalysis, NoteAnalyzer

def test_parse_note_analysis_with_valid_string():
    """
    GIVEN a valid note analysis string
    WHEN ParseNoteAnalysis is called
    THEN check that the analysis is correctly parsed
    """
    analysis_string = """
    OVERALL_SCORE: 85

    SECTION: Clarity
    CONFIDENCE: 90
    ISSUES:
    - Some sentences are a bit long.
    WHY_IT_MATTERS:
    - Long sentences can be hard to follow.
    SUGGESTIONS:
    - Break up long sentences.

    SECTION: Completeness
    CONFIDENCE: 80
    ISSUES:
    - Missing details on topic X.
    WHY_IT_MATTERS:
    - Topic X is important for understanding the subject.
    SUGGESTIONS:
    - Add more details about topic X.
    """
    analysis = ParseNoteAnalysis(analysis_string)
    assert analysis["overall_score"] == 85
    assert len(analysis["sections"]) == 2
    assert analysis["sections"][0]["title"] == "Clarity"
    assert analysis["sections"][0]["confidence"] == 90
    assert analysis["sections"][0]["issues"] == ["Some sentences are a bit long."]
    assert analysis["sections"][0]["why_it_matters"] == ["Long sentences can be hard to follow."]
    assert analysis["sections"][0]["suggestions"] == ["Break up long sentences."]
    assert analysis["sections"][1]["title"] == "Completeness"
    assert analysis["sections"][1]["confidence"] == 80
    assert analysis["sections"][1]["issues"] == ["Missing details on topic X."]
    assert analysis["sections"][1]["why_it_matters"] == ["Topic X is important for understanding the subject."]
    assert analysis["sections"][1]["suggestions"] == ["Add more details about topic X."]

def test_parse_note_analysis_with_empty_string():
    """
    GIVEN an empty note analysis string
    WHEN ParseNoteAnalysis is called
    THEN check that an empty analysis is returned
    """
    analysis = ParseNoteAnalysis("")
    assert analysis == {"overall_score": 0, "sections": []}

def test_parse_note_analysis_with_invalid_string():
    """
    GIVEN an invalid note analysis string
    WHEN ParseNoteAnalysis is called
    THEN check that an empty analysis is returned
    """
    analysis = ParseNoteAnalysis("invalid string")
    assert analysis == {"overall_score": 0, "sections": []}

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        yield app

def test_note_analyzer_increment_usage_for_free_user(mocker, app):
    """
    GIVEN a free user who has not reached their daily limit
    WHEN NoteAnalyzer is called
    THEN check that IncrementUsage is called
    """
    mocker.patch('routes.noteAnalyzer.current_user', mocker.Mock(is_authenticated=True, id='699755eb0ac27fe8296de32f'))
    mocker.patch('routes.noteAnalyzer.GetMongoClient', return_value={
        "EduDuck": {
            "users": mocker.Mock(find_one=lambda x: {"daily_usage": {"timesUsed": 0}})
        }
    })
    increment_usage_mock = mocker.patch('routes.noteAnalyzer.IncrementUsage')
    mocker.patch('routes.noteAnalyzer.AiReq', return_value="OVERALL_SCORE: 85")
    mocker.patch('routes.noteAnalyzer.StoreQuery', return_value="test_query_id")

    data = {
        "isFree": True,
        "notes": "test notes",
        "language": "English",
        "apiMode": "OpenAI",
        "model": "gpt-4.1-nano",
        "apiKey": "test_api_key"
    }
    mocker.patch('routes.noteAnalyzer.request', mocker.Mock(get_json=lambda: data))

    prompts = {
        "noteAnalyzer": "Analyze the following notes: {NOTES} in {LANGUAGE}."
    }
    NoteAnalyzer(prompts, {})
    increment_usage_mock.assert_called_once()
