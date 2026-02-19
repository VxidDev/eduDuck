import pytest
from flask import Flask
from routes.flashcardGenerator import ParseFlashcards, FlashcardGenerator

def test_parse_flashcards_with_valid_string():
    """
    GIVEN a valid flashcard string
    WHEN ParseFlashcards is called
    THEN check that the flashcards are correctly parsed
    """
    flashcard_string = "Question 1|Answer 1~Question 2|Answer 2"
    flashcards = ParseFlashcards(flashcard_string)
    assert flashcards == [
        {"question": "Question 1", "answer": "Answer 1"},
        {"question": "Question 2", "answer": "Answer 2"},
    ]

def test_parse_flashcards_with_empty_string():
    """
    GIVEN an empty flashcard string
    WHEN ParseFlashcards is called
    THEN check that an empty list is returned
    """
    flashcards = ParseFlashcards("")
    assert flashcards == []

def test_parse_flashcards_with_invalid_string():
    """
    GIVEN an invalid flashcard string
    WHEN ParseFlashcards is called
    THEN check that an empty list is returned
    """
    flashcards = ParseFlashcards("invalid string")
    assert flashcards == []

def test_parse_flashcards_with_missing_answer():
    """
    GIVEN a flashcard string with a missing answer
    WHEN ParseFlashcards is called
    THEN check that the flashcard is ignored
    """
    flashcard_string = "Question 1|Answer 1~Question 2"
    flashcards = ParseFlashcards(flashcard_string)
    assert flashcards == [
        {"question": "Question 1", "answer": "Answer 1"},
    ]

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        yield app

def test_flashcard_generator_increment_usage_for_free_user(mocker, app):
    """
    GIVEN a free user who has not reached their daily limit
    WHEN FlashcardGenerator is called
    THEN check that IncrementUsage is called
    """
    mocker.patch('routes.flashcardGenerator.current_user', mocker.Mock(is_authenticated=True, id='699755eb0ac27fe8296de32f'))
    mocker.patch('routes.flashcardGenerator.GetMongoClient', return_value={
        "EduDuck": {
            "users": mocker.Mock(find_one=lambda x: {"daily_usage": {"timesUsed": 0}})
        }
    })
    increment_usage_mock = mocker.patch('routes.flashcardGenerator.IncrementUsage')
    mocker.patch('routes.flashcardGenerator.AiReq', return_value="Question 1|Answer 1")
    mocker.patch('routes.flashcardGenerator.StoreQuery', return_value="test_query_id")

    data = {
        "isFree": True,
        "notes": "test notes",
        "language": "English",
        "apiMode": "OpenAI",
        "model": "gpt-4.1-nano",
        "amount": 5,
        "apiKey": "test_api_key"
    }
    mocker.patch('routes.flashcardGenerator.request', mocker.Mock(get_json=lambda: data))

    prompts = {
        "flashcard": "Create {AMOUNT} flashcards about {NOTES} in {LANGUAGE}."
    }
    FlashcardGenerator(prompts, {})
    increment_usage_mock.assert_called_once()
