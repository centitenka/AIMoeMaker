# tests/test_node_eval.py
"""Test the node evaluation engine's topological sort logic."""
from ui.node_eval import _topological_sort


class MockNode:
    def __init__(self, name):
        self.name = name
        self.bl_label = name
    def __repr__(self):
        return f"MockNode({self.name})"


class MockLink:
    def __init__(self, from_node, to_node):
        self.from_node = from_node
        self.to_node = to_node


def test_linear_chain():
    a = MockNode("A")
    b = MockNode("B")
    c = MockNode("C")
    links = [MockLink(a, b), MockLink(b, c)]
    result = _topological_sort([a, b, c], links)
    assert result.index(a) < result.index(b)
    assert result.index(b) < result.index(c)


def test_no_links():
    a = MockNode("A")
    b = MockNode("B")
    result = _topological_sort([a, b], [])
    assert len(result) == 2
    assert set(result) == {a, b}


def test_diamond_dependency():
    a = MockNode("A")
    b = MockNode("B")
    c = MockNode("C")
    d = MockNode("D")
    links = [MockLink(a, b), MockLink(a, c), MockLink(b, d), MockLink(c, d)]
    result = _topological_sort([a, b, c, d], links)
    assert result.index(a) < result.index(b)
    assert result.index(a) < result.index(c)
    assert result.index(b) < result.index(d)
    assert result.index(c) < result.index(d)


def test_single_node():
    a = MockNode("A")
    result = _topological_sort([a], [])
    assert result == [a]


def test_empty():
    result = _topological_sort([], [])
    assert result == []
