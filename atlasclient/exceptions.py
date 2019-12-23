#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Defines all the exceptions used to represent various error responses.

Adapted from python-novaclient with some changes.  Original source:

https://github.com/openstack/python-novaclient/blob/master/novaclient/exceptions.py
"""
import logging

LOG = logging.getLogger('pyatlasclient')


class ClientError(Exception):
    """
    The base exception class for all exceptions this library raises.
    """
    message = 'Unknown Error'

    def __init__(self, message=None):
        self.message = message or self.__class__.message
        super(ClientError, self).__init__()

    def __str__(self):
        exception_message = "Unexpected client-side error: %s" % self.message
        LOG.error(exception_message)
        return exception_message


class Timeout(Exception):
    """
    An exception indicating a timeout on a long-running operation.
    """
    message = 'Operation timeout exceeded'

    def __init__(self, timeout, message=None):
        self.timeout = timeout
        self.message = message or self.__class__.message
        super(Timeout, self).__init__()

    def __str__(self):
        exception_message = "Timed out after %s seconds: %s" % (self.timeout, self.message)
        LOG.error(exception_message)
        return exception_message


class Failed(Exception):
    """
    An exception indicating that a long-running operation failed to complete successfully.
    """
    message = 'Operation failed to complete'

    def __init__(self, model, message=None):
        self.model = model
        self.message = message or self.__class__.message
        super(Failed, self).__init__()

    def __str__(self):
        exception_message = "Failure detected for %s/%s: %s" % (self.model.__class__.__name__,
                                                                self.model.identifier,
                                                                self.message)
        LOG.error(exception_message)
        return exception_message


class HttpError(Exception):
    """
    The base exception class for all exceptions generated by HTTP responses.
    """
    message = 'Unknown Error'
    code = 500

    def __init__(self, code=None, message=None, details=None, url=None, method=None,
                 retry_after=None):
        self.code = code or self.__class__.code
        self.message = message or self.__class__.message
        self.details = details
        self.url = url
        self.method = method
        self.retry_after = retry_after
        super(HttpError, self).__init__()

    def __str__(self):
        params = (self.method, self.url, self.message, self.code, self.details)
        exception_message = "HTTP request failed for %s %s: %s %s: %s" % params
        LOG.error(exception_message)
        return exception_message


class BadRequest(HttpError):
    """
    HTTP 400 - Bad request: you sent some malformed data.
    """
    code = 400
    message = "Bad request"


class Unauthorized(HttpError):
    """
    HTTP 401 - Unauthorized: bad credentials.
    """
    code = 401
    message = "Unauthorized"


class Forbidden(HttpError):
    """
    HTTP 403 - Forbidden: your credentials don't give you access to this
    resource.
    """
    code = 403
    message = "Forbidden"


class NotFound(HttpError):
    """
    HTTP 404 - Not found
    """
    code = 404
    message = "Not found"


class MethodNotAllowed(HttpError):
    """
    HTTP 405 - Method Not Allowed: the method is valid but unsupported by this URL.
    """
    code = 405
    message = "Method Not Allowed"


class Conflict(HttpError):
    """
    HTTP 409 - Conflict: usually indicates that the resource changed underneath you.
    """
    code = 409
    message = "Conflict"


class RateLimitExceeded(HttpError):
    """
    HTTP 429 - Rate limit: you've sent too many requests for this time period.
    """
    code = 429
    message = "Rate limit"


class ServerError(HttpError):
    """
    HTTP 500 - Internal Server Error: the server had an unrecoverable error.
    """
    code = 500
    message = "Internal Server Error"


# NotImplemented is a python keyword.
class MethodNotImplemented(HttpError):
    """
    HTTP 501 - Not Implemented: the server does not support this operation.
    """
    code = 501
    message = "Not Implemented"


class ServerUnavailable(HttpError):
    """
    HTTP 503 - Service Unavailable: the server is not currently available.

    This can be used to indicate a server in a maintenance state, for example.
    """
    code = 503
    message = "Service Unavailable"


# pylint: disable=no-member
_status_to_exception_type = dict((c.code, c) for c in HttpError.__subclasses__())


def handle_response(response):
    """
    Given a requests.Response object, throw the appropriate exception, if applicable.
    """

    # ignore valid responses
    if response.status_code < 400:
        return

    cls = _status_to_exception_type.get(response.status_code, HttpError)

    kwargs = {
        'code': response.status_code,
        'method': response.request.method,
        'url': response.request.url,
        'details': response.text,
    }

    if response.headers and 'retry-after' in response.headers:
        kwargs['retry_after'] = response.headers.get('retry-after')

    raise cls(**kwargs)
