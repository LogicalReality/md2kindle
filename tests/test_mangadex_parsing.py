import pytest
from md2kindle.services.mangadex import parser, resolver

def test_extract_uuid_from_url_manga():
    url = "https://mangadex.org/title/a2c3a969-e669-4ef2-b608-f03b0c36b694/berserk"
    link_type, uuid = parser.extract_uuid_from_url(url)
    assert link_type == "title"
    assert uuid == "a2c3a969-e669-4ef2-b608-f03b0c36b694"

def test_extract_uuid_from_url_chapter():
    url = "https://mangadex.org/chapter/50e7f7b3-847e-402a-9e11-e40854d19318"
    link_type, uuid = parser.extract_uuid_from_url(url)
    assert link_type == "chapter"
    assert uuid == "50e7f7b3-847e-402a-9e11-e40854d19318"

def test_parse_manga_data_basic():
    mock_data = {
        "data": {
            "attributes": {
                "title": {"en": "Test Manga"},
                "altTitles": [{"ja-ro": "Testo Manga"}]
            },
            "relationships": [
                {"type": "author", "attributes": {"name": "Author Name"}}
            ]
        }
    }
    options, author = parser.parse_manga_data(mock_data)
    assert author == "Author Name"
    assert any(opt["title"] == "Test Manga" for opt in options)
    assert any(opt["label"] == "Romaji" for opt in options)

def test_parse_chapter_data():
    mock_data = {
        "data": {
            "attributes": {
                "chapter": "1.5",
                "volume": "2",
                "translatedLanguage": "en"
            },
            "relationships": [
                {"type": "manga", "id": "manga-uuid-123"}
            ]
        }
    }
    start, vol, lang, manga_uuid = parser.parse_chapter_data(mock_data)
    assert start == "1.5"
    assert vol == "2"
    assert lang == "en"
    assert manga_uuid == "manga-uuid-123"

def test_build_chapter_lang_map_mixed():
    primary_lang = "es-la"
    primary_aggregate = {
        "1": {
            "chapters": {
                "1": {"chapter": "1"},
                "2": {"chapter": "2"}
            }
        }
    }
    fallback_aggregates = {
        "en": {
            "1": {
                "chapters": {
                    "1": {"chapter": "1"},
                    "2": {"chapter": "2"},
                    "3": {"chapter": "3"}
                }
            }
        }
    }
    lang_priority = ["en"]
    
    chapter_map, is_mixed = resolver.build_chapter_lang_map(
        "1", primary_lang, primary_aggregate, fallback_aggregates, lang_priority
    )
    
    assert chapter_map["1"] == "es-la"
    assert chapter_map["2"] == "es-la"
    assert chapter_map["3"] == "en"
    assert is_mixed is True

def test_parse_aggregate_data_ok():
    mock_res = {
        "result": "ok",
        "volumes": {"1": "data"}
    }
    res = parser.parse_aggregate_data(mock_res)
    assert res == {"1": "data"}
