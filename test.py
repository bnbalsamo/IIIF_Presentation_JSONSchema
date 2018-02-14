import argparse
import json
from sys import exit
from os import scandir
from os.path import join

import jsonschema


SCHEMAS_ROOT = "."
SCHEMA_FILE_NAME_PREFIX = "IIIF_Presentation_Records_"
TEST_RECORDS_ROOT = "./test_records/"


class TestRecord:
    def __init__(self, version, fp, expected_result):
        self.version = version
        self.fp = fp
        self.expected_result = expected_result
        with open(fp) as f:
            self.doc = json.load(f)

    def validate_against(self, schema):
        try:
            jsonschema.validate(self.doc, schema)
            return True
        except jsonschema.exceptions.ValidationError:
            return False


def main(args):
    schema_files = []
    for x in scandir(args.schemas_root):
        if x.name.startswith(args.schema_file_name_prefix):
            schema_files.append(x.path)

    test_records = []
    for vdir in scandir(args.test_records_root):
        v = vdir.name
        for x in scandir(join(vdir.path, 'positive')):
            if not x.name.endswith(".json"):
                continue
            test_records.append(
                TestRecord(v, x.path, True)
            )
        for x in scandir(join(vdir.path, 'negative')):
            if not x.name.endswith(".json"):
                continue
            test_records.append(
                TestRecord(v, x.path, False)
            )

    results = {}
    results['failure'] = []
    results['success'] = []
    for sf in schema_files:
        v = sf.split("_")[-1][:-len(".json")]
        with open(sf) as f:
            schema = json.load(f)
        relevant_test_records = [x for x in test_records if x.version == v or \
                                 x.version == 'all']
        for tr in relevant_test_records:
            if not tr.validate_against(schema) == tr.expected_result:
                results['failure'].append((sf, tr))
            else:
                results['success'].append((sf, tr))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--schemas-root",
        type=str, default=SCHEMAS_ROOT
    )
    parser.add_argument(
        "--schema-file-name-prefix",
        type=str, default=SCHEMA_FILE_NAME_PREFIX
    )
    parser.add_argument(
        "--test-records-root",
        type=str, default=TEST_RECORDS_ROOT
    )
    parser.add_argument(
        "--print-success",
        action='store_true', default=False
    )
    parser.add_argument(
        "--print-failure",
        action='store_true', default=True
    )
    parser.add_argument(
        "--print-totals",
        action='store_true', default=True
    )
    args = parser.parse_args()
    r = main(args)
    if args.print_failure:
        for x in r['failure']:
            print(
                "FAIL: {} - {} - Expected Result {}".format(
                    x[0], x[1].fp, str(x[1].expected_result)
                )
            )
    if args.print_success:
        for x in r['success']:
            print(
                "SUCCESS: {} - {} - Expected Result {}".format(
                    x[0], x[1].fp, str(x[1].expected_result)
                )
            )
    if args.print_totals:
        print(
            "Successes: {}\nFailures: {}".format(
                str(len(r['success'])), str(len(r['failure']))
            )
        )
    if r['failure']:
        exit(1)
    exit(0)
