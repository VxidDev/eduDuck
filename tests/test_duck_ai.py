import pytest
from flask import Flask
from routes.duckAI import GenerateResponse

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        yield app

def test_generate_response_increment_usage_for_free_user(mocker, app):
    """
    GIVEN a free user who has not reached their daily limit
    WHEN GenerateResponse is called
    THEN check that IncrementUsage is called
    """
    mocker.patch('routes.duckAI.current_user', mocker.Mock(is_authenticated=True, id='699755eb0ac27fe8296de32f'))
    mocker.patch('routes.duckAI.GetMongoClient', return_value={
        "EduDuck": {
            "users": mocker.Mock(find_one=lambda x: {"daily_usage": {"timesUsed": 0}})
        }
    })
    increment_usage_mock = mocker.patch('routes.duckAI.IncrementUsage')
    mocker.patch('routes.duckAI.AiReq', return_value="Test response")

    data = {
        "isFree": True,
        "message": "test message",
        "apiMode": "OpenAI",
        "model": "gpt-4.1-nano",
        "apiKey": "test_api_key"
    }
    mocker.patch('routes.duckAI.request', mocker.Mock(get_json=lambda: data))

    prompts = {
        "generateResponse": "Generate a response to the following message: {MESSAGE}"
    }
    GenerateResponse(prompts)
    increment_usage_mock.assert_called_once()
