import csv
import json

# A tool used to convert a csv of the segmentation map values into their colors

in_file_path = 'seg_map.csv'
out_file_path = 'seg_map.json'
data = {
    "origin": "https://docs.google.com/spreadsheets/d/1se8YEtb2detS7OuPE86fXGyD269pMycAWe2mtKUj2W8/edit#gid=0",
    "key": []
}
with open(in_file_path, 'r') as file:
    csv_file = csv.reader(file)
    for line_num, line in enumerate(csv_file):
        if line_num == 0:
            continue
        rgb_str_split = line[5].replace('(', '').replace(')', '').replace(' ', '').split(',')
        rgb_parsed = list(map(lambda x: int(x), rgb_str_split)) # convert "(120, 120, 120)" into [120, 120, 120]
        line_values = {
            'rgb': rgb_parsed,
            'hex': line[6],
            'desc': line[8].split(';')
        }
        data['key'].append(line_values)


with open(out_file_path, 'w') as file:
    file.write(json.dumps(data, indent=4))