import pytest
from flask import Flask
from routes.quiz import QuizGen

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        yield app

def test_quiz_gen_free_user_limit(mocker, app):
    """
    GIVEN a free user who has reached their daily limit
    WHEN QuizGen is called
    THEN check that the "dailyLimit.html" template is rendered
    """
    mocker.patch('routes.quiz.current_user', mocker.Mock(is_authenticated=True))
    mocker.patch('routes.quiz.GetUsage', return_value=mocker.Mock(get_json=lambda: {"timesUsed": 3}))
    mocker.patch('routes.quiz.render_template', return_value="dailyLimit.html")

    data = {
        "isFree": True,
        "notes": "test notes",
        "language": "English",
        "questionCount": 5,
        "apiMode": "OpenAI",
        "difficulty": "Easy",
        "model": "gpt-4.1-nano"
    }
    mocker.patch('routes.quiz.request', mocker.Mock(get_json=lambda: data))

    response = QuizGen({}, {})
    assert response == "dailyLimit.html"

def test_quiz_gen_calls_parse_quiz(mocker, app):
    """
    GIVEN a successful AI response
    WHEN QuizGen is called
    THEN check that parse_quiz is called with the correct argument
    """
    mocker.patch('routes.quiz.current_user', mocker.Mock(is_authenticated=False))
    ai_req_mock = mocker.patch('routes.quiz.AiReq', return_value="1. Question? a) ans b) ans |CORRECT:a")
    parse_quiz_mock = mocker.patch('routes.quiz.parse_quiz', return_value={'1': {'question': 'Question?', 'options': ['ans', 'ans'], 'answer': 'a'}})
    mocker.patch('routes.quiz.StoreTempQuery', return_value="test_query_id")

    data = {
        "isFree": False,
        "notes": "test notes",
        "language": "English",
        "questionCount": 5,
        "apiMode": "OpenAI",
        "difficulty": "Easy",
        "model": "gpt-4.1-nano",
        "apiKey": "test_api_key"
    }
    mocker.patch('routes.quiz.request', mocker.Mock(get_json=lambda: data))

    prompts = {
        "quiz": "Create a quiz with {AMOUNT} questions about {NOTES} in {LANGUAGE} at a {DIFFICULTY} difficulty."
    }
    QuizGen(prompts, {})
    ai_req_mock.assert_called_once()
    parse_quiz_mock.assert_called_once_with("1. Question? a) ans b) ans |CORRECT:a")
