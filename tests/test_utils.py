import pytest
from routes.utils import GetMongoURI, Log

def test_get_mongo_uri(monkeypatch):
    """
    GIVEN a monkeypatched environment variable for MONGODB_URI
    WHEN GetMongoURI is called
    THEN check that the URI is correctly formatted
    """
    monkeypatch.setenv("MONGODB_URI", "mongodb://user:password@host:port/db")
    uri = GetMongoURI()
    assert uri == "mongodb://user:password@host:port/db"

def test_get_mongo_uri_with_special_chars(monkeypatch):
    """
    GIVEN a monkeypatched environment variable for MONGODB_URI with special characters in the password
    WHEN GetMongoURI is called
    THEN check that the password is correctly quoted
    """
    monkeypatch.setenv("MONGODB_URI", "mongodb://user:p@ssw@rd@host:port/db")
    uri = GetMongoURI()
    assert uri == "mongodb://user:p%40ssw%40rd@host:port/db"

def test_log(capsys):
    """
    GIVEN a status and a message
    WHEN Log is called
    THEN check that the message is printed to stdout with the correct color
    """
    Log("test message", "info")
    captured = capsys.readouterr()
    assert "test message" in captured.out
    assert "info" in captured.out
