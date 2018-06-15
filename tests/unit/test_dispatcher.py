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

from mock import patch
from pytest import fixture, mark, raises

from inspire_mitmproxy.dispatcher import Dispatcher
from inspire_mitmproxy.errors import NoServicesForRequest
from inspire_mitmproxy.http import MITMHeaders, MITMRequest, MITMResponse
from inspire_mitmproxy.services import BaseService


def make_test_service(url, message):
    class TestService(BaseService):
        SERVICE_HOSTS = [url]

        def process_request(self, request: dict):
            return MITMResponse(
                body=message,
                headers=MITMHeaders({
                    'Content-Type': ['text/plain'],
                })
            )

    return TestService


@fixture(scope='module')
def dispatcher():
    with patch.object(Dispatcher, 'SERVICE_LIST', [
        make_test_service('test-service-a.local', 'TestServiceA'),
        make_test_service('test-service-b.local', 'TestServiceB'),
        make_test_service('test-service-a.local', 'TestServiceC'),
    ]):
        return Dispatcher()


@mark.parametrize(
    'url, message',
    [
        ('http://test-service-a.local', b'TestServiceA'),
        ('http://test-service-b.local/some_path', b'TestServiceB'),
        ('http://test-service-a.local/other_path', b'TestServiceA'),
    ],
    ids=[
        'first',
        'second, with path',
        'match first, even though also matches third (ordered)'
    ]
)
def test_dispatcher_process_request(dispatcher, url, message):
    result = dispatcher.process_request(
        MITMRequest(
            url=url,
            headers=MITMHeaders({
                'Accept': ['text/plain'],
            })
        )
    )

    assert result.body == message


def test_dispatcher_process_request_fail_if_none_match(dispatcher):
    with raises(NoServicesForRequest):
        dispatcher.process_request(
            MITMRequest(
                url='http://test-service-z.local/does_not_exist',
                headers=MITMHeaders({
                    'Accept': ['text/plain'],
                })
            )
        )
