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

"""Base for fake services."""

from os import environ
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import splitport  # type: ignore
from urllib.parse import urlparse

from ..errors import DoNotIntercept, NoMatchingRecording, ScenarioNotInService
from ..http import MITMRequest, MITMResponse
from ..interaction import Interaction


class BaseService:
    """Mocked service base."""
    SERVICE_HOSTS: List[str] = []

    def __init__(self):
        self.active_scenario: str = 'default'
        self.interactions_replayed: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.is_recording = False

    @property
    def name(self):
        return type(self).__name__

    def set_active_scenario(self, active_scenario: str):
        self.active_scenario = active_scenario
        self.interactions_replayed[self.active_scenario] = {}

    def handles_request(self, request: MITMRequest) -> bool:
        """Can this service handle the request?"""
        try:
            host = splitport(request.headers['Host'])[0]
        except (TypeError, KeyError):
            host = urlparse(request.url).hostname

        return host in self.SERVICE_HOSTS

    def _get_first_matching_interaction(self, request):
        for interaction in self.get_interactions_for_active_scenario():
            if interaction.matches_request(request):
                return interaction

    def _raise_do_not_intercept_if_recording(self, request):
        if self.is_recording:
            raise DoNotIntercept(self.name, request)

    def process_request(self, request):
        try:
            matched_interaction = self._get_first_matching_interaction(request)
        except ScenarioNotInService:
            self._raise_do_not_intercept_if_recording(request)
            raise

        if matched_interaction is None:
            self._raise_do_not_intercept_if_recording(request)
            raise NoMatchingRecording(self.name, request)

        response = matched_interaction.response
        matched_interaction.execute_callbacks()
        self.increment_interaction_count(matched_interaction.name)
        return response

    def process_response(self, request: MITMRequest, response: MITMResponse):
        """Perform operations based on live response."""
        if not self.is_recording:
            return

        current_scenario_dir = self.get_path_for_active_scenario_dir(create=True)
        interaction = Interaction.next_in_dir(
            directory=current_scenario_dir,
            request=request,
            response=response,
        )
        interaction.save_in_dir(current_scenario_dir)

    def increment_interaction_count(self, interaction_name: str):
        try:
            self.interactions_replayed[self.active_scenario][interaction_name]['num_calls'] += 1
        except KeyError:
            self.interactions_replayed.setdefault(
                self.active_scenario,
                {},
            ).setdefault(
                interaction_name,
                {'num_calls': 1},
            )

    def get_path_for_active_scenario_dir(self, create=False) -> Path:
        scenarios_path = Path(environ.get('SCENARIOS_PATH', './scenarios/'))
        interactions_dir = scenarios_path / self.active_scenario / self.name

        if create:
            interactions_dir.mkdir(parents=True, exist_ok=True)

        return interactions_dir

    def get_interactions_in_scenario(self, scenario_path: Path) -> List[Interaction]:
        return [
            Interaction.from_file(interaction_file=interaction_path)
            for interaction_path in sorted(scenario_path.iterdir())
            if interaction_path.is_file() and interaction_path.suffix == '.yaml'
        ]

    def get_interactions_for_active_scenario(self) -> List[Interaction]:
        """Get a list of scenarios"""
        scenario_dir = self.get_path_for_active_scenario_dir(create=False)

        if not scenario_dir.exists():
            raise ScenarioNotInService(self.name, self.active_scenario)

        return self.get_interactions_in_scenario(scenario_dir)
