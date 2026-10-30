from localcode.tools.validate_cases import cases_to_exclude


def test_excludes_cases_every_trusted_reference_fails():
    outcomes = {"java": [True, False, True, True], "cpp": [True, False, False, True]}
    assert cases_to_exclude(outcomes) == {1}


def test_ignores_references_that_mostly_fail():
    # cpp's reference fails most cases (wrong signature semantics), so only java is trusted
    outcomes = {"java": [True, True, False, True], "cpp": [False, False, False, True]}
    assert cases_to_exclude(outcomes) == {2}


def test_no_trusted_reference_excludes_nothing():
    assert cases_to_exclude({"java": [False, False, True]}) == set()
    assert cases_to_exclude({}) == set()
