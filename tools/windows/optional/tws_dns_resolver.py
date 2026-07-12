#!/usr/bin/env python3
r"""
Optional Tiny Swarm World DNS resolver for tsw.local.

This is not the default bridge mechanism. Prefer the PowerShell bridge with
explicit Windows hosts-file entries.

Requirements on Windows:
  py -m pip install dnslib

Example:
  py .\tools\windows\optional\tws_dns_resolver.py --distro Debian --zone tsw.local --address 127.0.0.1 --port 53

Caveats:
  - Port 53 may require Administrator privileges.
  - Windows name resolution must be configured to query this resolver.
  - DNS uses UDP by default; netsh portproxy is TCP-only and is not suitable
    as a generic DNS UDP forwarder.
"""

import argparse
import subprocess
import time
from typing import Optional

from dnslib import A, QTYPE, RCODE, RR
from dnslib.server import BaseResolver, DNSServer


class TwsResolver(BaseResolver):
    def __init__(self, distro: str, zone: str, ttl: int, cache_seconds: int) -> None:
        self.distro = distro
        self.zone = zone.strip(".").lower() + "."
        self.ttl = ttl
        self.cache_seconds = cache_seconds
        self._cached_ip: Optional[str] = None
        self._cached_until = 0.0

    def resolve(self, request, handler):
        reply = request.reply()
        qname = str(request.q.qname).lower()
        qtype = QTYPE[request.q.qtype]

        if not qname.endswith(self.zone):
            reply.header.rcode = RCODE.NXDOMAIN
            return reply

        if qtype not in ("A", "ANY"):
            return reply

        wsl_ip = self.get_wsl_ip()
        reply.add_answer(RR(request.q.qname, QTYPE.A, rdata=A(wsl_ip), ttl=self.ttl))
        return reply

    def get_wsl_ip(self) -> str:
        now = time.time()
        if self._cached_ip and now < self._cached_until:
            return self._cached_ip

        if self.distro == "auto":
            cmd = ["wsl.exe", "hostname", "-I"]
        else:
            cmd = ["wsl.exe", "-d", self.distro, "-e", "hostname", "-I"]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=True)
        ip = result.stdout.split()[0]

        self._cached_ip = ip
        self._cached_until = now + self.cache_seconds
        return ip


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--distro", default="auto", help="WSL distro name, e.g. Debian or Ubuntu-24.04. Use auto for default distro.")
    parser.add_argument("--zone", default="tsw.local", help="DNS zone suffix.")
    parser.add_argument("--address", default="127.0.0.1", help="Address to bind.")
    parser.add_argument("--port", default=53, type=int, help="DNS port.")
    parser.add_argument("--ttl", default=60, type=int)
    parser.add_argument("--cache-seconds", default=10, type=int)
    args = parser.parse_args()

    resolver = TwsResolver(
        distro=args.distro,
        zone=args.zone,
        ttl=args.ttl,
        cache_seconds=args.cache_seconds,
    )

    server = DNSServer(resolver, address=args.address, port=args.port)
    server.start()


if __name__ == "__main__":
    main()
