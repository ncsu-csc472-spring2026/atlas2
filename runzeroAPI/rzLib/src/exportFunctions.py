import requests


class RunZeroAPIError(Exception):
    """Raised when the RunZero export operation fails."""
    pass


def export_assets_csv(
    org_token: str,
    output_file: str = "assets.csv",
    url: str = "https://console.runzero.com/api/v1.0/export/org/assets.csv",
    timeout: int = 60,
) -> str:
    """
    Export assets from the RunZero API as a CSV file.

    Parameters:
        org_token (str):
            REQUIRED. Your RunZero organization API token.
            This is used for authentication via a Bearer token.

        output_file (str):
            OPTIONAL. File path where the CSV will be saved.
            Defaults to "assets.csv" in the current working directory.

        url (str):
            OPTIONAL. RunZero API endpoint for exporting assets.
            Defaults to the standard organization assets export endpoint.

        timeout (int):
            OPTIONAL. Request timeout in seconds.
            Defaults to 60 seconds.

    Returns:
        str:
            The path to the saved CSV file (i.e., the value of `output_file`).

    Raises:
        RunZeroAPIError:
            - If the HTTP request fails (network issues, timeout, DNS, etc.)
            - If the API returns a non-200 status code
            - If writing the file to disk fails

    Example:
        export_assets_csv("my_token", "assets.csv")
    """

    # Prepare authorization header using Bearer token
    headers = {
        "Authorization": f"Bearer {org_token}"
    }

    # Perform HTTP GET request to RunZero API
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
    except requests.exceptions.RequestException as e:
        # Wrap lower-level request errors in a library-specific exception
        raise RunZeroAPIError(f"Request error: {e}") from e

    # Validate HTTP response status
    if response.status_code != 200:
        raise RunZeroAPIError(
            f"Request failed ({response.status_code}): {response.text}"
        )

    # Write CSV content to disk
    try:
        with open(output_file, "wb") as f:
            f.write(response.content)
    except OSError as e:
        # Handle filesystem-related errors (permissions, disk issues, etc.)
        raise RunZeroAPIError(f"File write error: {e}") from e

    # Return the path to the saved file for caller use
    return output_file
