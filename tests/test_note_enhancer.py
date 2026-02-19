import pytest
from flask import Flask
from routes.noteEnhancer import EnhanceNotes

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        yield app

def test_enhance_notes_free_user_limit(mocker, app):
    """
    GIVEN a free user who has reached their daily limit
    WHEN EnhanceNotes is called
    THEN check that the "dailyLimit.html" template is rendered
    """
    mocker.patch('routes.noteEnhancer.current_user', mocker.Mock(is_authenticated=True, id='699755eb0ac27fe8296de32f'))
    mocker.patch('routes.noteEnhancer.GetMongoClient', return_value={
        "EduDuck": {
            "users": mocker.Mock(find_one=lambda x: {"daily_usage": {"timesUsed": 3}})
        }
    })
    mocker.patch('routes.noteEnhancer.render_template', return_value="dailyLimit.html")

    data = {
        "isFree": True,
        "notes": "test notes",
        "language": "English",
        "apiMode": "OpenAI",
        "model": "gpt-4.1-nano"
    }
    mocker.patch('routes.noteEnhancer.request', mocker.Mock(get_json=lambda: data))

    response = EnhanceNotes({}, {})
    assert response == "dailyLimit.html"

def test_enhance_notes_increment_usage_for_free_user(mocker, app):
    """
    GIVEN a free user who has not reached their daily limit
    WHEN EnhanceNotes is called
    THEN check that IncrementUsage is called
    """
    mocker.patch('routes.noteEnhancer.current_user', mocker.Mock(is_authenticated=True, id='699755eb0ac27fe8296de32f'))
    mocker.patch('routes.noteEnhancer.GetMongoClient', return_value={
        "EduDuck": {
            "users": mocker.Mock(find_one=lambda x: {"daily_usage": {"timesUsed": 0}})
        }
    })
    increment_usage_mock = mocker.patch('routes.noteEnhancer.IncrementUsage')
    mocker.patch('routes.noteEnhancer.AiReq', return_value="Enhanced notes")
    mocker.patch('routes.noteEnhancer.StoreQuery', return_value="test_query_id")

    data = {
        "isFree": True,
        "notes": "test notes",
        "language": "English",
        "apiMode": "OpenAI",
        "model": "gpt-4.1-nano",
        "apiKey": "test_api_key"
    }
    mocker.patch('routes.noteEnhancer.request', mocker.Mock(get_json=lambda: data))

    prompts = {
        "enhanceNotes": "Enhance the following notes: {NOTES} in {LANGUAGE}."
    }
    EnhanceNotes(prompts, {})
    increment_usage_mock.assert_called_once()
