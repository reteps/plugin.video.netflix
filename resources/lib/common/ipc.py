# -*- coding: utf-8 -*-
"""
    Copyright (C) 2017 Sebastian Golasch (plugin.video.netflix)
    Copyright (C) 2018 Caphm (original implementation module)
    Helper functions for inter-process communication via AddonSignals

    SPDX-License-Identifier: MIT
    See LICENSES/MIT.md for more information.
"""
import pickle
from base64 import b64encode, b64decode

from resources.lib.common import exceptions
from resources.lib.globals import G
from resources.lib.utils.logging import LOG, measure_exec_time_decorator
from .misc_utils import run_threaded

def make_call(*args, **kwargs):
    print('make_call')

def register_slot(*args, **kwargs):
    print('register_slot')
IPC_TIMEOUT_SECS = 20

# IPC over HTTP endpoints
IPC_ENDPOINT_CACHE = '/netflix_service/cache'
IPC_ENDPOINT_MSL = '/netflix_service/msl'
IPC_ENDPOINT_NFSESSION = '/netflix_service/nfsession'
IPC_ENDPOINT_NFSESSION_TEST = '/netflix_service/nfsessiontest'


class Signals:  # pylint: disable=no-init,too-few-public-methods
    """Signal names for use with AddonSignals"""
    PLAYBACK_INITIATED = 'playback_initiated'
    REQUEST_KODI_LIBRARY_UPDATE = 'request_kodi_library_update'
    SWITCH_EVENTS_HANDLER = 'switch_events_handler'



def make_http_call(endpoint, func_name, data=None):
    """
    Make an IPC call via HTTP and wait for it to return.
    The contents of data will be expanded to kwargs and passed into the target function.
    """
    from urllib.request import build_opener, install_opener, ProxyHandler, urlopen
    from urllib.error import URLError
    # Note: Using 'localhost' as address slowdown the call (Windows OS is affected) not sure if it is an urllib issue
    url = f'http://127.0.0.1:{G.LOCAL_DB.get_value("nf_server_service_port")}{endpoint}/{func_name}'
    LOG.debug('Handling HTTP IPC call to {}', url)
    install_opener(build_opener(ProxyHandler({})))  # don't use proxy for localhost
    try:
        with urlopen(url=url,
                     data=pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL),
                     timeout=IPC_TIMEOUT_SECS) as f:
            received_data = f.read()
            if received_data:
                _data = pickle.loads(received_data)
                if isinstance(_data, Exception):
                    raise _data
                return _data
        return None
    # except HTTPError as exc:
    #     raise exc
    except URLError as exc:
        err_msg = str(exc)
        if '10049' in err_msg:
            err_msg += '\r\nPossible cause is wrong localhost settings in your operative system.'
        LOG.error(err_msg)
        raise exceptions.BackendNotReady(err_msg) from exc


class EnvelopeAddonSignalsCallback:
    """
    Handle an AddonSignals function callback,
    allow to use funcs with multiple args/kwargs,
    allow an automatic AddonSignals.returnCall callback,
    can handle catching and forwarding of exceptions
    """
    def __init__(self, func):
        self._func = func

    def call(self, data):
        """In memory reference for the target func"""
        try:
            _data = pickle.loads(b64decode(data))
            _call(self._func, _data)
        except Exception:  # pylint: disable=broad-except
            import traceback
            LOG.error(traceback.format_exc())


def _call(func, data):
    if isinstance(data, dict):
        return func(**data)
    if data is not None:
        return func(data)
    return func()
