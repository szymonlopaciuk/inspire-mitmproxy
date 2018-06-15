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

from mitmproxy.http import HTTPResponse
from mitmproxy.net.http.headers import Headers

from inspire_mitmproxy.http import MITMHeaders, MITMResponse


TEST_DICT_RESPONSE = {
    'status': {
        'code': 200,
        'message': 'OK',
    },
    'body': 'Witaj, świecie!',
    'headers': {
        'Content-Type': ['text/plain; charset=ISO-8859-2'],
        'Date': ['Wed, 21 Mar 2018 12:47:18 GMT'],
        'Server': ['nginx/1.12.2'],
    }
}

TEST_DICT_RESPONSE_WITH_BYTES_BODY = {
    'status': {
        'code': 200,
        'message': 'OK',
    },
    'body': b'Witaj, \xb6wiecie!',
    'headers': {
        'Content-Type': ['text/plain; charset=ISO-8859-2'],
        'Date': ['Wed, 21 Mar 2018 12:47:18 GMT'],
        'Server': ['nginx/1.12.2'],
    }
}

TEST_DICT_RESPONSE_GZIP = {
    'status': {
        'code': 200,
        'message': 'OK'
    },
    # gzipped utf-8-encoded "Hello, world!"
    'body': b'x\x9c\xf3H\xcd\xc9\xc9\xd7Q(\xcf/\xcaIQ\x04\x00 ^\x04\x8a',
    'headers': {
        'Content-Type': ['text/plain; charset=UTF-8'],
        'Date': ['Wed, 21 Mar 2018 12:47:18 GMT'],
        'Server': ['nginx/1.12.2'],
        'Content-Encoding': ['gzip']
    }
}

TEST_MITM_RESPONSE = HTTPResponse(
    http_version='HTTP/1.1',
    status_code=200,
    reason='OK',
    headers=Headers(
        fields=[
            (b'Content-Type', b'text/plain; charset=ISO-8859-2'),
            (b'Date', b'Wed, 21 Mar 2018 12:47:18 GMT'),
            (b'Server', b'nginx/1.12.2'),
        ]
    ),
    content=b'Witaj, \xb6wiecie!',
)

TEST_MITM_RESPONSE_GZIP = HTTPResponse(
    http_version='HTTP/1.1',
    status_code=200,
    reason='OK',
    headers=Headers(
        fields=[
            (b'Content-Type', b'text/plain; charset=UTF-8'),
            (b'Date', b'Wed, 21 Mar 2018 12:47:18 GMT'),
            (b'Server', b'nginx/1.12.2'),
            (b'Content-Encoding', b'gzip'),
        ]
    ),
    # gzipped utf-8-encoded "Hello, world!"
    content=b'x\x9c\xf3H\xcd\xc9\xc9\xd7Q(\xcf/\xcaIQ\x04\x00 ^\x04\x8a',
)

TEST_RESPONSE = MITMResponse(
    status_code=200,
    status_message='OK',
    body="Witaj, świecie!",
    headers=MITMHeaders({
        'Content-Type': ['text/plain; charset=ISO-8859-2'],
        'Date': ['Wed, 21 Mar 2018 12:47:18 GMT'],
        'Server': ['nginx/1.12.2'],
    }),
    original_encoding='ISO-8859-2',
    http_version='HTTP/1.1',
)

TEST_RESPONSE_WITH_BYTES_BODY = MITMResponse(
    status_code=200,
    status_message='OK',
    body=b"Witaj, \xb6wiecie!",
    headers=MITMHeaders({
        'Content-Type': ['text/plain; charset=ISO-8859-2'],
        'Date': ['Wed, 21 Mar 2018 12:47:18 GMT'],
        'Server': ['nginx/1.12.2'],
    }),
    original_encoding='ISO-8859-2',
    http_version='HTTP/1.1',
)

TEST_RESPONSE_GZIP = MITMResponse(
    status_code=200,
    status_message='OK',
    headers=MITMHeaders({
        'Content-Type': ['text/plain; charset=UTF-8'],
        'Date': ['Wed, 21 Mar 2018 12:47:18 GMT'],
        'Server': ['nginx/1.12.2'],
        'Content-Encoding': ['gzip']
    }),
    # gzipped utf-8-encoded "Hello, world!"
    body=b'x\x9c\xf3H\xcd\xc9\xc9\xd7Q(\xcf/\xcaIQ\x04\x00 ^\x04\x8a',
)


def test_response_from_mitmproxy():
    result = MITMResponse.from_mitmproxy(TEST_MITM_RESPONSE)
    expected = TEST_RESPONSE

    assert result == expected


def test_response_from_mitmproxy_gzip():
    result = MITMResponse.from_mitmproxy(TEST_MITM_RESPONSE_GZIP)
    expected = TEST_RESPONSE_GZIP

    assert result == expected


def test_response_from_dict():
    result = MITMResponse.from_dict(TEST_DICT_RESPONSE)
    expected = TEST_RESPONSE

    assert result == expected


def test_response_from_dict_gzip():
    result = MITMResponse.from_dict(TEST_DICT_RESPONSE_GZIP)
    expected = TEST_RESPONSE_GZIP

    assert result == expected


def test_response_to_mitmproxy():
    result = TEST_RESPONSE.to_mitmproxy()
    expected = TEST_MITM_RESPONSE

    assert result == expected


def test_response_to_mitmproxy_gzip():
    result = TEST_RESPONSE_GZIP.to_mitmproxy()
    expected = TEST_MITM_RESPONSE_GZIP

    assert result == expected


def test_response_to_dict():
    result = TEST_RESPONSE.to_dict()
    expected = TEST_DICT_RESPONSE

    assert result == expected


def test_response_to_dict_gzip():
    result = TEST_RESPONSE_GZIP.to_dict()
    expected = TEST_DICT_RESPONSE_GZIP

    assert result == expected


def test_dict_responses_from_bytes_and_str_equal():
    result_from_string = MITMResponse.from_dict(TEST_DICT_RESPONSE)
    result_from_bytes = MITMResponse.from_dict(TEST_DICT_RESPONSE_WITH_BYTES_BODY)

    assert result_from_string == result_from_bytes


def test_responses_from_bytes_and_str_equal():
    assert TEST_RESPONSE == TEST_RESPONSE_WITH_BYTES_BODY
