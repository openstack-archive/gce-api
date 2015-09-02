# Copyright 2014
# The Cloudscaling Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from gceapi.api import utils
from gceapi.tests.unit import test


class FieldsTest(test.TestCase):
    """Test for parsing fields params."""

    def setUp(self):
        """Run before each test."""
        super(FieldsTest, self).setUp()

    def test_apply_template(self):
        fields1 = 'one,two,three(smth,else/one)'
        fields2 = 'one/smth,five/smth'
        wrongfields1 = 'zero,one/smth'
        wrongfields2 = 'fgdfds)9342'
        dct = {'one': {'smth': 1,
                       'else': 0},
               'two': 2,
               'three': [{'smth': 3,
                          'another': 'string',
                          'else': {'one': 1}}],
               'four': 4,
               'five': {'smth': 5}
              }

        expected1 = {'one': {'smth': 1,
                             'else': 0},
                     'two': 2,
                     'three': [{'smth': 3,
                                'else': {'one': 1}}]
                    }

        expected2 = {'one': {'smth': 1},
                     'five': {'smth': 5}
                    }

        res1 = utils.apply_template(fields1, dct)
        res2 = utils.apply_template(fields2, dct)
        self.assertEqual(res1, expected1)
        self.assertEqual(res2, expected2)

        self.assertRaises(ValueError, utils.apply_template, wrongfields1, dct)
        self.assertRaises(ValueError, utils.apply_template, wrongfields2, dct)

    def test_split_by_comma(self):
        string = 'bla,bla,smth/else,another(bla,bla/bla),yet/bla'
        expected = ['bla', 'bla', 'smth/else', 'another(bla,bla/bla)',
                    'yet/bla']
        res = utils.split_by_comma(string)
        self.assertEqual(res, expected)
