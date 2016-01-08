#!/usr/bin/env python
"""
 * cros project                                              https://wolflinux.org/s/4jRm3
 * (c) 2016 Py64 <py64.wolflinux@gmail.com>                  https://wolflinux.org/s/mmdoe
 *
 * This software is distributed on CPL license.
 * https://github.com/ProjectCros/CPL
"""
import sys
if sys.version_info <= (3,0):
    print("cros has been written only for Python 3 and tested on Python 3.5.1.")
    sys.exit(4)
import re, os
from lib import IfNoneUseDefault as inud
from lib import Configuration, Arguments, Out, crosinfo, Gzip, RequestHandlers, Servers, SSL
import threading
if os.name == "nt": print("Running on Windows. SPDY may be not available.")
else: import spdylay

# Load configuration
configpath = inud.get(Arguments.get(re.compile("--config|-c")), "RunFile", True)
config = Configuration.Configuration(configpath)
servers = config.Servers

# Show message with version.
Out.log(config.MainLog, "cros " + crosinfo.Version, True)

# Check for root.
try:
    if os.geteuid() == 0 and crosinfo.Insecure == False or Arguments.get(re.compile("--config|-c"), True) == False:
        Out.log(config.MainLog, " [err] cros cannot be executed by root for security reasons.", True, True)
except AttributeError: None

# Start servers. Get ports & addresses. Listen to them.
httpservers = []
threads = []
try:
    for server in servers:
        httpserver = None
        if server.SPDY['Enable']:
            httpserver = Servers.ThreadedSPDYServer((server.Address, server.Port),
                                                    RequestHandlers.SPDY,
                                                    server,
                                                    cert_file=server.SSL['Certificate'],
                                                    key_file=server.SSL['PrivateKey'])
        else:
            httpserver = Servers.ThreadedTCPServer(server, (server.Address, server.Port), RequestHandlers.HTTP)
            if server.SSL['Enable']:
                httpserver.socket = SSL.new_socket(httpserver.socket, crt=server.SSL['Certificate'], key=server.SSL['PrivateKey'],
                                                        ca=inud.get_d(server.SSL, 'CA', None), ciphers=inud.get_d(server.SSL, 'Ciphers', SSL.DefaultCiphers))
        httpservers.append(httpserver)
        Out.log(config.MainLog, " [inf] Serving " + server.Address + " on port " + str(server.Port) + ".", True)
        if server.SPDY['Enable']:
            server_thread = threading.Thread(target=httpserver.start())
        else: server_thread = threading.Thread(target=httpserver.serve_forever())
        server_thread.daemon = True
        server_thread.start()
        threads.append(server_thread)
except KeyboardInterrupt:
    print("Interrupted by keyboard.")
