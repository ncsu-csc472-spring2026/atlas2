import requests
import json


class RunZeroAPIError(Exception):
    """Custom exception for RunZero API errors."""
    pass


def add_assets_and_scan(
    org_token: str,
    site_name: str,
    ips: list[str],
    description: str,
    base_url: str = "https://console.runzero.com/api/v1.0/org",
    timeout: int = 30,
) -> dict:
    """
    Add one or more IPs as /32 subnets to a RunZero site and trigger a scan
    using the Hosted Explorer.

    Args:
        org_token (str): RunZero organization API token.
        site_name (str): Name of the site to create or update.
        ips (list[str]): List of IP addresses (e.g., ["1.2.3.4"]).
        description (str): Description to attach to new subnets.
        base_url (str): Base API URL (default: RunZero org API).
        timeout (int): Request timeout in seconds.

    Returns:
        dict: {
            "site_id": str,
            "added_subnets": list[str],
            "existing_subnets": list[str],
            "scan_id": str | None
        }

    Raises:
        RunZeroAPIError: If any API request fails.
    """

    headers = {
        "Authorization": f"Bearer {org_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    cidrs = [f"{ip}/32" for ip in ips]

    def _request(method, url, **kwargs):
        try:
            r = requests.request(method, url, headers=headers, timeout=timeout, **kwargs)
            r.raise_for_status()
            return r
        except requests.exceptions.HTTPError as e:
            raise RunZeroAPIError(f"HTTP error: {e} - {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise RunZeroAPIError(f"Request error: {e}")

    # ---- Get or create site ----
    sites = _request("GET", f"{base_url}/sites").json()
    matching = [s for s in sites if s.get("name") == site_name]

    if matching:
        site = matching[0]
    else:
        site = _request(
            "POST",
            f"{base_url}/sites",
            json={"name": site_name, "subnets": []},
        ).json()

    site_id = site["id"]

    # ---- Get site details ----
    site_data = _request("GET", f"{base_url}/sites/{site_id}").json()
    subnets_data = site_data.get("subnets", {})

    if isinstance(subnets_data, dict):
        existing_subnets = list(subnets_data.keys())
    elif isinstance(subnets_data, list):
        existing_subnets = subnets_data
    else:
        subnets_data = {}
        existing_subnets = []

    added_subnets = []

    # ---- Add new subnets ----
    for cidr in cidrs:
        if cidr not in existing_subnets:
            if isinstance(subnets_data, dict):
                subnets_data[cidr] = {"description": description}
            else:
                subnets_data.append(cidr)

            added_subnets.append(cidr)

    # ---- Update site if needed ----
    if added_subnets:
        _request(
            "PATCH",
            f"{base_url}/sites/{site_id}",
            json={"subnets": subnets_data, "name": site_name},
        )

    # ---- Trigger scan using Hosted Explorer ----
    scan_payload = {
        "hosted-zone-name": "auto",
        "targets": ",".join(cidrs),  # must be string
    }

    r = _request(
        "PUT",
        f"{base_url}/sites/{site_id}/scan",
        json=scan_payload,
    )

    scan_id = None
    try:
        scan_id = r.json().get("id")
    except json.JSONDecodeError:
        pass

    return {
        "site_id": site_id,
        "added_subnets": added_subnets,
        "existing_subnets": existing_subnets,
        "scan_id": scan_id,
    }
