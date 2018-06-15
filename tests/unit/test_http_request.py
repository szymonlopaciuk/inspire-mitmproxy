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

from mitmproxy.http import HTTPRequest

from inspire_mitmproxy.http import MITMHeaders, MITMRequest


TEST_REQUEST = MITMRequest(
    body='{"message": "Witaj, świecie!"}',
    headers=MITMHeaders({
        'Content-Type': ['application/json; charset=UTF-8'],
        'Accept-Encoding': ['gzip, deflate'],
        'Connection': ['keep-alive'],
        'User-Agent': ['python-requests/2.18.4'],
    }),
    method='GET',
    url='http://127.0.0.1/test'
)


TEST_REQUEST_GZIP = MITMRequest(
    # gzipped utf-8-encoded "Hello, world!"
    body=b'x\x9c\xf3H\xcd\xc9\xc9\xd7Q(\xcf/\xcaIQ\x04\x00 ^\x04\x8a',
    headers=MITMHeaders({
        'Content-Type': ['text/plain; charset=UTF-8'],
        'Content-Encoding': ['gzip'],
        'Accept-Encoding': ['gzip, deflate'],
        'Connection': ['keep-alive'],
        'User-Agent': ['python-requests/2.18.4'],
    }),
    method='GET',
    url='http://127.0.0.1/test'
)


TEST_REQUEST_WITH_BYTES_BODY = MITMRequest(
    body=b'{"message": "Witaj, \xc5\x9bwiecie!"}',
    headers=MITMHeaders({
        'Content-Type': ['application/json; charset=UTF-8'],
        'Accept-Encoding': ['gzip, deflate'],
        'Connection': ['keep-alive'],
        'User-Agent': ['python-requests/2.18.4'],
    }),
    method='GET',
    url='http://127.0.0.1/test'
)


TEST_DICT_REQUEST = {
    'body': '{"message": "Witaj, świecie!"}',
    'headers': {
        'Content-Type': ['application/json; charset=UTF-8'],
        'Accept-Encoding': ['gzip, deflate'],
        'Connection': ['keep-alive'],
        'User-Agent': ['python-requests/2.18.4'],
    },
    'method': 'GET',
    'url': 'http://127.0.0.1/test',
}


TEST_DICT_REQUEST_GZIP = {
    # gzipped utf-8-encoded "Hello, world!"
    'body': b'x\x9c\xf3H\xcd\xc9\xc9\xd7Q(\xcf/\xcaIQ\x04\x00 ^\x04\x8a',
    'headers': {
        'Content-Type': ['text/plain; charset=UTF-8'],
        'Content-Encoding': ['gzip'],
        'Accept-Encoding': ['gzip, deflate'],
        'Connection': ['keep-alive'],
        'User-Agent': ['python-requests/2.18.4'],
    },
    'method': 'GET',
    'url': 'http://127.0.0.1/test',
}


TEST_MITM_REQUEST = HTTPRequest(
    first_line_format='absolute',
    method='GET',
    scheme='http',
    host='127.0.0.1',
    port=80,
    path='/test',
    http_version='HTTP/1.1',
    headers=[
        (b'Content-Type', b'application/json; charset=UTF-8'),
        (b'Accept-Encoding', b'gzip, deflate'),
        (b'Connection', b'keep-alive'),
        (b'User-Agent', b'python-requests/2.18.4'),
    ],
    content=b'{"message": "Witaj, \xc5\x9bwiecie!"}'
)


TEST_MITM_REQUEST_GZIP = HTTPRequest(
    first_line_format='absolute',
    method='GET',
    scheme='http',
    host='127.0.0.1',
    port=80,
    path='/test',
    http_version='HTTP/1.1',
    headers=[
        (b'Content-Type', b'text/plain; charset=UTF-8'),
        (b'Content-Encoding', b'gzip'),
        (b'Accept-Encoding', b'gzip, deflate'),
        (b'Connection', b'keep-alive'),
        (b'User-Agent', b'python-requests/2.18.4'),
    ],
    # gzipped utf-8-encoded "Hello, world!"
    content=b'x\x9c\xf3H\xcd\xc9\xc9\xd7Q(\xcf/\xcaIQ\x04\x00 ^\x04\x8a',
)


def test_request_from_mitmproxy():
    result = MITMRequest.from_mitmproxy(TEST_MITM_REQUEST)
    expected = TEST_REQUEST

    assert result == expected


def test_request_from_mitmproxy_gzip():
    result = MITMRequest.from_mitmproxy(TEST_MITM_REQUEST_GZIP)
    expected = TEST_REQUEST_GZIP

    assert result == expected


def test_request_from_dict():
    result = MITMRequest.from_dict(TEST_DICT_REQUEST)
    expected = TEST_REQUEST

    assert result == expected


def test_request_from_dict_gzip():
    result = MITMRequest.from_dict(TEST_DICT_REQUEST_GZIP)
    expected = TEST_REQUEST_GZIP

    assert result == expected


def test_request_to_mitmproxy():
    result = TEST_REQUEST.to_mitmproxy()
    expected = TEST_MITM_REQUEST

    assert result == expected


def test_request_to_mitmproxy_gzip():
    result = TEST_REQUEST_GZIP.to_mitmproxy()
    expected = TEST_MITM_REQUEST_GZIP

    assert result == expected


def test_request_to_dict():
    result = TEST_REQUEST.to_dict()
    expected = TEST_DICT_REQUEST

    assert result == expected


def test_request_to_dict_gzip():
    result = TEST_REQUEST_GZIP.to_dict()
    expected = TEST_DICT_REQUEST_GZIP

    assert result == expected


def test_request_with_bytes_body():
    assert TEST_REQUEST == TEST_REQUEST_WITH_BYTES_BODY
