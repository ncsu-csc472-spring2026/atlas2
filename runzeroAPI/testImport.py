from importSRC import add_assets_to_site


def main():
    result = add_assets_to_site(
        site_name="site name",
        ips=[
            "45.33.32.156",
            "64.233.180.153"
        ],
        descriptions=[
            "nmap test site",
            "open range test site"
        ],
        create_if_missing=True
    )

    print("=== Import Result ===")
    print(f"Site ID: {result['site_id']}")
    print(f"Updated: {result['updated']}")
    print(f"Scan ID: {result['scan_id']}")
    print(f"Total IPs: {result['total_ips']}")


if __name__ == "__main__":
    main()
