#! /usr/bin/python3
# Copyright salsa-ci-team
# SPDX-License-Identifier: FSFAP
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved. This file is offered as-is, without any warranty.
"""Trigger a pipeline and wait until it finishes."""
import os
import argparse
import logging
from dataclasses import dataclass
from functools import lru_cache
import time

from gitlab import Gitlab

logger = logging.getLogger(__name__)


GITLAB_URL = os.environ.get('CI_SERVER_HOST')
REGISTRY_URL = os.environ.get('CI_REGISTRY_IMAGE')
PROJECT_ID = os.environ.get('CI_PROJECT_ID')
TOKEN = os.environ.get('CI_JOB_TOKEN')
REF = os.environ.get('CI_COMMIT_REF_NAME')
RELEASE = os.environ.get('RELEASE')
DEFAULT_BRANCH = os.environ.get('CI_DEFAULT_BRANCH')

PIPELINE_FAILED = 'failed'
PIPELINE_SUCCESS = 'success'
PIPELINE_CANCELED = 'canceled'
PIPELINE_FINISHED = [PIPELINE_FAILED, PIPELINE_SUCCESS, PIPELINE_CANCELED]


@dataclass
class PipelineData:
    gitlab_url: str
    project_id: int
    token: str
    reference: str
    variables: dict


class PipelineTrigger:
    """Pipeline trigger class."""
    def __init__(self, pipeline_data):
        """Init."""
        self.pipeline_data = pipeline_data

    @property
    @lru_cache(maxsize=None)
    def project(self):
        """Get Gitlab project."""
        gitlab = Gitlab(self.pipeline_data.gitlab_url)
        return gitlab.projects.get(self.pipeline_data.project_id)

    def _log_trigger_data(self):
        """Print the values of the trigger."""
        logger.info(f'Reference: {self.pipeline_data.reference}')
        logger.info(f'Variables:')
        [logger.info(f'{key}: {value}') for key, value in self.pipeline_data.variables.items()]

    def trigger(self):
        """Trigger a new pipeline."""
        logger.info('Triggering pipeline.')
        self._log_trigger_data()

        result = self.project.trigger_pipeline(
            ref=self.pipeline_data.reference,
            token=self.pipeline_data.token,
            variables=self.pipeline_data.variables
            )

        logger.debug(f'Result: {result}')
        logger.info(f'Triggered: {result.web_url}')
        return result

    def wait(self, pipeline):
        """Wait for pipeline to finish."""
        pipeline = self.project.pipelines.get(pipeline.id)
        while pipeline.status not in PIPELINE_FINISHED:
            logging.info(f'Pipeline {pipeline.id} is still running.')
            time.sleep(10)
            pipeline.refresh()

        logging.info(f'Pipeline finished with status <{pipeline.status}>')
        assert pipeline.status == PIPELINE_SUCCESS, 'Pipeline failed!'


def generate_staging_images_urls(registry_url, release, staging_tag):
    """Generate a dict with the variables of the Salsa CI pipeline images."""
    images = [
        # amd64 images
        ('APTLY', 'aptly'),
        ('AUTOPKGTEST', 'autopkgtest'),
        ('BASE', 'base'),
        ('GENERIC_TESTS', 'generic_tests'),
        ('BLHC', 'blhc'),
        ('GBP', 'gbp'),
        ('LINTIAN', 'lintian'),
        ('PIUPARTS', 'piuparts'),
        ('REPROTEST', 'reprotest'),
        # i386 images
        ('BASE_I386', 'i386/base'),
    ]

    return {
        f'SALSA_CI_IMAGES_{name}': f'{registry_url}/{path}:{release}_{staging_tag}'
        for name, path in images
    }


def create_variables_from_args(args, release):
    """Use args values to create the variables dict."""
    variables = {
        'IS_A_CHILD_PIPELINE': 'true',
        'RELEASE': release,
    }

    # Split key=value variables from args.
    for variable in args.env:
        key, value = variable.split('=')
        variables.update({key: value})

    if args.include_image_urls:
        logging.info(f'Current branch: {args.reference}. Default branch: {args.default_branch}')

        if args.default_branch == args.reference:
            logging.info('Running on default branch. Not including image urls.')

        else:
            images = generate_staging_images_urls(args.registry_url, release, staging_tag=args.staging_tag)
            variables.update(images)

    return variables


def arguments_parse():
    """Create argparser and return the arguments."""
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--gitlab-url', help='URL of the target instance',
                        default=f'https://{GITLAB_URL}')
    parser.add_argument('--project-id', help='ID or namespace of the targeted project',
                        default=PROJECT_ID)
    parser.add_argument('--token', help='Pipeline token.',
                        default=TOKEN)
    parser.add_argument('--reference', help='Branch to trigger',
                        default=REF)
    parser.add_argument('-e','--env', action='append', help='Variables to add',
                        default=[])
    parser.add_argument('--verbose', help='Output verbose', action='store_true')

    # To be used on salsa-ci-team/pipeline CI.
    parser.add_argument('--release', help='Release variable to use for Salsa CI Images.',
                        default=[RELEASE,], nargs='+')
    parser.add_argument('--include-image-urls', help='Include the Salsa CI Images urls.',
                        action='store_true')
    parser.add_argument('--registry-url', help='Registry URL. '
                                               'To be used with --include-image-urls',
                        default=REGISTRY_URL)
    parser.add_argument('--default-branch', help='Repository default branch to identify staging vs main branch. '
                                                 'To be used with --include-image-urls',
                        default=DEFAULT_BRANCH)
    parser.add_argument('--staging-tag', help='String to be used as staging tag.'
                                              'To be used with --include-image-urls',
                        default=REF)
    return parser.parse_args()


if __name__ == '__main__':
    args = arguments_parse()

    if args.verbose:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    logging.basicConfig(level=logging_level)

    triggered_pipelines = []
    for release in args.release:
        variables = create_variables_from_args(args, release)

        pipeline_data = PipelineData(
            args.gitlab_url,
            args.project_id,
            args.token,
            args.reference,
            variables,
        )

        trigger = PipelineTrigger(pipeline_data)
        pipeline = trigger.trigger()
        triggered_pipelines.append((trigger, pipeline))

    for trigger, pipeline in triggered_pipelines:
        trigger.wait(pipeline)
