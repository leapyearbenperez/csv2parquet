import unittest
import os
from collections import OrderedDict

import csv2parquet

THIS_DIR = os.path.dirname(__file__)
TEST_CSV = os.path.join(THIS_DIR, 'test-simple.csv')
TEST_CSV_MAP = os.path.join(THIS_DIR, 'test-header-mapping.csv')

class TestCsvSource(unittest.TestCase):
    def test_real_path_to_prevent_drill_script_errors(self):
        # Specifying a CSV file path of something like "../something.csv" will confuse Drill.
        # Prevent this by expanding the path.
        csv_src = csv2parquet.CsvSource('./test-simple.csv')
        self.assertEqual(csv_src.path, os.path.realpath(TEST_CSV))
    def test_headers_simple(self):
        csv_src = csv2parquet.CsvSource(TEST_CSV)
        expected_headers = [
            'Date',
            'Open',
            'High',
            'Low',
            'Close',
            'Volume',
            'ExDividend',
            'SplitRatio',
            'AdjOpen',
            'AdjHigh',
            'AdjLow',
            'AdjClose',
            'AdjVolume',
            ]
        self.assertEqual(expected_headers, csv_src.headers)
        # CSV and Parquet column names should be the same.
        expected_header_map = dict((header, header) for header in expected_headers)
        self.assertEqual(expected_header_map, csv_src.header_map)

    def test_headers_map(self):
        # verify that an exception is raised if we try to create it without mapping
        csv_src = csv2parquet.CsvSource(TEST_CSV_MAP)
        with self.assertRaises(csv2parquet.CsvSourceError):
            csv_src.header_map
        # now try again, with a mapping
        name_map = {
            'Adj. Open'   : 'Adj Open',
            'Adj. High'   : 'Adj High',
            'Adj. Low'    : 'Adj Low',
            'Adj. Close'  : 'Adj Close',
            'Adj. Volume' : 'Adj Volume',
            }
        csv_src = csv2parquet.CsvSource(TEST_CSV_MAP, name_map)
        expected_header_map = OrderedDict([
            ('Date', 'Date'),
            ('Open', 'Open'),
            ('High', 'High'),
            ('Low', 'Low'),
            ('Close', 'Close'),
            ('Volume', 'Volume'),
            ('Ex-Dividend', 'Ex-Dividend'),
            ('Split Ratio', 'Split Ratio'),
            ('Adj. Open', 'Adj Open'),
            ('Adj. High', 'Adj High'),
            ('Adj. Low', 'Adj Low'),
            ('Adj. Close', 'Adj Close'),
            ('Adj. Volume', 'Adj Volume'),
            ])
        self.assertEqual(expected_header_map, csv_src.header_map)

class TestDrillScript(unittest.TestCase):
    def test_build_script(self):
        # .strip() the actual scripts to ignore leading/trailing whitespace
        expected_script = '''
alter session set `store.format`='parquet';
CREATE TABLE dfs.tmp.`/path/to/parquet_output/` AS
SELECT
columns[0] as `Date`,
columns[1] as `Open`,
columns[2] as `High`,
columns[3] as `Low`,
columns[4] as `Close`,
columns[5] as `Volume`,
columns[6] as `Ex-Dividend`,
columns[7] as `Split Ratio`
FROM dfs.`/path/to/input.csv`
OFFSET 1
'''.strip()
        headers = [
            'Date',
            'Open',
            'High',
            'Low',
            'Close',
            'Volume',
            'Ex-Dividend',
            'Split Ratio',
            ]
        actual_script = csv2parquet.render_drill_script(headers, '/path/to/parquet_output/', '/path/to/input.csv').strip()
        self.assertEqual(expected_script, actual_script)
        
