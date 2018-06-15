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

from mitmproxy.net.http.headers import Headers

from inspire_mitmproxy.http import MITMHeaders


TEST_DICT_HEADERS = {
    'Content-Type': ['text/plain; charset=ASCII'],
    'Access-Control-Expose-Headers': [
        'Content-Type, ETag, Link, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, '
        'X-Multiple-Values',
    ],
    'X-Multiple-Values': [
        'Value1',
        'Value2',
    ]
}


TEST_MITM_HEADERS = Headers(
    fields=[
        (b'Content-Type', b'text/plain; charset=ASCII'),
        (b'Access-Control-Expose-Headers', b'Content-Type, ETag, Link, X-RateLimit-Limit, '
            b'X-RateLimit-Remaining, X-RateLimit-Reset, X-Multiple-Values'),
        (b'X-Multiple-Values', b'Value1'),
        (b'X-Multiple-Values', b'Value2'),
    ]
)


TEST_HEADERS = MITMHeaders(headers={
    'Content-Type': ['text/plain; charset=ASCII'],
    'Access-Control-Expose-Headers': [
        'Content-Type, ETag, Link, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, '
        'X-Multiple-Values',
    ],
    'X-Multiple-Values': [
        'Value1',
        'Value2',
    ]
})


def test_headers_from_dict():
    expected = TEST_HEADERS
    result = MITMHeaders.from_dict(TEST_DICT_HEADERS)

    assert expected == result


def test_headers_from_mitmproxy():
    expected = TEST_HEADERS
    result = MITMHeaders.from_mitmproxy(TEST_MITM_HEADERS)

    assert expected == result


def test_headers_to_dict():
    expected = TEST_DICT_HEADERS
    result = TEST_HEADERS.to_dict()

    assert expected == result


def test_headers_to_mitmproxy():
    expected = TEST_MITM_HEADERS
    result = TEST_HEADERS.to_mitmproxy()

    assert expected == result


def test_headers_getitem():
    expected = 'Value1'
    result = TEST_HEADERS['X-Multiple-Values']

    assert expected == result


def test_headers_keys():
    expected = ['Content-Type', 'Access-Control-Expose-Headers', 'X-Multiple-Values']
    result = TEST_HEADERS.keys()

    assert expected == list(result)
