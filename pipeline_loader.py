import os
import requests
import io

import yaml


def parse_salsa_pipeline_tpl(filename):
    salsa_pipeline_tps = []
    salsa_pipeline = []
    data = salsa_pipeline_tps
    with open(filename, 'r') as f:
        for line in f.readlines():
            if '# end of salsa pipeline bot parser' in line:
                data = salsa_pipeline
                continue
            data.append(line)
    return ''.join(salsa_pipeline_tps), ''.join(salsa_pipeline)


def fetch_remote_content(url):
    response = requests.get(url)
    return str(response.content, encoding='utf-8')


def get_include_item(value):
    if value.startswith('http'):
        return fetch_remote_content(value)
    else:
        with open(value, 'r', encoding='utf-8') as f:
            return f.read()


class IncludeWrongFormat(Exception):
    pass


def render_salsa_pipeline_tpl(salsa_pipeline_tpl):
    f = io.StringIO(''.join(salsa_pipeline_tpl))
    data = yaml.load(f, yaml.SafeLoader)
    content_rendered = []
    include = data.get('include', '')
    if type(include) not in (str, list):
        raise IncludeWrongFormat('It must be a string or a list')
    if type(include) == str:
        include = [include]
    for item in include:
        content = get_include_item(item)
        content_rendered.append(content)
    return ''.join(content_rendered)


if __name__ == '__main__':
    import sys
    salsa_pipeline_tpl, salsa_pipeline = parse_salsa_pipeline_tpl(sys.argv[1])
    content = render_salsa_pipeline_tpl(salsa_pipeline_tpl)
    pipeline = content + salsa_pipeline
    print(pipeline)
