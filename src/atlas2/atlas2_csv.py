import csv

'''
Export a PSU object as a csv file with the name set to the PSU ID + PSU Name 
'''
def export_psu_as_csv(psu, folder=""):
    return export_assets_as_csv(f'{psu.id}_{psu.name}.csv', psu.assets, folder)

'''
Exports a list of assets to a csv file with the passed name
If the asset list is empty, it will just print the header and no other rows, which is expected behavior
'''
def export_assets_as_csv(name: str, assets: list, folder=""):
    # Open and use CSV file with passed name
    with open(folder + name, 'w', newline='') as csvfile:
        # Define field (header) names manually (could do thsi automatically later if these change)
        fieldnames = ['ip', 'in_block', 'ping_status', 'asn', 'domains', 'source', 'timestamp', 'comments']
        assetwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header to file
        assetwriter.writeheader()
        # Write each asset as a row to the file
        for asset in assets:
            assetwriter.writerow(asset.__dict__)

    return 0 # Return normal exit code

