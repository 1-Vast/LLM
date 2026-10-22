import json

from auditor_title_descriptions import project


def test_source_prose_preserves_timing_identity_and_masks_quantitative_response():
    result = project('<p>Images captured at 3 hours. Response 12345.6789. See https://example.org/data.</p>')
    assert result["literal_time_mentions_in_source_description"] == ["3 hours"]
    assert "12345.6789" not in json.dumps(result)
    assert result["source_description_citation_URLs"] == ["https://example.org/data"]


def test_time_lapse_word_detection_is_not_schedule_certification():
    result = project("Time-lapse images are available.")
    assert result["time_lapse_literal_mentioned"]
    assert result["literal_time_mentions_in_source_description"] == []
    assert result["time_mentions_are_not_independently_verified_acquisition_schedule"]
