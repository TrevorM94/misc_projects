from configobj import ConfigObj
import csv
import collections
import logging
from datetime import datetime
from pprint import pprint
import re

LOG_FILENAME = 'test_log.log'
config = ConfigObj('test_config.ini')
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

def check_barcode(barcode):
    match = re.search(r'01(\d{14})11(\d{6})21(.*)', barcode)
    if match:
        gtin = match.group(1)
        device_data_structure = config.get(match.group(1), None)
        mac = match.group(3)
        if device_data_structure is not None:
            device_data_structure = device_data_structure['Structure'].dict()
            try:
                build_date = datetime.strptime(match.group(2), '%y%m%d')
                return gtin, device_data_structure, build_date, mac
            except ValueError:
                logging.error(f'Wrong date format found in the barcode {barcode}. Expected YYMMDD, {match.group(2)} was found. Please check the date format.')
        else:
            logging.error(f'The GTIN {match.group(1)} within the barcode {barcode} was not able to be matched to a device.')
    else:
        logging.error(f'The barcode {barcode} is not in the required format. Should be (01)GTIN(11)BUILDDATE(21)MAC.')

def check_headers(found_headers, sensor_id):
    if config.get(sensor_id[2:16]):
        device_info = config.get(sensor_id[2:16])
        if collections.Counter(found_headers) == collections.Counter(device_info['valid_test_names']):
            logging.info(f'Header match found for a {device_info["project_name"]} device found. Proceeding.')
            return True
    return False

with open('enter_file_here.tsv', 'r', newline='') as tsvin:
    headers = next(tsvin).strip().split('\t')
    tsv_no_blanks = [line.strip().split('\t') for line in tsvin if len(line.strip().split('\t')) > 1]
    if check_headers(headers, tsv_no_blanks[0][0]):
        if len(tsv_no_blanks) > 1:
            for i in range(0, (len(tsv_no_blanks[0])-1)):
                barcode_status = check_barcode(tsv_no_blanks[i][0])
                data_dict = {}
                dict_holder = []
                if barcode_status is not None:
                    for k, v in barcode_status[1].items():
                        if v.isnumeric() and int(v) in range(len(tsv_no_blanks[i])):
                            data_dict[k] = tsv_no_blanks[i][int(v)]
                        if not v.isnumeric():
                            if k == 'BuildDate': data_dict[k] = barcode_status[2].strftime('%Y-%m-%dT%H:%M:%S')
                            if k in ['InventoryCurrent', 'RSSI', 'Site']: data_dict[k] = '0'
                            if k == 'Status': data_dict['Status'] = 'PassAssembly' if tsv_no_blanks[i][-1] == 'PASS' else 'FailAssembly'
                            if k in ['mac', 'serial']: data_dict[k] = barcode_status[3]
                            if k in ['DUT_NAME', 'OwnerTable']: data_dict[k] = v
                    dict_holder.append(data_dict)
                else:
                    continue
        else:
            barcode_status = check_barcode(tsv_no_blanks[0][0])
            data_dict = {}
            dict_holder = []
            if barcode_status is not None:
                for k, v in barcode_status[1].items():
                    if v.isnumeric() and int(v) in range(len(tsv_no_blanks[0])):
                        data_dict[k] = tsv_no_blanks[i][int(v)]
                    if not v.isnumeric():
                        if k == 'BuildDate': data_dict[k] = barcode_status[2].strftime('%Y-%m-%dT%H:%M:%S')
                        if k in ['InventoryCurrent', 'RSSI', 'Site']: data_dict[k] = '0'
                        if k == 'Status': data_dict['Status'] = 'PassAssembly' if tsv_no_blanks[0][-1] == 'PASS' else 'FailAssembly'
                        if k in ['mac', 'serial']: data_dict[k] = barcode_status[3]
                        if k in ['DUT_NAME', 'OwnerTable']: data_dict[k] = v
                dict_holder.append(data_dict)
                pprint(dict_holder)
    else:  
        logging.error(f'The headers within the TSV file do not match any known device.')