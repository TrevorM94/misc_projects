from pprint import pprint
import os
import csv
from configobj import ConfigObj
import logging
import collections
from datetime import datetime
import re

# PYTHON 3.6+ DICTS ARE NOW INSERTION ORDERED.
# LISTS ARE ALWAYS INSERTION ORDERED.
# TODO: Find out of the server this will be run on can run Python 3.6+. If not,
#       change the current dict functionality to OrderedDict. Preserving the order
#       of it is vital to this program working properly.

class DataCleaner:

    def __init__(self):
        # Config and log file initialization
        self.LOG_FILENAME = 'test_log.log'
        self.config = ConfigObj('test_config.ini')
        logging.basicConfig(filename=self.LOG_FILENAME, level=logging.DEBUG)

        # self.final_json = []
        self.final_json = {}
        self.auths = []
        self.macs = []
        self.test_log_matches = []
        self.tests = []
        self.barcode_regex = r'01(\d{14})11(\d{6})21(.*)'
        self.device_data_structure = None
        self.needed_test_locations = []

    # The purpose of this method is to first take a list of headers and the first row with a 
    # Sensor ID from a .tsv file. Then it will then pull the GTIN out of the Sensor ID and look
    # for a match within the config.ini file. If a match is found, it will then compare the passed
    # in list of headers from the .tsv file to the valid_test_names variable within the .ini file.
    # If they are equal, a good match is found and the program will continue.
    def check_headers(self, found_headers, sensor_id):
        if self.config.get(sensor_id[2:16]):
            device_info = self.config.get(sensor_id[2:16])
            if collections.Counter(found_headers) == collections.Counter(device_info['valid_test_names']):
                logging.info(f'Header match found for a {device_info["project_name"]} device. Proceeding.')
                self.device_data_structure = device_info['Structure'].dict()
                return True
        return False

    # The purpose of this method is to verify that the barcode (or Sensor ID) from the .tsv file is
    # in the proper format. It should look like: (01)GTIN(11)BUILDDATE(21)MAC. If the proper format 
    # is found, it will then begin pulling the barcode apart. The GTIN, Build Date, and MAC address
    # will be pulled out. It will use the GTIN to search the config.ini file for a match. If a match
    # is found, it will take the 'Structure' section from the match and store it to an instance var.
    # Logging will be completed through every step. It will also confirm that the BUILDDATE is in a
    # proper format.
    # TODO: Remove GTIN, not needed.
    def check_barcode_format(self, barcode):
        match = re.search(self.barcode_regex, barcode)
        if match:
            gtin = match.group(1)
            self.device_data_structure = self.config.get(match.group(1), None)
            mac = match.group(3)
            if self.device_data_structure is not None:
                self.device_data_structure = self.device_data_structure['Structure'].dict()
                try:
                    build_date = datetime.strptime(match.group(2), '%y%m%d')
                    return gtin, build_date, mac
                except ValueError:
                    logging.error(f'Wrong date format found in the barcode {barcode}. Expected YYMMDD, {match.group(2)} was found. Please check the date format.')
            else:
                logging.error(f'The GTIN {match.group(1)} within the barcode {barcode} was not able to be matched to a device.')
        else:
            logging.error(f'The barcode {barcode} is not in the required format. Should be (01)GTIN(11)BUILDDATE(21)MAC.')

    # The purpose of this function is to open the .tsv file and begin parcing. It will first pull out 
    # the headers and put every other line into a list seperated by tabs. After checking that the headers
    # are a match, it will begin iterating over the list-version of every row. While iterating, it will 
    # begin building the final JSON structure. Comments will be added within the function to go more
    # in depth.
    def process_file(self, filename):
        with open(filename, 'r') as tsvin:
            headers = next(tsvin).strip().split('\t')
            tsv_no_blanks = [line.strip().split('\t') for line in tsvin if len(line.strip().split('\t')) > 1]
            current_test_results = {}
            test_dict = {}

            if self.check_headers(headers, tsv_no_blanks[0][0]):
                for i in range(0, (len(tsv_no_blanks) - 1)):

                    # Check the current row's barcode/Sensor ID is proper.
                    barcode_status = self.check_barcode_format(tsv_no_blanks[i][0])
                    if barcode_status is not None:
                        test_mac = self.mac_processing(barcode_status[2], '-')
                        
                        # Comparing the current row's Sensor ID to the next row's Sensor ID. Because of the 
                        # way that the .tsvs are structured, the last occurance of a Sensor ID in the file
                        # will be the row that should be used to build the 'main' JSON structure that will 
                        # be uploaded to DynamoDB.
                        if tsv_no_blanks[i][0] != tsv_no_blanks[i+1][0]:
                            self.final_json[test_mac] = self.build_json_values(self.device_data_structure, barcode_status[1], barcode_status[2], tsv_no_blanks[i])
                            # self.final_json.append(self.build_json_values(self.device_data_structure, barcode_status[1], barcode_status[2], tsv_no_blanks[i]))

                        # The ICT/FT test results are stored in a list of dictionaries in the final JSON
                        # structure. This begins building that list of dictionaries. The key in every
                        # dict will be the sensor ID. It will use a method called 'build_test()' that will
                        # take the current row's information and build the value for every key.
                        if test_mac not in current_test_results.keys():
                            current_test_results[test_mac] = [self.build_test(tsv_no_blanks[i])]
                        # If the sensor ID is already a key, insert the newly constructed value to the first 
                        # position in the list of dicts. This is done this way because of the current data
                        # structure within DynamoDB. If there are multiple rows within the .tsv with the same 
                        # Sensor ID, the last occurance of it will be the most recent test done. The data from
                        # Dynamo is from most recent down.
                        else:
                            current_test_results[test_mac].insert(0, self.build_test(tsv_no_blanks[i]))

                        self.macs.append(self.mac_processing(barcode_status[2], '-'))

                # This section is to analyze the last row in the .tsv, since I iterate through the length of it
                # -1 to avoid getting a KeyError.
                last_row_bc_status = self.check_barcode_format(tsv_no_blanks[-1][0])
                last_row_mac = self.mac_processing(last_row_bc_status[2], '-')
                self.macs.append(self.mac_processing(last_row_bc_status[2], '-'))

                if last_row_mac not in current_test_results.keys():
                    current_test_results[last_row_mac] = [self.build_test(tsv_no_blanks[-1])]
                else:
                    current_test_results[last_row_mac].insert(0, self.build_test(tsv_no_blanks[-1]))

                # The list of dicts for FT/ICT tests.
                self.tests.append(current_test_results)

                # The final JSON data structure for Dynamo.
                self.final_json[last_row_mac] = self.build_json_values(self.device_data_structure, last_row_bc_status[1], last_row_bc_status[2], tsv_no_blanks[-1])
                # self.final_json.append(self.build_json_values(self.device_data_structure, last_row_bc_status[1], last_row_bc_status[2], tsv_no_blanks[-1]))
                
                # self.add_tests_to_json()
                result = {}
                for key in (current_test_results.keys() | self.final_json.keys()):
                    if key in current_test_results: result.setdefault(key, []).append(current_test_results[key])
                    if key in test_dict: result.setdefault(key, []).append(test_dict[key])
            else:
                logging.error(f'The headers within the TSV file do not match any known device.')

    # The purpose of this function is to take in the unseperated MAC address and split it however
    # the seperator states. ie: F8FE5C4C002A to F8:FE:5C:4C:00:2A
    def mac_processing(self, row, separator):
        return separator.join(row[i:i+2] for i in range(0, len(row), 2))

    # The purpose of this function is to find test logs with matching MAC addresses (F8FE5C4C002A to F8-FE-5C-4C-00-2A-somedate.log)
    # by iterating through the self test logs and the pre-filled MAC list. Because a more than one log can be listed for one device
    # with an Auth Key and different times, it will build a dict with the mac address as a key, and the value will be the the most
    # recent test log entry.
    def find_self_test_logs(self):

        # This reduces the amount of files that need to be looped through. Because I am only looking for
        # the Auth Key from every matching test log, I can filter out every file that does not start with
        # F8-FE-5C.
        relevant_logs = list(filter(lambda x: x.startswith('F8-FE-5C'), os.listdir('selfTestLogs')))

        test_log_matches = {}
        for mac in self.macs:
            for log in relevant_logs:
                if mac in log:
                    test_log_matches[mac] = log

        return list(test_log_matches.values())

    # The purpose of this function is to loop through the pre-matched logs and pull the auth keys
    # from them.
    def get_auths_from_logs(self):
        unique_logs = self.find_self_test_logs()
        for log in unique_logs:
            # This part was put into its own function to allow me to break out of the first loop
            # when an auth key is found.
            self.find_auth_move_to_next(log)
            
        # self.add_auths_and_tests_to_json()

    # The purpose of this function is to have a singular test log passed in, open that log,
    # loop through from the bottom of the file up. (in case there is more than one Auth Key
    # in the file. The bottom one is the one that I want to pull out.) If it finds the line
    # where an Auth Key is assigned, it will pull the auth key out and add it to a list. 
    # If an auth key is not found it will just put 'N/A' into that spot's position in the
    # auth key list. 
    def find_auth_move_to_next(self, test_log):
        with open(f'selfTestLogs/{test_log}', 'r', encoding='latin1') as f:
            lines = f.readlines()
            # From the bottom of the file up
            for line in reversed(lines):
                auth_found = False
                if line.startswith('Auth Key is:'):
                    self.auths.append(line[12:-1])
                    auth_found = True
                    return
            if not auth_found:
                self.auths.append('N/A')

    # The purpose of this function is to build each .tsv row's ICT/FT data structure that will
    # be added to the final JSON structure. It uses Test2 values from the config.ini file to know
    # where to look in the current .tsv row's list form.
    def build_test(self, tsv_row):
        completed_tsv_entry_tests = {}
        completed_tsv_entry_tests['Description'] = f'Site {tsv_row[self.needed_test_locations[1]]}, Description: {tsv_row[self.needed_test_locations[2]]}'
        completed_tsv_entry_tests['Status'] = 'PassAssembly' if tsv_row[self.needed_test_locations[-1]] == 'PASS' else 'FailAssembly'
        completed_tsv_entry_tests['TestTime'] = tsv_row[self.needed_test_locations[0]]
        return completed_tsv_entry_tests

    # The purpose of this function is to construct the main data structure that is expected in
    # DynamoDB. This function will be called for every row in the file, getting passed in the
    # 'Structure' section within the config.ini file, which will hold where each position is 
    # within the current .tsv row. (ie Limulus' barcode is in the first column, so the BarCode section
    # in the 'Structure' part of the .ini file will say: "BarCode: 0")
    def build_json_values(self, bc_dict, build_date, mac, tsv_row):
        data_dict = {}
        for k, v in bc_dict.items():
            if not isinstance(v, list):
                if v.isnumeric() and int(v) in range(len(tsv_row)):
                    # This row is passed on whether or not FT passed. 
                    if k == 'Status': data_dict['Status'] = 'PassAssembly' if tsv_row[int(v)] == 'PASS' else 'FailAssembly'
                    data_dict[k] = tsv_row[int(v)]
                if not v.isnumeric():
                    # Converts the passed in 'build_date' to the date format that is present in the 
                    # DynamoDB data structure. 
                    if k == 'BuildDate': data_dict[k] = build_date.strftime('%Y-%m-%dT%H:%M:%S')
                    # These three entries are always zero in the data structure.
                    if k in ['InventoryCurrent', 'RSSI', 'Site']: data_dict[k] = '0'
                    # These two fields are the same. TODO: Find out of they are different ever
                    if k in ['mac', 'serial']: data_dict[k] = mac
                    # These two are already placed within the specific device's section in the .ini file.
                    if k in ['DUT_NAME', 'OwnerTable']: data_dict[k] = v
            else:
                # TestTime ALWAYS spot 0
                # Site ALWAYS spot 1
                # Description ALWAYS spot 2
                # Status ALWAYS last spot
                self.needed_test_locations = list(map(int, v))
        return data_dict

    # The purpose of this function is to add both ICT/FT data structure and auth key to
    # each final_json value. They are insertion ordered from creation so they will be in line.
    def add_auths_and_tests_to_json(self):
        for i in range(0, len(self.final_json)):
            self.final_json[i]['AuthKey'] = self.auths[i]
            for k, v in self.tests[0].items():
                if self.final_json[i]['BarCode'] == k:
                    self.final_json[i]['Test2'] = v

    def decrypt_auths(self):
        pass

dc = DataCleaner()
dc.process_file('tsvs/2018-E_20191217_trunc.tsv')
dc.get_auths_from_logs()