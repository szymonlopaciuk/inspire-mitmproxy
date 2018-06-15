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

"""Interaction is a recording of a request-response pair that is to be replayed during the test.

Scenarios are what interactions are organised into. For inspire-next they reside at::

    tests/e2e/scenarios

The directory structure is as follows::

    scenarios/<scenario_name>/<service_name>/<interaction>.yaml

Scenario name can be anything,
but by convention it is the name of the E2E test without the `test_` prefix. Service name has to
match one of the services defined in :attr:`inspire_mitmproxy.services`. Name of the interaction
can be anything, and is only for informative purposes. When recorded automatically, interactions
are named in sequence of `interaction_0.yaml`, `interaction_1.yaml`, and so on.
"""

from logging import getLogger
from os.path import expandvars
from pathlib import Path
from pprint import pformat
from re import compile
from threading import Timer
from typing import Any, Dict, List, Optional, Pattern, Union

import requests
from yaml import dump as yaml_dump
from yaml import load as yaml_load

from .http import MITMRequest, MITMResponse, response_to_string


logger = getLogger(__name__)


class Interaction:
    DEFAULT_EXACT_MATCH_FIELDS: List[str] = ['url', 'method', 'body']
    DEFAULT_REGEX_MATCH_FIELDS: Dict[str, Pattern[str]] = {}
    DEFAULT_CALLBACK_DELAY = 0.5

    DEFAULT_NAME_PATTERN = 'interaction_{}'
    DEFAULT_NAME_MATCH_REGEX = compile(r'^interaction_(\d+)$')

    def __init__(
        self,
        name: str,
        request: MITMRequest,
        response: MITMResponse,
        match: Optional[dict] = None,
        callbacks: Optional[List[dict]] = None,
    ) -> None:
        self.name = name
        self.request = request
        self.response = response
        self.match = match or {}
        self.callbacks = callbacks or []

    @classmethod
    def from_file(cls, interaction_file: Optional[Path]) -> 'Interaction':
        interaction_string = interaction_file.read_text()  # type: ignore
        interaction_dict = yaml_load(interaction_string)

        return cls(
            name=interaction_file.stem,  # type: ignore
            request=MITMRequest.from_dict(interaction_dict['request']),
            response=MITMResponse.from_dict(interaction_dict['response']),
            match=interaction_dict.get('match'),
            callbacks=interaction_dict.get('callbacks'),
        )

    def to_dict(self) -> dict:
        serialized_interaction: Dict[str, Any] = {
            'request': self.request.to_dict(),
            'response': self.response.to_dict(),
            'match': self.match,
            'callbacks': self.callbacks,
        }

        return serialized_interaction

    @property
    def exact_match_fields(self) -> List[str]:
        """Fields specified match exactly."""
        if not self.match:
            return self.DEFAULT_EXACT_MATCH_FIELDS

        try:
            return self.match['exact']
        except KeyError:
            return []

    @property
    def regex_match_fields(self) -> Dict[str, Pattern[str]]:
        """Fields specified (as key in the dictionary) match on the regex defined in value."""
        if not self.match:
            return self.DEFAULT_REGEX_MATCH_FIELDS

        try:
            regexes = self.match['regex']
            return {field: compile(regex) for field, regex in regexes.items()}
        except KeyError:
            return {}

    def _matches_by_exact_rules(self, request: MITMRequest) -> bool:
        for match_on in self.exact_match_fields:
            if self.request[match_on] != request[match_on]:
                return False

        return True

    def _matches_by_regex_rules(self, request: MITMRequest) -> bool:
        for match_on, regex in self.regex_match_fields.items():
            if not regex.match(request[match_on]):
                return False

        return True

    def matches_request(self, request: MITMRequest) -> bool:
        """Check if interaction matches the request.

        By default the request is matching the prerecoded request if their urls, methods and bodies
        are equal (see :attr:`~inspire_mitmproxy.interaction.Interaction.DEFAULT_EXACT_MATCH_FIELDS`
        and :attr:`~inspire_mitmproxy.interaction.Interaction.DEFAULT_REGEX_MATCH_FIELDS`). You
        can specify custom matching rules per interaction by using the ``match`` field in the
        interaction YAML file.
        """
        return self._matches_by_exact_rules(request) and self._matches_by_regex_rules(request)

    @staticmethod
    def execute_callback(request: MITMRequest, delay: Union[int, float]):
        def execute_request(_request: MITMRequest):
            request_params = dict(
                method=request.method,
                url=expandvars(request.url),
                data=request.body,
                headers={
                    key: expandvars(request.headers[key])
                    for key in request.headers.keys()
                },
                timeout=10,
            )
            logger.warning("Executing callback:\n%s", pformat(request_params))

            response = requests.request(**request_params)
            if not response.ok:
                logger.error("Error executing callback:\n%s", response_to_string(response))

        timer = Timer(delay, execute_request, args=[request])
        timer.start()

    def execute_callbacks(self):
        for callback in self.callbacks:
            request = MITMRequest.from_dict(callback['request'])
            self.execute_callback(
                request=request,
                delay=callback.get('delay', self.DEFAULT_CALLBACK_DELAY)
            )

    @classmethod
    def get_next_sequence_number_in_dir(cls, directory: Path) -> int:
        def _next_sequence_number_after_file(path):
            if not path.is_file() or path.suffix != '.yaml':
                return 0

            seq_number_match = cls.DEFAULT_NAME_MATCH_REGEX.match(path.stem)
            if not seq_number_match:
                return 0

            cur_seq_number = int(seq_number_match.group(1))
            return cur_seq_number + 1

        next_seq_number = 0
        for interaction_path in directory.iterdir():
            candidate_next_seq_number = _next_sequence_number_after_file(interaction_path)
            next_seq_number = max(next_seq_number, candidate_next_seq_number)

        return next_seq_number

    @classmethod
    def next_in_dir(
        cls,
        directory: Path,
        request: MITMRequest,
        response: MITMResponse
    ) -> 'Interaction':
        """Create a new interaction with a name taking from next available in directory."""
        sequence_number = cls.get_next_sequence_number_in_dir(directory)
        new_name = cls.DEFAULT_NAME_PATTERN.format(sequence_number)
        return Interaction(name=new_name, request=request, response=response)

    def save_in_dir(self, directory: Path):
        """Save the interaction to a file.

        Structure of interactions:

        .. code-block:: yaml

            request:
              body: 'Body of the request'           # string (or bytes)
              headers:
                Content-Type: ['text/plain']        # array of strings (case of repeated headers)
                Host: ['samplehost.local']
              method: 'PUT'                         # string (one of allowed HTTP method names)
              url: 'http://samplehost.local/path'   # string
            response:
              body: 'Body of the response'          # string (or bytes)
              headers:
                Content-Type: ['text/plain']        # array of strings (ditto)
              status:
                code: 200                           # integer
                message: OK                         # string
            match:
              exact:
              - method                              # array of one of the keys in request
              - uri
              regex:
                method: 'PUT|POST'                  # dict with keys of the keys in request
            callbacks:
            - delay: 10                             # integer (seconds)
              request: {}                           # follows request above (as callback is executed
                                                    # using python-requests, which does not support
                                                    # multiple header values, only first value of
                                                    # each header will be used)
        """
        output_path = directory / f'{self.name}.yaml'
        output_path.write_text(yaml_dump(self.to_dict()))

    def __repr__(self):
        return f'Interaction(name={self.name!r}, request={self.request!r}, ' \
            f'response={self.response!r}, match={self.match!r}, callbacks={self.callbacks!r})'

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.request == other.request
            and self.response == other.response
            and self.match == other.match
            and self.callbacks == other.callbacks
        )
