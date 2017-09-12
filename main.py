#!/usr/bin/env python3

# TODO: fix socks proxies

import requests
from processor import Processor
from core.models import Proxy
import proxy_provider_server
from program_killer import ProgrammKiller

from django.conf import settings
import time
import os
from threading import Thread

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

proxies = []

killer = ProgrammKiller()


# thread which includes new collectors without restarting program
def collectorsUpdater():
    while not killer.kill:
        # include collectors on fly
        try:
            fromScriptVariables = {}
            exec(open(os.path.join(dirPath, 'collectors_list.py')).read(), fromScriptVariables)
            for CollectorType in fromScriptVariables['collectorTypes']:
                proxyProcessor.addCollectorOfType(CollectorType)
        except Exception as ex:
            print('some shit happened with file collectors_list.py: ' + repr(ex))
        except:
            print('some shit happened with file collectors_list.py')

        time.sleep(10)


if __name__ == "__main__":
    dirPath = os.path.dirname(os.path.realpath(__file__))
    killer = ProgrammKiller()

    proxyProcessor = Processor(100)

    proxy_provider_server.runServer(
        proxyProcessor,
        settings.PROXY_PROVIDER_SERVER['HOST'],
        settings.PROXY_PROVIDER_SERVER['PORT'])

    collectorsUpdaterThread = Thread(target=collectorsUpdater)
    collectorsUpdaterThread.start()


    while True:
        # print some information
        try:
            print('main thread: proxies count is' +
              str(Proxy.objects.count()))
            print('processor tasks count is ' +
                  str(proxyProcessor.tasks.qsize()))
        except Exception as ex:
            print('some shit happened: ' + repr(ex))
        except:
            print('some shit happened')

        if killer.kill:
            proxyProcessor.stop()
            break
        time.sleep(1)

    collectorsUpdaterThread.join()
    proxyProcessor.join()
    proxy_provider_server.stopServer()
    if proxy_provider_server.serverThread is not None:
        proxy_provider_server.serverThread.join()