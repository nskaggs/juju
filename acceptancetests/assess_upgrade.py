#!/usr/bin/env python
""" TODO: Single line description of this assess script purpose.

TODO: add description For:
  - Juju features tested in this module
  - Brief outline of what the test will do to undertake this
  - Notes on any tricky details needed for the tests
  - etc.
"""

from __future__ import print_function

import argparse
import logging
import sys

from assess_model_migration import (
    assert_model_migrated_successfully,
    deploy_simple_server_to_new_model,
    migrate_model_to_controller,
    )
from assess_model_migration_versions import (
    AllMachinesRunning,
    get_new_devel_bootstrap_manager,
    create_bootstrap_environments,
    )
from deploy_stack import (
    get_random_string,
    )
from utility import (
    add_basic_testing_arguments,
    configure_logging,
    )

__metaclass__ = type

log = logging.getLogger('assess_model_migration_versions')


def assess_default_upgrade(stable_bsm, devel_bsm, args):
    """Upgrade an active model from stable to devel controller.

    Method:
      - Bootstraps the provided stable controller
      - Deploys an active application
      - Bootstraps a devel controller
      - Migrates from stable -> devel controller
      - Asserts the deployed application continues to work
    """
    with stable_bsm.booted_context(args.upload_tools):
        devel_bsm.client.env.juju_home = stable_bsm.client.env.juju_home
        with devel_bsm.existing_booted_context(args.upload_tools):
            stable_client = stable_bsm.client
            devel_client = devel_bsm.client
            resource_contents = get_random_string()
            test_stable_model, application = deploy_simple_server_to_new_model(
                stable_client,
                'upgrade-model',
                resource_contents)
            migration_target_client = migrate_model_to_controller(
                test_stable_model, devel_client)
            assert_model_migrated_successfully(
                migration_target_client, application, resource_contents)

            # Deploy another devel controller and attempt migration to it.
            another_bsm = get_new_devel_bootstrap_manager(args, devel_bsm)
            with another_bsm.existing_booted_context(args.upload_tools):
                another_bsm.client.get_controller_client().wait_for(
                    AllMachinesRunning())
                another_migration_client = migrate_model_to_controller(
                    migration_target_client, another_bsm.client)
                assert_model_migrated_successfully(
                    another_migration_client, application, resource_contents)

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description='Test upgrade between versioned controllers.')
    add_basic_testing_arguments(parser, existing=False)
    parser.add_argument(
        '--stable-juju-bin',
        help='Path to juju binary to be used as the stable version of juju.')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    configure_logging(args.verbose)

    stable_bsm, devel_bsm = create_bootstrap_environments(args)
    assess_default_upgrade(stable_bsm, devel_bsm, args)

    # TODO: add test for upgrading by using a specific agent
    #assess_specificed_agent_upgrade(stable_bsm, devel_bsm, args)



if __name__ == '__main__':
    sys.exit(main())
