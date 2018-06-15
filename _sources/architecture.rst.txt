************
Architecture
************

INSPIRE-MITMProxy is a solution for running E2E tests in INSPIRE. It intercepts all HTTP(S) traffic
from the workers (web, task and crawler nodes) and either let's it pass through (e.g. when
communication happens with internal services, or while recording communication with external
service) or parses the incoming request and replies according to predefined (recorded) responses.


Dispatcher
++++++++++

Dispatcher is the object which decides which service is responsible for handling an incoming
request: all of the services are registered with the dispatcher. When a new request comes, the
dispatcher iterates through the services until it either finds one that handles the request (by
using :meth:`~inspire_mitmproxy.services.base_service.BaseService.handles_request`, or fails with
HTTP 501: :exc:`~inspire_mitmproxy.errors.NoServicesForRequest`.


Services
++++++++

Service is a basic building block of inspire-mitmproxy: each service imitates one of the external
services we are mocking. In the basic case it has defined hostnames on which it listens, and if
a request is matching one of those, it is passed to the service using
:meth:`~inspire_mitmproxy.services.base_service.BaseService.process_request`.


Management Service
++++++++++++++++++

:class:`~inspire_mitmproxy.services.management_service.ManagementService` is aware of the other
services and is used to orchestrate tests. Tests are organised in scenarios. In order to set a test
scenario, a POST or PUT request has to be sent to its `/config` endpoint, like:

.. code-block:: json

   {
      "active_scenario": "name of scenario"
   }

When the mitmproxy starts, the active scenario is `default`: since a scenario can be set only at
the beginning of a test, this is to ensure that all of the responses required for proper start-up
of INSPIRE are present.

The proxy also supports recording of new scenarios. Recording can be switched on and off via the
Management Service, by a POST or PUT request to its `/record` endpoint. E.g. to switch on the
recording (and respectively with `false` to switch it off):

.. code-block:: json

   {
      "enable": true
   }

See https://git.io/vhi3B for more endpoints of the Manager Service.


Whitelist Service
+++++++++++++++++

Whitelist service is designed to enable the user to specify hosts to which the traffic should always
be allowed to passed. Interactions with whitelisted services cannot be recorded or replayed.

By default whitelisted services are: ``test-indexer`` (ElasticSearch), ``test-scrapyd`` (scrapyd),
``test-web-e2e.local`` (web node). You can specify your own list using an environment variable
``MITM_PROXY_WHITELIST``, and listing the hostnames (no port number), white-space separated.
