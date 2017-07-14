# -*- coding: utf-8    # This file contains Unicode characters.

from textwrap import dedent

import pytest

from parso import parse
from parso.python import tree


class TestsFunctionAndLambdaParsing(object):

    FIXTURES = [
        ('def my_function(x, y, z) -> str:\n    return x + y * z\n', {
            'name': 'my_function',
            'call_sig': 'my_function(x, y, z)',
            'params': ['x', 'y', 'z'],
            'annotation': "str",
        }),
        ('lambda x, y, z: x + y * z\n', {
            'name': '<lambda>',
            'call_sig': '<lambda>(x, y, z)',
            'params': ['x', 'y', 'z'],
        }),
    ]

    @pytest.fixture(params=FIXTURES)
    def node(self, request):
        parsed = parse(dedent(request.param[0]), version='3.5')
        request.keywords['expected'] = request.param[1]
        child = parsed.children[0]
        if child.type == 'simple_stmt':
            child = child.children[0]
        return child

    @pytest.fixture()
    def expected(self, request, node):
        return request.keywords['expected']

    def test_name(self, node, expected):
        if node.type != 'lambdef':
            assert isinstance(node.name, tree.Name)
            assert node.name.value == expected['name']

    def test_params(self, node, expected):
        assert isinstance(node.params, list)
        assert all(isinstance(x, tree.Param) for x in node.params)
        assert [str(x.name.value) for x in node.params] == [x for x in expected['params']]

    def test_is_generator(self, node, expected):
        assert node.is_generator() is expected.get('is_generator', False)

    def test_yields(self, node, expected):
        assert node.is_generator() == expected.get('yields', False)

    def test_annotation(self, node, expected):
        expected_annotation = expected.get('annotation', None)
        if expected_annotation is None:
            assert node.annotation is None
        else:
            assert node.annotation.value == expected_annotation


def test_end_pos_line(each_version):
    # jedi issue #150
    s = "x()\nx( )\nx(  )\nx (  )\n"

    module = parse(s, version=each_version)
    for i, simple_stmt in enumerate(module.children[:-1]):
        expr_stmt = simple_stmt.children[0]
        assert expr_stmt.end_pos == (i + 1, i + 3)


def test_default_param(each_version):
    func = parse('def x(foo=42): pass', version=each_version).children[0]
    param, = func.params
    assert param.default.value == '42'
    assert param.annotation is None
    assert not param.star_count


def test_annotation_param(each_py3_version):
    func = parse('def x(foo: 3): pass', version=each_py3_version).children[0]
    param, = func.params
    assert param.default is None
    assert param.annotation.value == '3'
    assert not param.star_count


def test_annotation_params(each_py3_version):
    func = parse('def x(foo: 3, bar: 4): pass', version=each_py3_version).children[0]
    param1, param2 = func.params

    assert param1.default is None
    assert param1.annotation.value == '3'
    assert not param1.star_count

    assert param2.default is None
    assert param2.annotation.value == '4'
    assert not param2.star_count


def test_default_and_annotation_param(each_py3_version):
    func = parse('def x(foo:3=42): pass', version=each_py3_version).children[0]
    param, = func.params
    assert param.default.value == '42'
    assert param.annotation.value == '3'
    assert not param.star_count
