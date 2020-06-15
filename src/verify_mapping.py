import argparse
import configparser
import csv
from collections import namedtuple
from fhir import FHIRClient

#
# Valid code mappings using the FHIR terminology server
# Input is a CSV file with source code, target code
# Output is a CSV file with source code, target code, source display, target display, mapping valid
#


_HEADER_IN = [
    "source_code",
    "target_code"
]

_HEADER_OUT = [
    "source_code",
    "target_code",
    "source_display",
    "target_display",
    "mapping_valid"
]

Record = namedtuple('Record', _HEADER_IN)


def get_display(ts: FHIRClient, system, version, code):
    response = ts.code_system_validate_code(system, version, code)
    if response.get_boolean("result"):
        return response.get_string("display")
    else:
        return None


def mapping_exists(ts: FHIRClient, url, system_a, code_a, system_b, code_b):
    mappings = ts.concept_map_translate(url, system_a, code_a, system_b, True)
    result = mappings.get_boolean("result")
    if not result:
        return False  # No mappings found
    concepts = [match.get_coding('concept') for match in mappings.get_parts('match')]
    matches = [concept for concept in concepts if concept.get('system') == system_b and concept.get('code') == code_b]
    return len(matches) > 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('input')
    parser.add_argument('output')
    args = parser.parse_args()

    with open(args.input, encoding='utf-8-sig') as csv_file, open(args.output, "w+") as output:
        reader = csv.reader(csv_file)
        writer = csv.writer(output, lineterminator='\n')
        writer.writerow(_HEADER_OUT)
        if next(reader) != _HEADER_IN:
            raise ValueError("Invalid header row")

        config = configparser.ConfigParser(allow_no_value=True)
        config.read(args.config)
        source_system = config['mapping']['source_system']
        source_version = config['mapping']['source_version']
        target_system = config['mapping']['target_system']
        target_version = config['mapping']['target_version']
        concept_map = config['mapping']['concept_map']
        client = FHIRClient(config['server']['url'], False)

        for index, row in enumerate(reader):
            print("Processing row", index)
            record = Record._make(row)
            source_display = get_display(client, source_system, source_version, record.source_code)
            target_display = get_display(client, target_system, target_version, record.target_code)
            mapping_valid = mapping_exists(client, concept_map, source_system, record.source_code, target_system,
                                           record.target_code)
            writer.writerow(
                [record.source_code, record.target_code, source_display, target_display, mapping_valid])


if __name__ == '__main__':
    main()
