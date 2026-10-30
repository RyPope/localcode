from localcode.importer.case_filter import case_key, filter_cases, fits_java_type

INT_SIG = {"method": "f", "ret": "int", "params": [{"type": "int[]", "name": "nums"}, {"type": "int", "name": "k"}]}


def test_fits_java_primitives():
    assert fits_java_type(5, "int")
    assert not fits_java_type(2**31, "int")
    assert fits_java_type(2**31, "long")
    assert not fits_java_type(2**63, "long")
    assert not fits_java_type(1.5, "int")
    assert fits_java_type(1.5, "double") and fits_java_type(2, "double")
    assert fits_java_type("a", "char") and not fits_java_type("ab", "char")
    assert not fits_java_type(True, "int")
    assert fits_java_type(True, "boolean")


def test_fits_java_containers():
    assert fits_java_type([[1, 2]], "int[][]")
    assert not fits_java_type([[1, 2**40]], "int[][]")
    assert fits_java_type([1, 2], "List<Integer>")
    assert not fits_java_type([1, 2**40], "List<Integer>")
    assert fits_java_type([[1]], "List<List<Integer>>")
    assert fits_java_type([1, None, 2], "TreeNode")
    assert fits_java_type(["ab"], "String[]")


def test_unknown_java_type_is_permissive():
    assert fits_java_type({"x": 1}, "Map<String, Integer>")


def test_filter_drops_overflowing_inputs_and_outputs():
    cases = [{"args": [[1], 1], "expected": 1},
             {"args": [[2**40], 1], "expected": 1},
             {"args": [[1], 1], "expected": 2**40}]
    assert filter_cases(cases, "int", INT_SIG, excluded=set()) == [cases[0]]


def test_filter_drops_none_expected_for_value_returns():
    cases = [{"args": [[1], 1], "expected": None}, {"args": [[1], 2], "expected": 3}]
    assert filter_cases(cases, "int", INT_SIG, excluded=set()) == [cases[1]]


def test_filter_keeps_empty_node_results():
    sig = {"method": "f", "ret": "TreeNode", "params": [{"type": "TreeNode", "name": "root"}]}
    cases = [{"args": [[]], "expected": []}]
    assert filter_cases(cases, "TreeNode", sig, excluded=set()) == cases


def test_filter_without_java_signature_only_applies_value_rules():
    cases = [{"args": [[2**40]], "expected": 1}, {"args": [[1]], "expected": None}]
    assert filter_cases(cases, "int", None, excluded=set()) == [cases[0]]


def test_filter_applies_exclusion_list():
    cases = [{"args": [[1], 1], "expected": 1}, {"args": [[2], 1], "expected": 2}]
    assert filter_cases(cases, "int", INT_SIG, excluded={case_key(cases[1]["args"])}) == [cases[0]]


def test_case_key_is_stable_and_short():
    assert case_key([[1, 2], "a"]) == case_key([[1, 2], "a"])
    assert len(case_key([1])) == 16
