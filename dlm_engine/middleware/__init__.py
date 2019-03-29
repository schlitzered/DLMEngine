from uuid import uuid4
import json
import logging

from aiohttp.web import middleware, json_response
import jsonschema
import pymongo.errors

from dlm_engine.errors import BaseError
from dlm_engine.errors import InvalidBody
from dlm_engine.errors import MongoConnError


@middleware
async def request_id(request, handler):
    _request_id = request.headers.get('X-Request-ID', None)
    if not _request_id:
        _request_id = str(uuid4())
        request['X-Request-ID'] = _request_id
    response = await handler(request)
    response.headers['X-Request-ID'] = _request_id
    return response


@middleware
async def error_catcher(request, handler):
    log = logging.getLogger('application')
    _request_id = request['X-Request-ID']
    try:
        try:
            log.debug("{0} entering module {1} function {2}".format(
                _request_id, handler.__module__, handler.__name__))
            return await handler(request)
        except (jsonschema.exceptions.ValidationError, json.decoder.JSONDecodeError) as err:
            log.error('{0} received invalid JSON body {1}'.format(_request_id, err))
            raise InvalidBody(err)
        except pymongo.errors.ConnectionFailure as err:
            log.error('{0} error communicating with MongoDB: {1}'.format(_request_id, err))
            raise MongoConnError(err)
        finally:
            log.debug("{0} leaving module {1} function {2}".format(
                _request_id, handler.__module__, handler.__name__)
            )
    except BaseError as err:
        return json_response(
            data=err.err_rsp,
            status=err.status
        )
