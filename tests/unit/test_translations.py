from src.shared.translations import format_inventory, format_lead_time, translate


def test_translate_replaces_known_phrases():
    assert translate("In Stock") == "במלאי"
    assert translate("63 Days") == "63 ימים"
    assert translate("End of Life") == "סוף חיי מוצר"


def test_translate_prefers_longest_match_over_substring():
    """מוודא ש-'RoHS Compliant' מתורגם כמכלול ולא 'תואם' חלקי בגלל 'Compliant' הבודד."""
    assert translate("RoHS Compliant") == "תואם RoHS"
    assert translate("Not Compliant") == "לא תואם RoHS"


def test_translate_keeps_unknown_fragments_and_handles_empty():
    assert translate("42 units") == "42 units"
    assert translate("") == "לא ידוע"
    assert translate(None) == "לא ידוע"


def test_format_inventory_prefixes_vendor():
    assert format_inventory("Mouser", "24,755 In Stock") == "Mouser: 24,755 במלאי"


def test_format_lead_time_translates_and_handles_missing():
    assert format_lead_time("63 Days") == "זמן אספקה: 63 ימים"
    assert format_lead_time(None) == "זמן אספקה: לא ידוע"
