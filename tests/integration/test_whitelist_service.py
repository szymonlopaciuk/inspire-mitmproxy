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

from mock import patch
from pytest import fixture, raises

from inspire_mitmproxy.dispatcher import Dispatcher
from inspire_mitmproxy.errors import DoNotIntercept
from inspire_mitmproxy.http import MITMHeaders, MITMRequest
from inspire_mitmproxy.services.whitelist_service import WhitelistService


@fixture(scope='function')
def dispatcher() -> Dispatcher:
    with patch.object(Dispatcher, 'SERVICE_LIST', [WhitelistService]):
        return Dispatcher()


def test_whitelist_service_raises(dispatcher):
    with raises(DoNotIntercept):
        dispatcher.process_request(
            MITMRequest(
                method='GET',
                url='http://test-indexer:9200/records-hep/fake',
                body="{}",
                headers=MITMHeaders({
                    'Host': ['test-indexer:9200'],
                    'Accept': ['application/json'],
                })
            )
        )
