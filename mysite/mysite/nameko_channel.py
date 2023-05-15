import eventlet

eventlet.monkey_patch(socket=True)  # noqa (code before rest of imports)

import errno
import threading
import uuid

from channels.layers import BaseChannelLayer
from nameko.standalone.rpc import ClusterRpcProxy
from nameko.standalone.events import event_dispatcher
from nameko.runners import ServiceRunner

from importlib import import_module


def _nameko_service_runner(event, config, predefined_services):
    service_runner = ServiceRunner(config=config)
    for service in predefined_services:
        module_path, class_name = service.rsplit(".", 1)
        module = import_module(module_path)
        service_runner.add_service(getattr(module, class_name))
    service_runner.start()
    runnlet = eventlet.spawn(service_runner.wait)
    print("Nameko is spawned")

    while True:
        try:
            with eventlet.timeout.Timeout(5, False):
                runnlet.wait()
            if event.is_set():
                print("Nameko is exiting..")
                service_runner.kill()
                break
            else:
                continue
        except OSError as exc:
            if exc.errno == errno.EINTR:
                # this is the OSError(4) caused by the signalhandler.
                # ignore and go back to waiting on the runner
                continue
            raise
        except KeyboardInterrupt:
            print()  # looks nicer with the ^C e.g. bash prints in the terminal
            try:
                service_runner.stop()
            except KeyboardInterrupt:
                print()  # as above
                service_runner.kill()
        else:
            # runner.wait completed
            break


class NamekoChannelLayer(BaseChannelLayer):
    name = "nameko_django_channel"

    def __init__(
            self,
            expiry=60,
            group_expiry=86400,
            capacity=100,
            channel_capacity=None,
            nameko_config=None,
            context={},
            predefined_services=None,
            **kwargs
    ):
        super().__init__(
            expiry=expiry,
            capacity=capacity,
            channel_capacity=channel_capacity,
            **kwargs
        )
        self.channels = {}
        self.groups = {}
        self.group_expiry = group_expiry
        self.nameko_config = nameko_config
        self.context = context
        self.predefined_services = predefined_services
        self._event = None
        self._runner = None
        self._run_nameko_run()

    def __del__(self):
        print("hasta la vista siempre")
        if getattr(self, '_event', None):
            self._event.set()
        if self._runner:
            self._runner.join()

    def _run_nameko_run(self):
        self._event = threading.Event()
        self._runner = threading.Thread(target=_nameko_service_runner, args=(
            self._event,
            self.nameko_config,
            self.predefined_services
        ))
        self._runner.start()

    def _get_context(self, user_id=None):
        return {
            **self.context,
            "correlation_id": uuid.uuid4().hex,
            **{"user_id": user_id if user_id else {}}
        }

    def rpc_call(self, user_id=None):
        context = self._get_context(user_id)
        return ClusterRpcProxy(self.nameko_config, context)

    def pub(self, pub_service_name, event_name, payload, extra_context={}):
        context = {
            **self._get_context(),
            **extra_context
        }
        pub = event_dispatcher(self.nameko_config, headers=context)
        return pub(pub_service_name, event_name, payload)

    """
    Mandatory channel methods below 
    """
    async def new_channel(self):
        return self.name

    async def receive(self, channel):
        return {'type': 'devnull'}
