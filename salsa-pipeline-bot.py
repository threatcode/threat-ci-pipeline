#!/usr/bin/python3
# salsa pipeline bot

import os
import tempfile
import subprocess
import shlex
import requests
import time
import logging

import gitlab
import yaml
from pipeline_loader import load_pipeline, fetch_remote_content
from repositories import REPOS


GITLAB_URL = 'https://salsa.debian.org'
GITLAB_PRIVATE_TOKEN = os.environ.get('SALSA_TOKEN')
SALSA_PIPELINE_YML_PATH = './debian/gitlab-ci.yml'
SALSA_PIPELINE_YML_TPL_PATH = './debian/gitlab-ci.yml.tpl'
SALSA_PIPELINE_TPL_URL = 'https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml.tpl'
SALSA_GCI_NEW_BRANCH = 'add-salsa-ci'
SALSA_PIPELINE_BOT_LABEL = 'salsa-ci-bot'


def run_cmd(*args, **kwargs):
    logging.info('Executing {}'.format(*args))
    cmd = shlex.split(args[0])
    proc = subprocess.Popen(cmd, cwd=kwargs.get('workdir'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    exit_code = proc.poll()
    if exit_code != 0:
        logging.error('\nstdout:\n%r\n\nstderr:\n%r\n' % (stdout, stderr))
        raise subprocess.CalledProcessError(exit_code, ' '.join(args))
    return stdout, stderr, exit_code


def get_mr_in_progress(project):
    return project.mergerequests.list(labels=[SALSA_PIPELINE_BOT_LABEL], state='opened')


def create_merge_request(project, source_branch, title, description, labels,
                         auto_accept=True, target_branch=None):
    target_branch = target_branch or project.attributes['default_branch']
    mr = project.mergerequests.create({
        'source_branch': source_branch,
        'target_branch': target_branch,
        'title': title,
        'description': description,
        'labels': labels,
        'remove_source_branch': True,
    })
    if auto_accept:
        # Sometimes it gets merged with no waiting for the pipeline...
        # Let's see if the following seep helps... /shrug
        time.sleep(15)
        mr.merge(should_remove_source_branch=True,
                 merge_when_pipeline_succeeds=True)


def git_add_pipeline_template(yml_tpl_path, workdir):
    with open(yml_tpl_path, 'w', encoding='utf-8') as f:
        data = fetch_remote_content(SALSA_PIPELINE_TPL_URL)
        f.write(data)
    run_cmd(f'git add {SALSA_PIPELINE_YML_TPL_PATH}', workdir=workdir)
    run_cmd(f'git commit -m "Add pipeline template\nGbp-Dch: Ignore"', workdir=workdir)


def git_add_pipeline_rendered(content, yml_path, git_comment, workdir):
    with open(yml_path, 'w', encoding='utf-8') as f:
        f.write(content)
    run_cmd(f'git add {SALSA_PIPELINE_YML_PATH}', workdir=workdir)
    run_cmd(f'git commit -m "{git_comment}\nGbp-Dch: Ignore"', workdir=workdir)


def add_gci_support(gl, repo_id, workdir, yml_path, yml_tpl_path,
                    branch_name=SALSA_GCI_NEW_BRANCH, auto_accept=True):
    logging.info('Adding gci support for the first time')
    project = gl.projects.get(repo_id)
    run_cmd(f'git checkout -b {branch_name}', workdir=workdir)

    git_add_pipeline_template(yml_tpl_path, workdir)
    pipeline = load_pipeline(yml_tpl_path)
    git_add_pipeline_rendered(pipeline, yml_path, 'Initial pipeline', workdir)

    run_cmd(f'git push origin {branch_name}', workdir=workdir)
    create_merge_request(project,
                         branch_name,
                         'Add salsa-ci pipeline',
                         '',
                         [SALSA_PIPELINE_BOT_LABEL],
                         auto_accept)


def check_for_pipeline_update(gl, repo_id, workdir, yml_path, yml_tpl_path):
    logging.info('Checking for pipeline update')
    project = gl.projects.get(repo_id)
    branch_name = f'salsa-ci-{int(time.time())}'
    if not os.path.exists(yml_tpl_path):
        add_gci_support(gl, repo_id, workdir, yml_path, yml_tpl_path,
                        branch_name, auto_accept=False)
        return
    pipeline_rendered = load_pipeline(yml_tpl_path)
    with open(yml_path, 'r', encoding='utf-8') as f:
        current_pipeline = f.read()

    if current_pipeline != pipeline_rendered:
        run_cmd(f'git checkout -b {branch_name}', workdir=workdir)
        git_add_pipeline_rendered(pipeline_rendered, yml_path,
                                  'Update pipeline', workdir)
        run_cmd(f'git push origin {branch_name}', workdir=workdir)
        create_merge_request(project,
                             branch_name,
                             'Update salsa-ci pipeline',
                             '',
                             [SALSA_PIPELINE_BOT_LABEL])


class RepositoryNotFound(Exception):
    pass


def get_repo_id(gl, repo):
    project_name, _ = os.path.splitext(os.path.basename(repo))
    for project in gl.projects.list(search=project_name):
        if project.attributes['path_with_namespace'] in repo:
            return project.attributes['id']
    raise RepositoryNotFound("Couldn't find the id for {}".format(repo))


def run(repo, gitlab_url, gitlab_private_token):
    gl = gitlab.Gitlab(gitlab_url, private_token=gitlab_private_token)
    repo_id = get_repo_id(gl, repo)
    if os.environ.get('SALSA_PIPELINE_PASSWORD', None):
        repo_url = f'https://salsa.debian.org/{repo}'
    else:
        repo_url = f'git@salsa.debian.org:{repo}'
    project = gl.projects.get(repo_id)
    if get_mr_in_progress(project):
        logging.info(f'[{repo}] There is a MR already in course, please merge it to allow new MRs be proposed by salsa-ci-bot')
        return
    if gl.projects.get(repo_id).attributes['ci_config_path'] != os.path.relpath(SALSA_PIPELINE_YML_PATH):
        ci_config_path = os.path.relpath(SALSA_PIPELINE_YML_PATH)
        logging.error(f'[{repo}] Wrong CI config path, please change it to {ci_config_path}')
        return
    with tempfile.TemporaryDirectory() as tmpdir:
        yml_path = os.path.join(tmpdir, SALSA_PIPELINE_YML_PATH)
        yml_tpl_path = os.path.join(tmpdir, SALSA_PIPELINE_YML_TPL_PATH)
        run_cmd(f'git clone --depth 1 {repo_url} .', workdir=tmpdir)
        if not os.path.exists(yml_path):
            add_gci_support(gl, repo_id, tmpdir, yml_path, yml_tpl_path)
        else:
            check_for_pipeline_update(gl, repo_id, tmpdir, yml_path, yml_tpl_path)


if __name__ == '__main__':
    FORMAT = '%(message)s'
    logging.basicConfig(level=os.environ.get('LOG_LEVEL', logging.INFO), format=FORMAT)
    for repo in REPOS:
        try:
            run(repo, GITLAB_URL, GITLAB_PRIVATE_TOKEN)
        except Exception as e:
            logging.error(e)
