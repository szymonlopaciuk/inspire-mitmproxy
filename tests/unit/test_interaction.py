# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE-MITMPROXY.
# Copyright (C) 2018 CERN.
#
# INSPIRE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INSPIRE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

from pathlib import Path
from re import compile
from typing import List

from pytest import fixture, mark

from inspire_mitmproxy.http import MITMHeaders, MITMRequest, MITMResponse
from inspire_mitmproxy.interaction import Interaction


TEST_REQUEST = MITMRequest(
    body=None,
    headers=MITMHeaders({'Host': ['test.local']}),
    method='GET',
    url='https://test.local/path',
)


TEST_RESPONSE = MITMResponse(
    body='{"key": "value"}',
    headers=MITMHeaders({'Content-Type': ['application/json; charset=UTF-8']}),
    status_code=200,
)


def _get_headers(good=True):
    if good:
        return MITMHeaders({})

    else:
        return MITMHeaders({'X-Wrong-Header': ["Headers don't matter"]})


def _test_match_request_data_generate_requests(test_data):
    params = []
    ids = []

    for scenario in test_data:
        _request = MITMRequest(
            method=scenario[0],
            body=scenario[1],
            url=scenario[2],
            headers=scenario[3],
        )
        params.append(_request)
        ids.append(repr(_request))

    return {
        'argnames': '_request',
        'argvalues': params,
        'ids': ids,
    }


TEST_MATCH_REQUEST_DATA_NEGATIVE = _test_match_request_data_generate_requests((
    ('POST', 'Wrong body', 'https://test.local/42/details', _get_headers(good=True)),
    ('POST', 'Wrong body', 'https://test.local/42/details', _get_headers(good=False)),
    ('POST', 'Wrong body', 'https://test.local/bad_url/details', _get_headers(good=True)),
    ('POST', 'Wrong body', 'https://test.local/bad_url/details', _get_headers(good=False)),
    ('POST', '', 'https://test.local/42/details', _get_headers(good=True)),
    ('POST', '', 'https://test.local/42/details', _get_headers(good=False)),
    ('POST', '', 'https://test.local/bad_url/details', _get_headers(good=True)),
    ('POST', '', 'https://test.local/bad_url/details', _get_headers(good=False)),
    ('GET', 'Wrong body', 'https://test.local/42/details', _get_headers(good=True)),
    ('GET', 'Wrong body', 'https://test.local/42/details', _get_headers(good=False)),
    ('GET', 'Wrong body', 'https://test.local/bad_url/details', _get_headers(good=True)),
    ('GET', 'Wrong body', 'https://test.local/bad_url/details', _get_headers(good=False)),
    ('GET', '', 'https://test.local/bad_url/details', _get_headers(good=True)),
    ('GET', '', 'https://test.local/bad_url/details', _get_headers(good=False)),
))


TEST_MATCH_REQUEST_DATA_POSITIVE = _test_match_request_data_generate_requests((
    ('GET', '', 'https://test.local/42/details', _get_headers(good=True)),
    ('GET', '', 'https://test.local/42/details', _get_headers(good=False)),
))


TEST_MATCH_REQUEST_DATA: dict = {
    'method': ['POST', 'GET'],
    'url': ['https://test.local/bad_url/details', 'https://test.local/42/details'],
    'body': ['wrong body', ''],
    'headers': [MITMHeaders({'X-Wrong-Header': ['Very Wrong']}), MITMHeaders({})]
}


@fixture(scope='module')
def interaction_all_fields(request):
    return Interaction.from_file(
        Path(request.fspath.join('../fixtures/test_interaction_detailed.yaml'))
    )


@fixture(scope='module')
def interaction_only_required_fields(request):
    return Interaction.from_file(
        Path(request.fspath.join('../fixtures/test_interaction_simple.yaml'))
    )


@fixture(scope='module')
def interaction_regex_but_no_exact(request):
    return Interaction.from_file(
        Path(request.fspath.join('../fixtures/test_interaction_partial_matches.yaml'))
    )


def test_interaction_all_fields(interaction_all_fields: Interaction):
    assert interaction_all_fields.request == TEST_REQUEST
    assert interaction_all_fields.response == TEST_RESPONSE
    assert interaction_all_fields.exact_match_fields == ['method', 'body']
    assert interaction_all_fields.regex_match_fields == {
        'url': compile(r'https://test\.local/\d+/details')
    }


def test_interaction_only_required_fields(interaction_only_required_fields: Interaction):
    assert interaction_only_required_fields.request == TEST_REQUEST
    assert interaction_only_required_fields.response == TEST_RESPONSE
    assert interaction_only_required_fields.exact_match_fields == ['url', 'method', 'body']
    assert interaction_only_required_fields.regex_match_fields == {}


def test_interaction_partial(interaction_regex_but_no_exact: Interaction):
    assert interaction_regex_but_no_exact.request == TEST_REQUEST
    assert interaction_regex_but_no_exact.response == TEST_RESPONSE
    assert interaction_regex_but_no_exact.exact_match_fields == []
    assert interaction_regex_but_no_exact.regex_match_fields == {
        'url': compile(r'https://test\.local/\d+/details')
    }


def test_interaction_to_dict(interaction_all_fields: Interaction):
    expected = {
        'request': {
            'body': '',
            'headers': {
                'Host': ['test.local'],
            },
            'url': 'https://test.local/path',
            'method': 'GET',
        },
        'response': {
            'body': '{"key": "value"}',
            'headers': {
                'Content-Type': ['application/json; charset=UTF-8'],
            },
            'status': {
                'message': 'OK',
                'code': 200,
            },
        },
        'match': {
            'regex': {
                'url': 'https://test\.local/\d+/details',
            },
            'exact': ['method', 'body'],
        },
        'callbacks': [
            {
                'delay': 2,
                'request': {
                    'body': None,
                    'headers': {
                        'Host': ['callback.local']
                    },
                    'url': 'http://callback.local',
                    'method': 'GET',
                },
            },
        ]
    }

    result = interaction_all_fields.to_dict()

    assert expected == result


@mark.parametrize(**TEST_MATCH_REQUEST_DATA_POSITIVE)
def test_interaction_matches_request_positive(
    interaction_all_fields: Interaction,
    _request: MITMRequest
):
    assert interaction_all_fields.matches_request(_request)


@mark.parametrize(**TEST_MATCH_REQUEST_DATA_NEGATIVE)
def test_interaction_matches_request_negative(
    interaction_all_fields: Interaction,
    _request
):
    assert not interaction_all_fields.matches_request(_request)


@mark.parametrize(
    'interaction_dir_files, expected_next_sequence_number',
    [
        (['interaction_1.yaml', 'interaction_0.yaml'], 2),
        (['interaction_0.yaml'], 1),
        ([], 0),
        (['interaction_7.yaml', 'interaction_13.yaml'], 14),
        (['interaction_1.yaml', 'other.yaml', 'interaction_0.yaml', 'another.yaml'], 2),
        (['interaction_3.yaml', 'other.yaml', 'interaction_5.yaml', 'another.yaml'], 6),
        (['interaction_1.yaml', 'interaction_0.yaml', 'interaction_2.zip'], 2),
        (['.DS_Store', 'interaction_0.yaml~', 'something.jpeg', 'something.tar.gz'], 0),
    ],
    ids=(
        'two interactions, continuous sequence from 0 => 2',
        'one interaction, from 0 => 1',
        'empty directory => 0',
        'two interactions, not continuous (7, 13) => 14',
        'two sequential interactions, two named otherwise, continuous sequence from 0 => 2',
        'two sequential interactions, two named otherwise, not continuous (3, 5) => 6',
        'two interactions, other file present (discard), continuous sequence from 0 => 2',
        'directory not empty, but all files irrelevant => 0',
    )
)
def test_interaction_get_next_sequence_number_in_dir(
    tmpdir,
    interaction_dir_files: List[str],
    expected_next_sequence_number: int,
):
    interaction_dir = tmpdir.mkdir('interactions')
    for file_name in interaction_dir_files:
        interaction_dir.join(file_name).ensure()

    interaction_dir_path = Path(interaction_dir.strpath)

    result = Interaction.get_next_sequence_number_in_dir(interaction_dir_path)

    assert expected_next_sequence_number == result


@mark.parametrize(
    'interaction_dir_files, expected_next_interaction_name',
    [
        (['interaction_1.yaml', 'interaction_0.yaml'], 'interaction_2'),
        (['interaction_0.yaml', 'interaction_1.yaml'], 'interaction_2'),
        (['interaction_0.yaml'], 'interaction_1'),
        ([], 'interaction_0'),
    ],
    ids=(
        'two interactions, continuous sequence from 0 => 2',
        'two interactions, continuous sequence from 0, reversed => 2',
        'one interaction, from 0 => 1',
        'empty directory => 0',
    )
)
def test_interaction_next_in_dir(
    tmpdir,
    interaction_dir_files: List[str],
    expected_next_interaction_name: str,
):
    interaction_dir = tmpdir.mkdir('interactions')
    for file_name in interaction_dir_files:
        interaction_dir.join(file_name).ensure()

    interaction_dir_path = Path(interaction_dir.strpath)

    result = Interaction.next_in_dir(
        directory=interaction_dir_path,
        request=MITMRequest(url='http://test.local/', method='GET'),
        response=MITMResponse(status_code=204)
    )

    expected_request = MITMRequest(url='http://test.local/', method='GET')
    expected_response = MITMResponse(status_code=204)

    assert expected_next_interaction_name == result.name
    assert expected_request == result.request
    assert expected_response == result.response
