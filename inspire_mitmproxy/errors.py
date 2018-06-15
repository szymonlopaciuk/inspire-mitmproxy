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

"""INSPIRE-MITMProxy Errors"""

from .http import MITMRequest


class MITMProxyHTTPError(Exception):
    http_status_code = 500


class NoServicesForRequest(MITMProxyHTTPError):
    def __init__(self, request: MITMRequest) -> None:
        self.http_status_code = 501
        message = f"None of the registered services can handle this request: {request}"
        super().__init__(message)


class ServiceNotFound(MITMProxyHTTPError):
    def __init__(self, service_name: str) -> None:
        self.http_status_code = 404
        message = f"Service {service_name} doesn't exist"
        super().__init__(message)


class RequestNotHandledInService(MITMProxyHTTPError):
    def __init__(self, service_name: str, request: MITMRequest) -> None:
        self.http_status_code = 501
        message = f"{service_name} can't handle the request {request}"
        super().__init__(message)


class InvalidRequest(MITMProxyHTTPError):
    def __init__(self, service_name: str, request: MITMRequest) -> None:
        self.http_status_code = 400
        message = f"Invalid request {request} for service {service_name}"
        super().__init__(message)


class DoNotIntercept(Exception):
    def __init__(self, service_name: str, request: MITMRequest) -> None:
        message = f"Allow request {request} in {service_name} to pass through to the outside"
        super().__init__(message)


class NoMatchingRecording(MITMProxyHTTPError):
    def __init__(self, service_name: str, request: MITMRequest) -> None:
        self.http_status_code = 501
        message = f"Service {service_name} cannot handle this request: {request}"
        super().__init__(message)


class ScenarioNotInService(MITMProxyHTTPError):
    def __init__(self, service_name: str, scenario: str) -> None:
        self.http_status_code = 501
        message = f"Scenario {scenario} not found in service {service_name}"
        super().__init__(message)
