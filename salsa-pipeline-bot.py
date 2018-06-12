#!/usr/bin/python3
# salsa pipeline bot

import os
import tempfile
import subprocess
import shlex
import requests
import time

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
    print('Executing {}'.format(*args))
    cmd = shlex.split(args[0])
    proc = subprocess.Popen(cmd, cwd=kwargs.get('workdir'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    exit_code = proc.poll()
    print(stdout, stderr)
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
    })
    if auto_accept:
        time.sleep(10) # waiting for the pipeline creation
        mr = project.mergerequests.get(mr.id)
        mr.cancel_merge_when_pipeline_succeeds()


def add_gci_support(gl, repo_id, workdir, yml_path, yml_tpl_path):
    project = gl.projects.get(repo_id)
    add_privileged_runner(project)
    if get_mr_in_progress(project):
        print('There is a MR already in course, please merge it to allow new MRs be proposed by salsa-ci-bot')
        return
    gl.projects.update(
        repo_id,
        {
            'ci_config_path': os.path.relpath(SALSA_PIPELINE_YML_PATH),
        },
    )
    run_cmd(f'git checkout -b {SALSA_GCI_NEW_BRANCH}', workdir=workdir)
    with open(yml_tpl_path, 'w') as f:
        data = fetch_remote_content(SALSA_PIPELINE_TPL_URL)
        f.write(data)
    run_cmd(f'git add {SALSA_PIPELINE_YML_TPL_PATH}', workdir=workdir)
    run_cmd(f'git commit -m "Add template of pipeline"', workdir=workdir)
    with open(yml_path, 'w') as f:
        pipeline = load_pipeline(yml_tpl_path)
        f.write(pipeline)
    run_cmd(f'git add {SALSA_PIPELINE_YML_PATH}', workdir=workdir)
    run_cmd(f'git commit -m "Add initial pipeline"', workdir=workdir)
    run_cmd(f'git push origin {SALSA_GCI_NEW_BRANCH}', workdir=workdir)
    create_merge_request(project,
                         SALSA_GCI_NEW_BRANCH,
                         'Add salsa-ci pipeline',
                         '',
                         [SALSA_PIPELINE_BOT_LABEL])


def check_for_pipeline_update(gl, repo_id, workdir, yml_path, yml_tpl_path):
    project = gl.projects.get(repo_id)
    if get_mr_in_progress(project):
        print('There is a MR already in course, please merge it to allow new MRs be proposed by salsa-ci-bot')
        return
    if not os.path.exists(yml_tpl_path):
        print('WARNING not using templates')
        return
    pipeline = load_pipeline(yml_tpl_path)
    # do comparison between the current on the repo and see if a mr is needed


def get_repo_id(gl, repo_url):
    project_name, _ = os.path.splitext(os.path.basename(repo_url))
    for project in gl.projects.list(search=project_name):
        if project.attributes['path_with_namespace'] in repo_url:
            return project.attributes['id']
    raise Exception("Couldn't find the project íd for {}".format(repo_url))


def add_privileged_runner(project):
    try:
        project.runners.create({'runner_id': 40})
    except gitlab.exceptions.GitlabCreateError:
        pass


def run(repo_url, gitlab_url, gitlab_private_token):
    gl = gitlab.Gitlab(gitlab_url, private_token=gitlab_private_token)
    repo_id = get_repo_id(gl, repo_url)
    project = gl.projects.get(repo_id)
    with tempfile.TemporaryDirectory() as tmpdir:
        yml_path = os.path.join(tmpdir, SALSA_PIPELINE_YML_PATH)
        yml_tpl_path = os.path.join(tmpdir, SALSA_PIPELINE_YML_TPL_PATH)
        run_cmd(f'git clone {repo_url} .', workdir=tmpdir)
        if not os.path.exists(yml_path):
            add_gci_support(gl, repo_id, tmpdir, yml_path, yml_tpl_path)
        else:
            check_for_pipeline_update(gl, repo_id, tmpdir, yml_path, yml_tpl_path)


if __name__ == '__main__':
    for repo_url in REPOS:
        run(repo_url, GITLAB_URL, GITLAB_PRIVATE_TOKEN)
