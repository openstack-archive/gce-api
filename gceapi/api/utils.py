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

"""Utilities and helper functions."""


def _parse_slash(string):
    res = ''
    sp = string.split('/')
    for element in reversed(sp):
        res = {element: res}
    return res


def split_by_comma(string):
    between = 0
    last_split = 0
    sp = []

    i = 0
    while i < len(string):
        if string[i] == '(':
            between += 1
        elif string[i] == ')':
            between -= 1
        elif string[i] == ',' and not between:
            sp.append(string[last_split:i])
            last_split = i + 1
        i += 1
    sp.append(string[last_split:])
    return sp


def _parse_template(string):
    sp = split_by_comma(string)

    i = 0
    while i < len(sp):
        if '(' in sp[i]:
            sp[i] = sp[i].replace('(', ' ').replace(')', ' ').split()
        i += 1

    json = {}
    i = 0
    while i < len(sp):
        if isinstance(sp[i], list):
            fields = sp[i][1].split(',')
            json[sp[i][0]] = [{}]
            for field in fields:
                dct = _parse_slash(field)
                key = dct.keys()[0]
                json[sp[i][0]][0][key] = dct[key]
        else:
            field = _parse_slash(sp[i])
            key = field.keys()[0]
            json[key] = field[key]
        i += 1

    return json


def apply_template(template_string, json):

    def apply_recursive(template, json):
        res = {}
        if template == '':
            return json
        for key, val in template.items():
            if key in json and val == '':
                res[key] = json[key]
            elif key in json and val == '*':
                pass
            elif key in json and isinstance(val, list):
                if not isinstance(json[key], list):
                    raise ValueError()
                array = []
                for element in json[key]:
                    r = apply_recursive(val[0], element)
                    array.append(r)
                res[key] = array
            elif key in json and isinstance(val, dict):
                r = apply_recursive(val, json[key])
                res[key] = r
            elif key not in json and key == '*':
                for k, v in json.items():
                    try:
                        r = apply_recursive(val, v)
                    except ValueError:
                        continue
                    res[k] = r
            elif key not in json:
                raise ValueError()
        return res

    return apply_recursive(_parse_template(template_string), json)


def to_dict(obj, recursive=False, classkey=None):
    if hasattr(obj, "__dict__"):
        data = dict()
        for key in dir(obj):
            try:
                value = getattr(obj, key)
                if not callable(value) and not key.startswith('_'):
                    data[key] = (value if not recursive
                        else to_dict(value, recursive, classkey))
            except AttributeError:
                pass
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data

    if not recursive:
        return obj

    if isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = to_dict(obj[k], recursive, classkey)
        return obj
    elif hasattr(obj, "__iter__"):
        return [to_dict(v, recursive, classkey) for v in obj]

    return obj


def _extract_name_from_url(url):
    """Get object name from fully qualified link."""
    return url.split('/')[-1]


def get_collection_name(type_name):
    if type_name == "project":
        return None
    elif type_name.endswith("s"):
        return "%ses" % type_name
    else:
        return "%ss" % type_name


def get_type_kind(type_name):
    return "compute#%s" % type_name


def get_list_kind(type_name):
    return "compute#%sList" % type_name


def get_aggregated_kind(type_name):
    return "compute#%sAggregatedList" % type_name
