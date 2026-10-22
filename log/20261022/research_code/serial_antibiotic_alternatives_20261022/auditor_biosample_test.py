import json

from auditor_biosample import project, safe_identity


def example(extra="", title="GPN_001", strain="GPN_001"):
    return f'''<BioSampleSet><BioSample id="000123" accession="SAMN000001" submission_date="2025-01-01"><Ids><Id db_label="Sample name" namespace="owner">GPN_001</Id><Id db="SRA">not_exported</Id></Ids><Description><Title>{title}</Title><Comment>MIC 64</Comment><Organism taxonomy_id="562" taxonomy_name="Escherichia coli"><OrganismName>Escherichia coli</OrganismName></Organism></Description><Owner><Name abbreviation="LAB">Laboratory</Name><Contacts><Contact><Name>private contact</Name></Contact></Contacts></Owner><Attributes><Attribute attribute_name="strain" harmonized_name="strain">{strain}</Attribute><Attribute attribute_name="collection_date" harmonized_name="collection_date">2025-01-01</Attribute><Attribute attribute_name="MIC">12345.6789</Attribute><Attribute attribute_name="fitness">98765.4321</Attribute><Attribute attribute_name="variation">mutation secret</Attribute>{extra}</Attributes></BioSample></BioSampleSet>'''.encode()


def test_identity_export_excludes_phenotypes_and_nonwhitelisted_comments_contacts():
    result = project(example())
    text = json.dumps(result)
    assert "12345.6789" not in text and "98765.4321" not in text and "mutation secret" not in text
    assert "private contact" not in text and "not_exported" not in text
    assert result["samples"][0]["strain_isolate_sample_identity"][0]["value"] == "GPN_001"
    assert {a["attribute_name"] for a in result["samples"][0]["attribute_names"]} >= {"MIC", "fitness", "variation"}


def test_identifier_digits_leading_zeros_are_preserved():
    sample = project(example())["samples"][0]
    assert sample["entrez_id"] == "000123" and sample["accession"] == "SAMN000001"
    assert sample["sample_name_ids"][0]["value"] == "GPN_001"


def test_possible_phenotype_in_title_or_strain_is_withheld():
    sample = project(example(title="MIC=64", strain="GEN_resistant_12345.6789"))["samples"][0]
    assert sample["title"]["withheld"] and sample["title"]["value"] is None
    assert sample["strain_isolate_sample_identity"][0]["withheld"]
    assert "12345.6789" not in json.dumps(sample)


def test_taxonomy_owner_and_collection_date_are_metadata():
    sample = project(example())["samples"][0]
    assert sample["taxonomy"]["taxonomy_id"] == "562"
    assert sample["owner"]["name"] == "Laboratory"
    assert sample["collection_dates"] == [{"attribute_name": "collection_date", "value": "2025-01-01"}]


def test_unapproved_attribute_values_do_not_leave_worker():
    sample = project(example(extra='<Attribute attribute_name="host">not-permitted-host-value</Attribute>'))["samples"][0]
    assert "not-permitted-host-value" not in json.dumps(sample)
    assert "host" in json.dumps(sample["attribute_names"])


def test_identifier_guard_keeps_history_names_without_interpreting_them():
    assert safe_identity("NPG-8") == {"value": "NPG-8", "withheld": False, "reason": None}
    assert safe_identity("GP 007")["value"] == "GP 007"
    assert safe_identity("Growth=1234")["withheld"]
    assert safe_identity("NIT 64 µg/mL")["withheld"]
