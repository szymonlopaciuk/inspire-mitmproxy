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

from inspire_mitmproxy.http import MITMHeaders, encoding_by_header


TEST_HEADERS = MITMHeaders({
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

TEST_HEADERS_NO_CHARSET = MITMHeaders({
    'Content-Type': ['text/plain'],
    'Access-Control-Expose-Headers': [
        'Content-Type, ETag, Link, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, '
        'X-Multiple-Values',
    ],
    'X-Multiple-Values': [
        'Value1',
        'Value2',
    ]
})


def test_encoding_by_header():
    result = encoding_by_header(TEST_HEADERS)
    expected = 'ASCII'

    assert result == expected


def test_encoding_by_header_defaults_to_utf_8():
    result = encoding_by_header(TEST_HEADERS_NO_CHARSET)
    expected = 'utf-8'

    assert result == expected
