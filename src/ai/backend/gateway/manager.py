import asyncio
import functools
import json
import logging
from typing import FrozenSet
import sqlalchemy as sa
import trafaret as t
from typing import (
    Any, Final,
    Iterable,
    Tuple,
)

from aiohttp import web
import aiohttp_cors
from aiojobs.aiohttp import atomic
from aiotools import aclosing

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common import validators as tx

from . import ManagerStatus
from .auth import superadmin_required
from .exceptions import InvalidAPIParameters, ServerFrozen, ServiceUnavailable
from .typing import CORSOptions, WebMiddleware
from .utils import check_api_params
from ..manager.models import kernels, KernelStatus


log = BraceStyleAdapter(logging.getLogger('ai.backend.gateway.manager'))


def server_status_required(allowed_status: FrozenSet[ManagerStatus]):

    def decorator(handler):

        @functools.wraps(handler)
        async def wrapped(request, *args, **kwargs):
            status = await request.app['config_server'].get_manager_status()
            if status not in allowed_status:
                if status == ManagerStatus.FROZEN:
                    raise ServerFrozen
                msg = f'Server is not in the required status: {allowed_status}'
                raise ServiceUnavailable(msg)
            return (await handler(request, *args, **kwargs))

        return wrapped

    return decorator


READ_ALLOWED: Final = frozenset({ManagerStatus.RUNNING, ManagerStatus.FROZEN})
ALL_ALLOWED: Final = frozenset({ManagerStatus.RUNNING})


class GQLMutationUnfrozenRequiredMiddleware:

    def resolve(self, next, root, info, **args):
        if info.operation.operation == 'mutation' and \
                info.context['manager_status'] == ManagerStatus.FROZEN:
            raise ServerFrozen
        return next(root, info, **args)


async def detect_status_update(app):
    try:
        async with aclosing(app['config_server'].watch_manager_status()) as agen:
            async for ev in agen:
                if ev.event == 'put':
                    app['config_server'].get_manager_status.cache_clear()
                    updated_status = await app['config_server'].get_manager_status()
                    log.debug('Process-{0} detected manager status update: {1}',
                              app['pidx'], updated_status)
    except asyncio.CancelledError:
        pass


@atomic
async def fetch_manager_status(request: web.Request) -> web.Response:
    log.info('MANAGER.FETCH_MANAGER_STATUS ()')
    try:
        status = await request.app['config_server'].get_manager_status()
        etcd_info = await request.app['config_server'].get_manager_nodes_info()
        configs = request.app['config']['manager']

        async with request.app['dbpool'].acquire() as conn, conn.begin():
            query = (sa.select([sa.func.count(kernels.c.id)])
                       .select_from(kernels)
                       .where((kernels.c.role == 'master') &
                              (kernels.c.status != KernelStatus.TERMINATED)))
            active_sessions_num = await conn.scalar(query)

            nodes = [
                {
                    'id': etcd_info[''],
                    'num_proc': configs['num-proc'],
                    'service_addr': str(configs['service-addr']),
                    'heartbeat_timeout': configs['heartbeat-timeout'],
                    'ssl_enabled': configs['ssl-enabled'],
                    'active_sessions': active_sessions_num,
                    'status': status.value,
                }
            ]
            return web.json_response({
                'nodes': nodes,
                'status': status.value,                  # legacy?
                'active_sessions': active_sessions_num,  # legacy?
            })
    except:
        log.exception('GET_MANAGER_STATUS: exception')
        raise


@atomic
@superadmin_required
@check_api_params(
    t.Dict({
        t.Key('status'): tx.Enum(ManagerStatus, use_name=True),
        t.Key('force_kill', default=False): t.ToBool,
    }))
async def update_manager_status(request: web.Request, params: Any) -> web.Response:
    log.info('MANAGER.UPDATE_MANAGER_STATUS (status:{}, force_kill:{})',
             params['status'], params['force_kill'])
    try:
        params = await request.json()
        status = params['status']
        force_kill = params['force_kill']
    except json.JSONDecodeError:
        raise InvalidAPIParameters(extra_msg='No request body!')
    except (AssertionError, ValueError) as e:
        raise InvalidAPIParameters(extra_msg=str(e.args[0]))

    if force_kill:
        await request.app['registry'].kill_all_sessions()
    await request.app['config_server'].update_manager_status(status)

    return web.Response(status=204)


async def init(app: web.Application) -> None:
    app['status_watch_task'] = asyncio.create_task(detect_status_update(app))


async def shutdown(app: web.Application) -> None:
    if app['status_watch_task'] is not None:
        app['status_watch_task'].cancel()
        await app['status_watch_task']


def create_app(default_cors_options: CORSOptions) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app['api_versions'] = (2, 3, 4)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    status_resource = cors.add(app.router.add_resource(r'/status'))
    cors.add(status_resource.add_route('GET', fetch_manager_status))
    cors.add(status_resource.add_route('PUT', update_manager_status))
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    return app, []
