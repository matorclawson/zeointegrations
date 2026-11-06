"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/ipinfo/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class IpInfoClient:
    BASE_URL = "https://ipinfo.io"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"content-type": "application/json"}

    def get_ip_info(self, ip_address: str | None = None) -> dict[str, Any]:
        """Get information about an IP address"""
        endpoint = f"{self.BASE_URL}/{ip_address}" if ip_address else self.BASE_URL
        params = {}
        response = self._http.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_bulk_info(self, ip_addresses: list[str]) -> dict[str, Any]:
        """Get information about multiple IP addresses"""
        endpoint = f"{self.BASE_URL}/batch"
        params = {}
        data = ip_addresses
        response = self._http.post(
            endpoint, headers=self.headers, params=params, json=data
        )
        response.raise_for_status()
        return response.json()

    def get_asn_info(self, asn: str) -> dict[str, Any]:
        """Get information about an ASN (Autonomous System Number)"""
        endpoint = f"{self.BASE_URL}/{asn}"
        params = {}
        response = self._http.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
