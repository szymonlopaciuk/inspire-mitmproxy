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

"""Tests for the WhitelistService"""

from distutils.dir_util import copy_tree
from json import loads as json_loads
from os import environ
from time import sleep

from mock import patch
from pytest import fixture, raises
from yaml import load as yaml_load

from inspire_mitmproxy.dispatcher import Dispatcher
from inspire_mitmproxy.errors import DoNotIntercept, ScenarioNotInService, ServiceNotFound
from inspire_mitmproxy.http import MITMHeaders, MITMRequest, MITMResponse
from inspire_mitmproxy.services import BaseService


@fixture
def service_a():
    class TestServiceA(BaseService):
        SERVICE_HOSTS = ['host_a.local']
        active_scenario = None

    return TestServiceA


@fixture
def service_b():
    class TestServiceB(BaseService):
        SERVICE_HOSTS = ['host_b.local']
        active_scenario = None

    return TestServiceB


@fixture(scope='function')
def dispatcher(scenarios_dir, service_a, service_b) -> Dispatcher:
    with patch.object(Dispatcher, 'SERVICE_LIST', [service_a, service_b]):
        return Dispatcher()


@fixture
def scenarios_dir(request):
    with patch.dict(environ, {
        'SCENARIOS_PATH': str(request.fspath.join('../fixtures/scenarios'))
    }):
        yield


@fixture(scope='function')
def temporary_scenarios_dir(request, tmpdir):
    fixtures_dir = request.fspath.join('../fixtures/scenarios')
    tmp_scenarios = tmpdir.join('scenarios')
    copy_tree(str(fixtures_dir), str(tmp_scenarios.strpath))

    with patch.dict(environ, {
        'SCENARIOS_PATH': str(tmp_scenarios.strpath)
    }):
        yield tmp_scenarios


def test_base_service_process_request_test_scenario_replays_ok(dispatcher):
    request_set_config = MITMRequest(
        method='POST',
        url='http://mitm-manager.local/config',
        body='{"active_scenario": "test_scenario_replays_ok"}',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    request_service_1 = MITMRequest(
        method='GET',
        url='https://host_a.local/api',
        headers=MITMHeaders({
            'Host': ['host_a.local'],
            'Accept': ['application/json'],
        })
    )

    request_service_2 = MITMRequest(
        method='GET',
        url='https://host_b.local/api',
        headers=MITMHeaders({
            'Host': ['host_b.local'],
            'Accept': ['application/json'],
        })
    )

    response_set_config = dispatcher.process_request(request_set_config)
    assert response_set_config.status_code == 201

    with patch('requests.request') as request:
        response_service_1 = dispatcher.process_request(request_service_1)
        assert response_service_1.body == b'test_scenario_replays_ok/TestServiceA/0'

        sleep(1)  # Wait for the callback
        request.assert_called_once()

    response_service_2 = dispatcher.process_request(request_service_2)
    assert response_service_2.body == b'test_scenario_replays_ok/TestServiceB/0'


def test_base_service_process_request_scenario_raise_if_no_interaction(dispatcher):
    request_set_config = MITMRequest(
        method='POST',
        url='http://mitm-manager.local/config',
        body='{"active_scenario": "test_scenario_raise_if_no_interaction"}',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    request_service_1 = MITMRequest(
        method='GET',
        body='correct body content',
        url='https://host_a.local/api',
        headers=MITMHeaders({
            'Host': ['host_a.local'],
            'Accept': ['application/json'],
        })
    )

    request_service_2 = MITMRequest(
        method='GET',
        url='http://host_b.local/api',
        headers=MITMHeaders({
            'Host': ['host_b.local'],
            'Accept': ['application/json'],
        })
    )

    response_set_config = dispatcher.process_request(request_set_config)
    assert response_set_config.status_code == 201

    response_service_1 = dispatcher.process_request(request_service_1)
    assert response_service_1.body == b'test_scenario_raise_if_no_interaction/TestServiceA/0'

    with raises(ScenarioNotInService):
        dispatcher.process_request(request_service_2)


def test_get_service_interactions(dispatcher: Dispatcher):
    request_set_config = MITMRequest(
        method='POST',
        url='http://mitm-manager.local/config',
        body='{"active_scenario": "test_scenario_replays_ok"}',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    request_service_a = MITMRequest(
        method='GET',
        url='https://host_a.local/api',
        headers=MITMHeaders({
            'Host': ['host_a.local'],
            'Accept': ['application/json'],
        })
    )

    request_service_b = MITMRequest(
        method='GET',
        url='https://host_b.local/api',
        headers=MITMHeaders({
            'Host': ['host_b.local'],
            'Accept': ['application/json'],
        })
    )

    request_service_a_interactions = MITMRequest(
        method='GET',
        url='http://mitm-manager.local/service/TestServiceA/interactions',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    request_service_b_interactions = MITMRequest(
        method='GET',
        url='http://mitm-manager.local/service/TestServiceB/interactions',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    response_set_config = dispatcher.process_request(request_set_config)
    assert response_set_config.status_code == 201

    with patch('requests.request') as request:
        response_service_a_1 = dispatcher.process_request(request_service_a)
        assert response_service_a_1.status_code == 200

        response_service_a_2 = dispatcher.process_request(request_service_a)
        assert response_service_a_2.status_code == 200

        sleep(1)  # Wait for the callback
        assert request.call_count == 2

    response_service_b = dispatcher.process_request(request_service_b)
    assert response_service_b.status_code == 200

    response_service_a_interactions = dispatcher.process_request(request_service_a_interactions)
    response_service_b_interactions = dispatcher.process_request(request_service_b_interactions)

    assert json_loads(response_service_a_interactions.body) == {
        'interaction_0': {'num_calls': 2}
    }
    assert json_loads(response_service_b_interactions.body) == {
        'interaction_0': {'num_calls': 1}
    }


def test_get_service_interactions_raises(dispatcher: Dispatcher):
    request_set_config = MITMRequest(
        method='POST',
        url='http://mitm-manager.local/config',
        body='{"active_scenario": "test_scenario_replays_ok"}',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    request_inexistent_service_interactions = MITMRequest(
        method='GET',
        url='http://mitm-manager.local/service/InexistentService/interactions',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    response_set_config = dispatcher.process_request(request_set_config)
    assert response_set_config.status_code == 201

    with raises(ServiceNotFound):
        dispatcher.process_request(request_inexistent_service_interactions)


def test_base_service_process_response_record_create_interaction_dir_if_does_not_exist(
    dispatcher: Dispatcher,
    temporary_scenarios_dir,
):
    assert not temporary_scenarios_dir.join('test_scenario_record_creates_dir').exists()

    expected_recording = {
        'request': {
            'body': '',
            'headers': {
                'Accept': ['text/plain'],
                'Host': ['host_a.local']
            },
            'method': 'GET',
            'url': 'https://host_a.local/recordme'
        },
        'response': {
            'body': 'Hello, world!',
            'headers': {},
            'status': {
                'code': 200,
                'message': 'OK'
            }
        },
        'match': {},
        'callbacks': [],
    }

    request_set_scenario = MITMRequest(
        method='POST',
        url='http://mitm-manager.local/config',
        body='{"active_scenario": "test_scenario_record_creates_dir"}',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    request_enable_recording = MITMRequest(
        method='POST',
        url='http://mitm-manager.local/record',
        body='{"enable": true}',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    request_to_be_recorded = MITMRequest(
        method='GET',
        url='https://host_a.local/recordme',
        headers=MITMHeaders({
            'Host': ['host_a.local'],
            'Accept': ['text/plain'],
        })
    )

    response_to_be_recorded = MITMResponse(
        status_code=200,
        body='Hello, world!'
    )

    response_set_scenario = dispatcher.process_request(request_set_scenario)
    assert response_set_scenario.status_code == 201

    response_enable_recording = dispatcher.process_request(request_enable_recording)
    assert response_enable_recording.status_code == 201

    with raises(DoNotIntercept):
        dispatcher.process_request(request_to_be_recorded)

    dispatcher.process_response(request_to_be_recorded, response_to_be_recorded)

    service_interactions_dir = temporary_scenarios_dir.join('test_scenario_record_creates_dir')
    assert service_interactions_dir.exists()
    assert len(service_interactions_dir.listdir()) == 1
    assert len(service_interactions_dir.join('TestServiceA').listdir()) == 1

    out_file = service_interactions_dir.join('TestServiceA').join('interaction_0.yaml').read()
    result_recording = yaml_load(out_file)
    assert expected_recording == result_recording


def test_base_service_process_response_record_when_empty_interactions_dir_exists_already(
    dispatcher: Dispatcher,
    temporary_scenarios_dir,
):
    temporary_scenarios_dir.join('test_scenario_record_dir_exists').mkdir()
    assert temporary_scenarios_dir.join('test_scenario_record_dir_exists').exists()

    expected_recording = {
        'request': {
            'body': '',
            'headers': {
                'Accept': ['text/plain'],
                'Host': ['host_a.local']
            },
            'method': 'GET',
            'url': 'https://host_a.local/recordme'
        },
        'response': {
            'body': 'Hello, world!',
            'headers': {},
            'status': {
                'code': 200,
                'message': 'OK'
            }
        },
        'match': {},
        'callbacks': [],
    }

    request_set_scenario = MITMRequest(
        method='POST',
        url='http://mitm-manager.local/config',
        body='{"active_scenario": "test_scenario_record_dir_exists"}',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    request_enable_recording = MITMRequest(
        method='POST',
        url='http://mitm-manager.local/record',
        body='{"enable": true}',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    request_to_be_recorded = MITMRequest(
        method='GET',
        url='https://host_a.local/recordme',
        headers=MITMHeaders({
            'Host': ['host_a.local'],
            'Accept': ['text/plain'],
        })
    )

    response_to_be_recorded = MITMResponse(
        status_code=200,
        body='Hello, world!'
    )

    response_set_scenario = dispatcher.process_request(request_set_scenario)
    assert response_set_scenario.status_code == 201

    response_enable_recording = dispatcher.process_request(request_enable_recording)
    assert response_enable_recording.status_code == 201

    with raises(DoNotIntercept):
        dispatcher.process_request(request_to_be_recorded)

    dispatcher.process_response(request_to_be_recorded, response_to_be_recorded)

    service_interactions_dir = temporary_scenarios_dir.join('test_scenario_record_dir_exists')
    assert service_interactions_dir.exists()
    assert len(service_interactions_dir.listdir()) == 1
    assert len(service_interactions_dir.join('TestServiceA').listdir()) == 1

    out_file = service_interactions_dir.join('TestServiceA').join('interaction_0.yaml').read()
    result_recording = yaml_load(out_file)
    assert expected_recording == result_recording


def test_base_service_process_response_record_when_dir_exists_and_has_some_interactions_already(
    dispatcher: Dispatcher,
    temporary_scenarios_dir,
):
    expected_replayed_response = b'test_scenario_record_not_empty/TestServiceA/0'
    expected_recording = {
        'request': {
            'url': 'https://host_a.local/recordme',
            'method': 'GET',
            'body': '',
            'headers': {
                'Accept': ['text/plain'],
                'Host': ['host_a.local'],
            },
        },
        'response': {
            'body': 'Hello, world!',
            'headers': {},
            'status': {
                'code': 200,
                'message': 'OK',
            },
        },
        'match': {},
        'callbacks': [],
    }

    request_set_scenario = MITMRequest(
        method='POST',
        url='http://mitm-manager.local/config',
        body='{"active_scenario": "test_scenario_record_not_empty"}',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    request_enable_recording = MITMRequest(
        method='POST',
        url='http://mitm-manager.local/record',
        body='{"enable": true}',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    request_to_be_replayed = MITMRequest(
        method='GET',
        url='https://host_a.local/replayme',
        headers=MITMHeaders({
            'Host': ['host_a.local'],
            'Accept': ['text/plain'],
        })
    )

    request_to_be_recorded = MITMRequest(
        method='GET',
        url='https://host_a.local/recordme',
        headers=MITMHeaders({
            'Host': ['host_a.local'],
            'Accept': ['text/plain'],
        })
    )

    response_to_be_recorded = MITMResponse(
        status_code=200,
        body='Hello, world!'
    )

    response_set_scenario = dispatcher.process_request(request_set_scenario)
    assert response_set_scenario.status_code == 201

    response_enable_recording = dispatcher.process_request(request_enable_recording)
    assert response_enable_recording.status_code == 201

    response_to_be_replayed = dispatcher.process_request(request_to_be_replayed)
    assert expected_replayed_response == response_to_be_replayed.body

    with raises(DoNotIntercept):
        dispatcher.process_request(request_to_be_recorded)

    dispatcher.process_response(request_to_be_recorded, response_to_be_recorded)

    service_interactions_dir = temporary_scenarios_dir.join('test_scenario_record_not_empty')
    assert service_interactions_dir.exists()
    assert len(service_interactions_dir.listdir()) == 1
    assert len(service_interactions_dir.join('TestServiceA').listdir()) == 2

    out_file = service_interactions_dir.join('TestServiceA').join('interaction_1.yaml').read()
    result_recording = yaml_load(out_file)
    assert expected_recording == result_recording
