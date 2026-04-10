import csv
import sys

OUTPUT_FILE = "master_psu_list.csv"

def main():
    csv_file = sys.argv[1]
    with open(csv_file, newline='') as csvfile:
        
        # PSU Number, PSU Name, Principal email, School domain email
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        new_list = []
        psu_ids = []
        for row in reader:
            new_row = []
            if len(row) == 4 and row[0] not in psu_ids:
                new_row.append(row[0].strip())
                psu_ids.append(row[0].strip())

                new_row.append(row[1].strip().replace(' ', '_'))
                new_row.append(row[2].split('@')[1].strip())
                new_row.append(row[3].strip())
                new_list.append(new_row)
                print((row[2].split('@'))[1])

        with open(OUTPUT_FILE, mode='w', newline='') as output_file:
            writer = csv.writer(output_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in new_list:
                writer.writerow(row)

if __name__=="__main__":
    main()
