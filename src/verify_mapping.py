import argparse
import csv
from collections import namedtuple
from fhir import FHIRClient

#
# Validate a list of code mappings using the FHIR terminology server
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


# Returns the preferred display value if the given code exists in the given code-system/version. Otherwise, return None.
def get_display(ts: FHIRClient, system, version, code):
    response = ts.code_system_validate_code(system, version, code)
    if response.get_boolean("result"):
        return response.get_string("display")
    else:
        return None


# Returns True if a mapping exists from code a in system a to code b in system b, False otherwise.
def mapping_exists(ts: FHIRClient, system_a, code_a, system_b, code_b):
    mappings = ts.concept_map_translate(None, system_a, code_a, system_b, True)
    result = mappings.get_boolean("result")
    if not result:
        return False  # No mappings found
    concepts = [match.get_coding('concept') for match in mappings.get_parts('match')]
    matches = [concept for concept in concepts if concept.get('system') == system_b and concept.get('code') == code_b]
    return len(matches) > 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--source-system', required=True)
    parser.add_argument('--source-version')
    parser.add_argument('--target-system', required=True)
    parser.add_argument('--target-version')
    parser.add_argument('input')
    parser.add_argument('output')
    args = parser.parse_args()

    with open(args.input, encoding='utf-8-sig') as csv_file, open(args.output, "w+") as output:
        reader = csv.reader(csv_file)
        writer = csv.writer(output, lineterminator='\n')
        writer.writerow(_HEADER_OUT)
        if next(reader) != _HEADER_IN:
            raise ValueError("Invalid header row")
        client = FHIRClient(args.url, False)
        for index, row in enumerate(reader):
            print("Processing row", index)
            record = Record._make(row)
            source_display = get_display(client, args.source_system, args.source_version, record.source_code)
            target_display = get_display(client, args.target_system, args.target_version, record.target_code)
            mapping_valid = mapping_exists(client, args.source_system, record.source_code, args.target_system,
                                           record.target_code)
            writer.writerow(
                [record.source_code, record.target_code, source_display, target_display, mapping_valid])


if __name__ == '__main__':
    main()
