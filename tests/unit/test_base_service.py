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

"""Test BaseService"""

from os import chdir, environ, getcwd
from pathlib import Path
from typing import Optional

from mock import patch
from pytest import fixture, mark, raises

from inspire_mitmproxy.errors import NoMatchingRecording, ScenarioNotInService
from inspire_mitmproxy.http import MITMHeaders, MITMRequest, MITMResponse
from inspire_mitmproxy.services import BaseService


@fixture(scope='function')
def service():
    class TestService(BaseService):
        SERVICE_HOSTS = ['host_a.local', 'host_b.local']

        def __init__(self):
            super().__init__()
            self.active_scenario = 'test_scenario'

    return TestService()


@fixture
def scenarios_dir(request):
    with patch.dict(environ, {
        'SCENARIOS_PATH': str(request.fspath.join('../fixtures/scenarios'))
    }):
        yield


@fixture(scope='function')
def in_tmpdir(tmpdir):
    initial_cwd = getcwd()
    chdir(tmpdir)
    yield tmpdir
    chdir(initial_cwd)


@fixture
def sample_request(request) -> MITMRequest:
    return MITMRequest(
        body='body content',
        headers=MITMHeaders({
            'Accept': ['text/plain'],
            'Connection': ['keep-alive'],
            'User-Agent': ['python-requests/2.18.4']
        }),
        method='GET',
        url='https://domain.local/path;param?query=value',
    )


@mark.parametrize(
    'request_, handled',
    [
        ({'url': 'http://host_a.local/api', 'headers': {'Host': ['host_a.local']}}, True),
        ({'url': 'http://host_b.local/api', 'headers': {'Host': ['host_b.local']}}, True),
        ({'url': 'http://wrong.local/api', 'headers': {'Host': ['host_a.local']}}, True),
        ({'url': 'http://host_a.local/api', 'headers': {'Host': ['wrong.local']}}, False),
        ({'url': 'http://host_a.local/api', 'headers': {}}, True),
        ({'url': 'http://wrong.local/api', 'headers': {'Host': ['wrong.local']}}, False),
    ],
    ids=[
        'check first, Host and URI matching: should be handled',
        'check second, Host and URI matching: should be handled',
        'Host matching, URI not: should be handled',
        'URI matching, Host not: should not be handled',
        'URI matching, Host undefined: should be handled',
        'URI and Host both not matching: should not be handled',
    ]
)
def test_base_service_handles_request(service: BaseService, request_: dict, handled: bool):
    request_ = MITMRequest(
        url=request_['url'],
        headers=MITMHeaders(request_['headers']),
    )
    assert service.handles_request(request_) == handled


def test_base_service_get_interactions_for_active_scenario(service: BaseService, scenarios_dir):
    expected_request_1 = MITMRequest(
        headers=MITMHeaders({
            'Accept': ['application/json'],
            'Accept-Encoding': ['gzip, deflate'],
            'Connection': ['keep-alive'],
            'User-Agent': ['python-requests/2.18.4']
        }),
        method='GET',
        url='https://host_a.local/api',
    )

    expected_response_1 = MITMResponse(
        body='{"value": "response1"}',
        headers=MITMHeaders({
            'content-type': ['application/json; charset=UTF-8']
        }),
        status_code=200,
    )

    expected_request_2 = MITMRequest(
        body='{"value": "response2"}',
        headers=MITMHeaders({
            'Accept': ['application/json'],
            'Accept-Encoding': ['gzip, deflate'],
            'Connection': ['keep-alive'],
            'User-Agent': ['python-requests/2.18.4']
        }),
        method='POST',
        url='https://host_a.local/api',
    )

    expected_response_2 = MITMResponse(
        headers=MITMHeaders({
            'content-type': ['application/json; charset=UTF-8']
        }),
        status_code=201,
    )

    interactions = service.get_interactions_for_active_scenario()

    assert len(interactions) == 2
    assert interactions[0].request == expected_request_1
    assert interactions[0].response == expected_response_1
    assert interactions[1].request == expected_request_2
    assert interactions[1].response == expected_response_2


@mark.parametrize(
    'request_, response',
    [
        (
            MITMRequest(
                headers=MITMHeaders({
                    'Accept': ['application/json'],
                }),
                method='GET',
                url='https://host_a.local/api',
            ),
            MITMResponse(
                body='{"value": "response1"}',
                headers=MITMHeaders({
                    'content-type': ['application/json; charset=UTF-8'],
                }),
                status_code=200,
            ),
        ),
        (
            MITMRequest(
                body='{"value": "response2"}',
                headers=MITMHeaders({
                    'Accept': ['application/json'],
                }),
                method='POST',
                url='https://host_a.local/api',
            ),
            MITMResponse(
                headers=MITMHeaders({
                    'content-type': ['application/json; charset=UTF-8'],
                }),
                status_code=201,
            ),
        ),
    ],
    ids=[
        'match interaction_0.yaml',
        'match interaction_1.yaml',
    ]
)
def test_process_request(
    service: BaseService,
    request_: MITMRequest,
    response: MITMResponse,
    scenarios_dir
):
    assert service.process_request(request_) == response


def test_process_request_fails_on_unknown_request(service: BaseService, scenarios_dir):
    request = MITMRequest(
        body='{"value": "whatever"}',
        headers=MITMHeaders({
            'Accept': ['application/json'],
        }),
        method='PUT',
        url='https://host_a.local/this/path/is/not/handled',
    )

    with raises(NoMatchingRecording):
        service.process_request(request)


def test_increment_interaction_count_first(service: BaseService):
    expected = 1

    service.increment_interaction_count('test_interaction')
    result = service.interactions_replayed[service.active_scenario]['test_interaction']['num_calls']

    assert expected == result


def test_increment_interaction_count_repeated(service: BaseService):
    service.interactions_replayed[service.active_scenario] = {
        'test_interaction': {'num_calls': 5},
    }

    expected = 6

    service.increment_interaction_count('test_interaction')
    result = service.interactions_replayed[service.active_scenario]['test_interaction']['num_calls']

    assert expected == result


def test_increment_interaction_count_repeated_on_multiple_scenarios(service: BaseService):
    service.interactions_replayed['scenario1'] = {
        'test_interaction': {'num_calls': 1},
    }
    service.interactions_replayed['scenario2'] = {
        'test_interaction': {'num_calls': 10},
    }

    expected_scenario1 = 2
    expected_scenario2 = 10
    service.active_scenario = 'scenario1'
    service.increment_interaction_count('test_interaction')
    result_scenario1 = service.interactions_replayed['scenario1']['test_interaction']['num_calls']
    result_scenario2 = service.interactions_replayed['scenario2']['test_interaction']['num_calls']

    assert expected_scenario1 == result_scenario1
    assert expected_scenario2 == result_scenario2

    expected_scenario1 = 2
    expected_scenario2 = 11
    service.active_scenario = 'scenario2'
    service.increment_interaction_count('test_interaction')
    result_scenario1 = service.interactions_replayed['scenario1']['test_interaction']['num_calls']
    result_scenario2 = service.interactions_replayed['scenario2']['test_interaction']['num_calls']

    assert expected_scenario1 == result_scenario1
    assert expected_scenario2 == result_scenario2


@mark.parametrize(
    'scenario_dir_exists, scenario_dir_envar, expected_generated_path',
    [
        (True, '{tmpdir}/scenarios/', '{tmpdir}/scenarios/test_scenario/TestService/'),
        (False, '{tmpdir}/scenarios/', '{tmpdir}/scenarios/test_scenario/TestService/'),
    ]
)
def test_get_path_for_active_scenario_dir_from_envar_and_create(
    tmpdir,
    service: BaseService,
    scenario_dir_exists: bool,
    scenario_dir_envar: Optional[str],
    expected_generated_path: str,
):
    scenarios_dir = tmpdir.join('scenarios').mkdir()

    if scenario_dir_exists:
        scenarios_dir.join('test_scenario').mkdir()
        scenarios_dir.join('test_scenario').join('TestService').mkdir()
        assert scenarios_dir.join('test_scenario').join('TestService').exists()
    else:
        assert not scenarios_dir.join('test_scenario').join('TestService').exists()

    with patch.dict(environ, {'SCENARIOS_PATH': scenario_dir_envar.format(tmpdir=tmpdir)}):
        result_generated_path = service.get_path_for_active_scenario_dir(create=True)
        expected_generated_path = Path(expected_generated_path.format(tmpdir=tmpdir))

        assert result_generated_path == expected_generated_path

        assert scenarios_dir.join('test_scenario').join('TestService').exists()


def test_get_path_for_active_scenario_dir_from_envar_do_not_create(
    tmpdir,
    service: BaseService,
):
    scenarios_dir = tmpdir.join('scenarios').mkdir()

    assert not scenarios_dir.join('test_scenario').join('TestService').exists()

    with patch.dict(environ, {'SCENARIOS_PATH': '{tmpdir}/scenarios/'.format(tmpdir=tmpdir)}):
        result_generated_path = service.get_path_for_active_scenario_dir(create=False)
        expected_generated_path = Path(
            '{tmpdir}/scenarios/test_scenario/TestService/'.format(tmpdir=tmpdir)
        )

        assert result_generated_path == expected_generated_path

        assert not scenarios_dir.join('test_scenario').join('TestService').exists()


def test_get_path_for_active_scenario_dir_from_default_do_not_create_already_exists(
    in_tmpdir,
    service: BaseService,
):
    scenarios_dir = in_tmpdir.join('scenarios').mkdir()

    assert not scenarios_dir.join('test_scenario').join('TestService').exists()

    result_generated_path = service.get_path_for_active_scenario_dir(create=False)
    expected_generated_path = Path(
        './scenarios/test_scenario/TestService/'.format(tmpdir=in_tmpdir)
    )

    assert result_generated_path == expected_generated_path

    assert not scenarios_dir.join('test_scenario').join('TestService').exists()


def test_get_interactions_in_scenario(service: BaseService, request):
    interaction_dir = request.fspath.join('../fixtures/scenarios/test_scenario/TestService/')

    expected = [
        f'Interaction.from_file({interaction_dir.join("interaction_0.yaml")})',
        f'Interaction.from_file({interaction_dir.join("interaction_1.yaml")})',
    ]

    with patch(
        'inspire_mitmproxy.interaction.Interaction.from_file',
        side_effect=lambda interaction_file: f'Interaction.from_file({interaction_file})',
    ):
        result = service.get_interactions_in_scenario(Path(interaction_dir))

        assert expected == result


def test_get_interactions_for_active_scenario(service: BaseService, scenarios_dir, request):
    interaction_dir = request.fspath.join('../fixtures/scenarios/test_scenario/TestService/')

    expected = [
        f'Interaction.from_file({interaction_dir.join("interaction_0.yaml")})',
        f'Interaction.from_file({interaction_dir.join("interaction_1.yaml")})',
    ]

    with patch(
        'inspire_mitmproxy.interaction.Interaction.from_file',
        side_effect=lambda interaction_file: f'Interaction.from_file({interaction_file})',
    ):
        result = service.get_interactions_for_active_scenario()

        assert expected == result


def test_get_interactions_for_active_scenario_raises(service: BaseService, scenarios_dir):
    service.active_scenario = 'this_scenario_does_not_exist'

    with raises(ScenarioNotInService):
        service.get_interactions_for_active_scenario()


def test_set_scenario_resets_interaction_count(service: BaseService):
    initial_interactions = {
        'scenario_entered': {
            'interaction_0': {
                'num_calls': 3,
            },
            'interaction_1': {
                'num_calls': 1,
            }
        },
        'scenario_irrelevant': {
            'interaction': 42,
        },
    }

    expected = {
        'scenario_entered': {},
        'scenario_irrelevant': {
            'interaction': 42,
        },
    }

    service.interactions_replayed = initial_interactions
    service.set_active_scenario('scenario_entered')
    result = service.interactions_replayed

    assert expected == result
