import csv
import sys

OUTPUT_FILE = "master_psu_list.csv"

def main():
    csv_file = sys.argv[1]
    ip_blocks_file = sys.argv[2]
    with open(csv_file, newline='') as csvfile, open(ip_blocks_file, newline='') as blocksfile:

        # PSU Number, PSU Name, Principal email, URL School Address
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        block_reader = csv.reader(blocksfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        new_list = []
        psu_ids = []
        debug_count = 0
        for row in reader:
            new_row = []
            if len(row) == 4 and row[0] not in psu_ids:
                new_row.append(row[0].strip())
                psu_ids.append(row[0].strip())

                new_row.append(row[1].strip().replace(' ', '_'))
                new_row.append(row[2].split('@')[1].strip())
                new_row.append(row[3].strip())
                blocks = []

                for block_row in block_reader:
                    if new_row[0] in block_row[-2]:
                        debug_count += 1
                        blocks.append(block_row[-3])

                blocksfile.seek(0)
                new_row.append(blocks)
                new_list.append(new_row)

        for row in block_reader:
            psu = row[-2].split('_')[0]
            if psu not in psu_ids:
                print(psu)

        with open(OUTPUT_FILE, mode='w', newline='') as output_file:
            writer = csv.writer(output_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in new_list:
                writer.writerow(row)
                if not row[-1]:
                    print(row)

        print(debug_count)

if __name__=="__main__":
    main()
