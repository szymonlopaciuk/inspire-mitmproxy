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

"""Wrappers for HTTP objects."""

from cgi import parse_header
from copy import copy, deepcopy
from socket import getservbyname
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from mitmproxy.http import HTTPRequest, HTTPResponse
from mitmproxy.net.http.headers import Headers
from mitmproxy.net.http.status_codes import RESPONSES


def encoding_by_header(headers: 'MITMHeaders') -> str:
    """Extract charset param from Content-Type or Accept headers"""
    try:
        content_type = headers['Content-Type']
        _, params = parse_header(content_type)
        return params['charset']
    except KeyError:
        return 'utf-8'


class MITMHeaders:
    def __init__(self, headers: Dict[str, List[str]]) -> None:
        self.headers: Dict[str, List[str]] = {}
        for header_name, header_value in headers.items():
            header_name = header_name.title()
            self.headers[header_name] = copy(header_value)

    @classmethod
    def from_dict(cls, headers_dict: Dict[str, List[str]]) -> 'MITMHeaders':
        return cls(headers=headers_dict)

    @classmethod
    def from_mitmproxy(cls, headers: Headers) -> 'MITMHeaders':
        header_dict: Dict[str, List[str]] = {}

        for key, value in headers.fields:
            key, value = key.decode('ascii'), value.decode('ascii')

            if key in header_dict:
                header_dict[key].append(value)
            else:
                header_dict[key] = [value]

        return cls(headers=header_dict)

    def to_dict(self) -> Dict[str, List[str]]:
        return deepcopy(self.headers)

    def to_mitmproxy(self) -> Headers:
        fields = []

        for key, values in self.headers.items():
            for value in values:
                fields.append(
                    (key.encode('ascii'), value.encode('ascii'))
                )

        return Headers(fields=fields)

    def __getitem__(self, item: str) -> str:
        try:
            return self.headers[item.title()][0]
        except IndexError:
            raise KeyError(item.title())

    def __eq__(self, other) -> bool:
        return self.headers == other.headers

    def __repr__(self):
        return f'MITMHeaders(headers={repr(self.headers)})'


class MITMRequest:
    def __init__(
        self,
        url: str,
        method: str = 'GET',
        body: Optional[str] = None,
        headers: Optional[MITMHeaders] = None,
        original_encoding: Optional[str] = None,
        http_version: Optional[str] = None,
    ) -> None:
        self.url = url
        self.method = method
        self.body = body or ''
        self.headers = headers or MITMHeaders({})
        self.original_encoding = original_encoding or encoding_by_header(self.headers)
        self.http_version = http_version or 'HTTP/1.1'

    @classmethod
    def from_mitmproxy(cls, request: HTTPRequest) -> 'MITMRequest':
        encoding = encoding_by_header(MITMHeaders.from_mitmproxy(request.headers))

        return cls(
            url=request.url,
            method=request.method,
            body=request.content.decode(encoding),
            headers=MITMHeaders.from_mitmproxy(request.headers),
            original_encoding=encoding,
            http_version=request.http_version,
        )

    @classmethod
    def from_dict(cls, request: Dict[str, Any]) -> 'MITMRequest':
        encoding = encoding_by_header(MITMHeaders.from_dict(request['headers']))

        return cls(
            url=request['uri'],
            method=request['method'],
            body=request['body'],
            headers=MITMHeaders.from_dict(request['headers']),
            original_encoding=encoding,
        )

    def to_mitmproxy(self) -> HTTPRequest:
        parsed_url = urlparse(self.url)

        return HTTPRequest(
            first_line_format='absolute',
            method=self.method,
            scheme=parsed_url.scheme,
            host=parsed_url.hostname,
            port=parsed_url.port or getservbyname(parsed_url.scheme),
            path=parsed_url.path,
            http_version=self.http_version,
            headers=self.headers.to_mitmproxy(),
            content=self.body.encode(self.original_encoding),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'method': self.method,
            'uri': self.url,
            'body': self.body,
            'headers': self.headers.to_dict(),
        }

    def __eq__(self, other) -> bool:
        return (
            self.url == other.url
            and self.method == other.method
            and self.body == other.body
            and self.headers == other.headers
        )

    def __repr__(self):
        return f'MITMRequest("{self.url}", "{self.method}", ' \
            f'headers={self.headers}, body="{self.body}")'


class MITMResponse:
    def __init__(
        self,
        status_code: int = 200,
        status_message: Optional[str] = None,
        body: Optional[str] = None,
        headers: Optional[MITMHeaders] = None,
        original_encoding: Optional[str] = None,
        http_version: Optional[str] = None,
    ) -> None:
        self.status_code = status_code
        self.status_message = status_message or RESPONSES[status_code]
        self.body = body or ''
        self.headers = headers or MITMHeaders({})
        self.http_version = http_version or 'HTTP/1.1'
        self.original_encoding = original_encoding or encoding_by_header(self.headers)

    @classmethod
    def from_mitmproxy(cls, response: HTTPResponse) -> 'MITMResponse':
        encoding = encoding_by_header(MITMHeaders.from_mitmproxy(response.headers))

        return cls(
            status_code=response.status_code,
            status_message=response.reason,
            body=response.content.decode(encoding),
            headers=MITMHeaders.from_mitmproxy(response.headers),
            original_encoding=encoding,
            http_version=response.http_version,
        )

    @classmethod
    def from_dict(cls, response: Dict[str, Any]) -> 'MITMResponse':
        encoding = encoding_by_header(MITMHeaders.from_dict(response['headers']))

        body = response['body']
        if isinstance(body, bytes):
            body = body.decode(encoding)

        return cls(
            status_code=response['status']['code'],
            status_message=response['status']['message'],
            body=body,
            headers=MITMHeaders.from_dict(response['headers']),
            original_encoding=encoding
        )

    def to_mitmproxy(self) -> HTTPResponse:
        return HTTPResponse(
            http_version='HTTP/1.1',
            status_code=self.status_code,
            reason=self.status_message,
            headers=self.headers.to_mitmproxy(),
            content=self.body.encode(self.original_encoding),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': {
                'code': self.status_code,
                'message': self.status_message,
            },
            'body': self.body,
            'headers': self.headers.to_dict(),
        }

    def __eq__(self, other) -> bool:
        return (
            self.status_code == other.status_code
            and self.body == other.body
            and self.headers == other.headers
        )

    def __repr__(self):
        return f'MITMResponse({self.status_code}, "{self.status_message}", ' \
            f'headers={self.headers}, body="{self.body}")'
