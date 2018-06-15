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

"""Tests for the ManagementService"""

from os import environ

from mock import patch
from pytest import fixture, mark, raises

from inspire_mitmproxy.errors import InvalidRequest
from inspire_mitmproxy.http import MITMHeaders, MITMRequest, MITMResponse
from inspire_mitmproxy.services import BaseService, ManagementService


@fixture(scope='function')
def management_service() -> ManagementService:
    class TestService(BaseService):
        SERVICE_HOSTS = ['test-service.local']

    mgmt_service = ManagementService([TestService()])

    mgmt_service.config = {
        'active_scenario': None,
        'a_setting': 'value',
    }

    return mgmt_service


@fixture
def fake_scenarios_dir(tmpdir) -> str:
    scenarios = tmpdir.mkdir('scenarios')

    scenario1 = scenarios.mkdir('scenario1')
    scenario2 = scenarios.mkdir('scenario2')

    scenario1_serviceA = scenario1.mkdir('A')
    scenario2_serviceA = scenario2.mkdir('A')
    scenario2_serviceB = scenario2.mkdir('B')

    scenario1_serviceA.join('1.yaml').ensure()
    scenario1_serviceA.join('2.yaml').ensure()

    scenario2_serviceA.join('1.yaml').ensure()
    scenario2_serviceB.join('1.yaml').ensure()
    scenario2_serviceB.join('2.yaml').ensure()
    scenario2_serviceB.join('3.yaml').ensure()

    environ['SCENARIOS_PATH'] = scenarios.strpath
    return scenarios.strpath


def test_management_service_get_services(management_service):
    result = management_service.get_services()
    expected = {
        0: {
            'class': 'ManagementService',
            'service_hosts': ['mitm-manager.local']
        },
        1: {
            'class': 'TestService',
            'service_hosts': ['test-service.local']
        }
    }

    assert expected == result


def test_management_service_get_scenarios(fake_scenarios_dir, management_service):
    result = management_service.get_scenarios()
    expected = {
        'scenario1': {
            'responses': {
                'A': ['1.yaml', '2.yaml'],
            }
        },
        'scenario2': {
            'responses': {
                'A': ['1.yaml'],
                'B': ['1.yaml', '2.yaml', '3.yaml'],
            }
        },
    }

    assert expected == result


def test_management_service_get_config(management_service):
    result = management_service.get_config()
    expected = {
        'active_scenario': None,
        'a_setting': 'value',
    }

    assert expected == result


def test_management_service_put_config(management_service):
    management_service.put_config(
        MITMRequest(
            url='http://mitm-manager.local/config',
            body='{"active_scenario": "a scenario"}'
        )
    )
    result = management_service.config

    expected = {
        'active_scenario': 'a scenario',
        'a_setting': 'value',
    }

    assert expected == result

    for service in management_service.services:
        assert service.active_scenario == 'a scenario'


@mark.parametrize(
    'request_body',
    [
        'definitely not valid JSON',
        '["parses as valid json, but is not a dict update"]',
    ],
)
def test_management_service_put_config_malformed_raises(management_service, request_body):
    request = MITMRequest(
        method='PUT',
        url='http://mitm-manager.local',
        body=request_body,
    )
    with raises(InvalidRequest):
        management_service.put_config(request)


def test_management_service_post_config(management_service):
    management_service.post_config(
        MITMRequest(
            method='POST',
            url='http://mitm-manager.local/config',
            body='{"active_scenario": "a scenario"}',
        )
    )
    result = management_service.config

    expected = {
        'active_scenario': 'a scenario',
    }

    assert expected == result

    for service in management_service.services:
        assert service.active_scenario == 'a scenario'


def test_management_service_post_config_malformed_raises(management_service):
    with raises(InvalidRequest):
        management_service.put_config(
            MITMRequest(
                method='POST',
                url='http://mitm-manager.local/config',
                body='definitely not valid JSON',
            )
        )


@mark.xfail
def test_management_service_post_config_array_raises(management_service):
    with raises(InvalidRequest):
        management_service.post_config({
            'body': '["parses as valid json, but is not a dict update"]'
        })


@mark.parametrize(
    'request_body, expected_state',
    [
        ('{"enable": true}', True),
        ('{"enable": false}', False),
    ],
)
def test_management_service_set_recording(management_service, request_body, expected_state):
    expected_response = {
        'enabled': expected_state,
    }

    result_response = management_service.set_recording(
        MITMRequest(
            method='PUT',
            url='http://mitm-manager.local/record',
            body=request_body
        )
    )

    result = management_service.is_recording

    assert expected_state == result

    for service in management_service.services:
        assert expected_state == service.is_recording

    assert expected_response == result_response


def test_management_service_set_recording_changes(management_service):
    initial_state = management_service.is_recording
    desired_state = not initial_state

    expected_response = {
        'enabled': desired_state,
    }

    result_response = management_service.set_recording(
        MITMRequest(
            method='PUT',
            url='http://mitm-manager.local/record',
            body=f'{{"enable": {"true" if desired_state else "false"}}}'
        )
    )

    result = management_service.is_recording

    assert desired_state == result

    for service in management_service.services:
        assert desired_state == service.is_recording

    assert expected_response == result_response


@mark.parametrize(
    'request_body',
    [
        'definitely not valid JSON',
        '["parses as valid json, but is not a valid record param"]',
        '{"enable key not here": "wrong"}',
    ],
)
def test_management_service_set_recording_malformed_raises(management_service, request_body):
    request = MITMRequest(
        method='PUT',
        url='http://mitm-manager.local/record',
        body=request_body
    )
    with raises(InvalidRequest):
        management_service.set_recording(request)


def test_management_service_build_response(management_service):
    with patch(
        'inspire_mitmproxy.services.management_service.get_current_version',
        return_value='0.0.1',
    ):
        result = management_service.build_response(201, json_message={'test': 'message'})

    expected = MITMResponse(
        body='{\n  "test": "message"\n}',
        headers=MITMHeaders({
            'Content-Type': ['application/json; encoding=UTF-8'],
            'Server': ['inspire-mitmproxy/0.0.1'],
        }),
        status_code=201,
    )

    assert expected == result


def test_management_service_build_response_empty_object_body(management_service):
    with patch(
        'inspire_mitmproxy.services.management_service.get_current_version',
        return_value='0.0.1',
    ):
        result = management_service.build_response(200, json_message={})

    expected = MITMResponse(
        body='{}',
        headers=MITMHeaders({
            'Content-Type': ['application/json; encoding=UTF-8'],
            'Server': ['inspire-mitmproxy/0.0.1'],
        }),
        status_code=200,
    )

    assert expected == result
