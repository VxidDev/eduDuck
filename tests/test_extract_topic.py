import pytest
from routes.utils import extract_topic

def test_extract_topic_with_empty_query_data():
    """
    GIVEN empty query data
    WHEN extract_topic is called
    THEN check that the topic is 'General'
    """
    topic = extract_topic(None, "quiz")
    assert topic == "General"

def test_extract_topic_with_topic_in_query_data():
    """
    GIVEN query data with a topic
    WHEN extract_topic is called
    THEN check that the topic is correctly extracted
    """
    query_data = {"topic": "Enhanced Study Notes on test topic"}
    topic = extract_topic(query_data, "notes")
    assert topic == "test topic"

def test_extract_topic_from_quiz_question():
    """
    GIVEN a quiz with a question
    WHEN extract_topic is called
    THEN check that the topic is correctly extracted from the question
    """
    query_data = {"q1": {"question": "What is the capital of France?"}}
    topic = extract_topic(query_data, "quiz")
    assert topic == "Capital France"

def test_extract_topic_from_string():
    """
    GIVEN a string of notes
    WHEN extract_topic is called
    THEN check that the topic is correctly extracted from the first line
    """
    query_data = """# Test Topic
This is a test note."""
    topic = extract_topic(query_data, "notes")
    assert topic == "Test Topic"
