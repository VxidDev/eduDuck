import pytest
from flask import Flask
from routes.studyPlanGenerator import StudyPlanGen

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        yield app

def test_study_plan_gen_increment_usage_for_free_user(mocker, app):
    """
    GIVEN a free user who has not reached their daily limit
    WHEN StudyPlanGen is called
    THEN check that IncrementUsage is called
    """
    mocker.patch('routes.studyPlanGenerator.current_user', mocker.Mock(is_authenticated=True, id='699755eb0ac27fe8296de32f'))
    mocker.patch('routes.studyPlanGenerator.GetMongoClient', return_value={
        "EduDuck": {
            "users": mocker.Mock(find_one=lambda x: {"daily_usage": {"timesUsed": 0}})
        }
    })
    increment_usage_mock = mocker.patch('routes.studyPlanGenerator.IncrementUsage')
    mocker.patch('routes.studyPlanGenerator.AiReq', return_value="## Day 1: Introduction to Python")
    mocker.patch('routes.studyPlanGenerator.StoreQuery', return_value="test_query_id")
    mocker.patch('routes.studyPlanGenerator.study_plan_parser.parse_study_plan', return_value=[{"day": 1, "topic": "Introduction to Python"}])

    data = {
        "isFree": True,
        "notes": "test notes",
        "language": "English",
        "apiMode": "OpenAI",
        "model": "gpt-4.1-nano",
        "startDate": "2024-01-01",
        "endDate": "2024-01-31",
        "hoursPerDay": 2,
        "learningStyles": ["Visual", "Auditory"],
        "goal": "Learn the basics of Python",
        "apiKey": "test_api_key"
    }
    mocker.patch('routes.studyPlanGenerator.request', mocker.Mock(get_json=lambda: data))

    prompts = {
        "studyPlan": "Create a study plan for {NOTES} in {LANGUAGE} from {START_DATE} to {END_DATE} with {HOURS_PER_DAY} hours per day, considering the following learning styles: {LEARNING_STYLES}. The goal is: {GOAL}"
    }
    StudyPlanGen(prompts, {})
    increment_usage_mock.assert_called_once()
