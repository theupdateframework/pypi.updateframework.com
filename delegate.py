#!/usr/bin/env python





"""A simple library to make it easier to delegate targets from delegator A to
delegatee B. This is useful for automation of the development
environment on pypi.updateframework.com."""


import datetime
import os
import time

from tuf.log import logger

import tuf.formats as formats
import tuf.repo.keystore as keystore
import tuf.repo.signercli as signercli
import tuf.repo.signerlib as signerlib

import check





########################### GLOBAL VARIABLES ##################################

# TODO: Need to review:
# http://csrc.nist.gov/publications/nistpubs/800-131A/sp800-131A.pdf
KEY_SIZE=2048

# Top-level role names.
RELEASE_ROLE_NAME = 'release'
TARGETS_ROLE_NAME = 'targets'
TIMESTAMP_ROLE_NAME = 'timestamp'

# Delegated targets role names.
CLAIMED_TARGETS_ROLE_NAME = '{0}/claimed'.format(TARGETS_ROLE_NAME)
RECENTLY_CLAIMED_TARGETS_ROLE_NAME = \
  '{0}/recently-claimed'.format(TARGETS_ROLE_NAME)
UNCLAIMED_TARGETS_ROLE_NAME = '{0}/unclaimed'.format(TARGETS_ROLE_NAME)

# Map full role names (str) to list of passwords ([str, ..., str]).
# Storing passwords in the clear is generally a bad idea. It is acceptable for
# development (but certainly not production).
ROLE_NAME_TO_PASSWORDS = {
  RELEASE_ROLE_NAME: ['release'],
  TARGETS_ROLE_NAME: ['targets'],
  TIMESTAMP_ROLE_NAME: ['timestamp'],
  CLAIMED_TARGETS_ROLE_NAME: ['claimed'],
  RECENTLY_CLAIMED_TARGETS_ROLE_NAME: ['recently-claimed'],
  UNCLAIMED_TARGETS_ROLE_NAME: ['unclaimed']
}

# Some expected directories and files.
KEYSTORE_DIRECTORY = os.path.abspath('keystore')
REPOSITORY_DIRECTORY = os.path.abspath('repository')
# Assume that config is at repository/config.cfg
CONFIGURATION_FILE = os.path.join(REPOSITORY_DIRECTORY, 'config.cfg')
# Assume that metadata is in repository/metadata
METADATA_DIRECTORY = os.path.join(REPOSITORY_DIRECTORY, 'metadata')
# Assume that metadata is in repository/targets
TARGETS_DIRECTORY = os.path.join(REPOSITORY_DIRECTORY, 'targets')

# Where are these metadata files expected to be located?
RELEASE_ROLE_FILE = os.path.join(METADATA_DIRECTORY,
                                 '{0}.txt'.format(RELEASE_ROLE_NAME))
TIMESTAMP_ROLE_FILE = os.path.join(METADATA_DIRECTORY,
                                 '{0}.txt'.format(TIMESTAMP_ROLE_NAME))




def check_sanity():
  """Check that we correctly set some parameters."""

  assert os.path.isdir(KEYSTORE_DIRECTORY)
  assert os.path.isdir(REPOSITORY_DIRECTORY)
  assert METADATA_DIRECTORY.startswith(REPOSITORY_DIRECTORY)
  assert os.path.isdir(METADATA_DIRECTORY)
  assert TARGETS_DIRECTORY.startswith(REPOSITORY_DIRECTORY)
  assert os.path.isdir(TARGETS_DIRECTORY)





# TODO: Update delegator if the relevant keys have changed.
# TODO: Ugly function which needs refactoring.
def delegator_needs_update(delegator_targets_role_name,
                           relative_delegatee_targets_role_name,
                           relative_delegated_paths,
                           path_hash_prefix):
  # By default, we will assume that the delegator needs no update.
  needs_update = False

  # Extract metadata from the delegator targets role.
  delegator_filename = \
    os.path.join(METADATA_DIRECTORY,
                 '{0}.txt'.format(delegator_targets_role_name))
  delegator_metadata_dict = \
    signerlib.read_metadata_file(delegator_filename)
  # TODO: Verify signature on delegator metadata!
  delegator_signed_metadata = delegator_metadata_dict['signed']

  # Find the delegatee, if it exists, in the delegator.
  delegations = delegator_signed_metadata.get('delegations', {})
  roles = delegations.get('roles', [])
  absolute_delegatee_targets_role_name = \
    '{0}/{1}'.format(delegator_targets_role_name,
                     relative_delegatee_targets_role_name)
  role_index = \
    signerlib.find_delegated_role(roles, absolute_delegatee_targets_role_name)

  if role_index is None:
    needs_update = True
    logger.info('{0} does not know about {1}'.format(
                delegator_targets_role_name,
                relative_delegatee_targets_role_name))
  else:
    role = roles[role_index]
    role_paths = role.get('paths')
    role_path_hash_prefix = role.get('path_hash_prefix')

    # relative_delegated_paths are relative to 'repository'.
    # relative_role_paths are relative to 'repository/targets'.
    # This is because role_paths are relative to 'repository/targets'.
    relative_role_paths = []
    for relative_delegated_path in relative_delegated_paths:
      assert relative_delegated_path.startswith('targets/')
      relative_role_paths.append(relative_delegated_path[8:])

    # Check role paths.
    if role_paths is not None:
      if relative_delegated_paths is not None:
        if set(role_paths) == set(relative_role_paths):
          logger.debug('Role paths are the same.')
        else:
          needs_update = True
          logger.info('Role paths have changed!')
      else:
        assert path_hash_prefix is not None
        needs_update = True
        logger.info('Role paths have been substituted with path_hash_prefix!')

    # Otherwise, check role path_hash_prefix.
    elif role_path_hash_prefix is not None:
      if path_hash_prefix is not None:
        if role_path_hash_prefix == path_hash_prefix:
          logger.debug('Role path_hash_prefix is the same.')
        else:
          needs_update = True
          logger.debug('Role path_hash_prefix has changed!')
      else:
        assert relative_delegated_paths is not None
        needs_update = True
        logger.info('Role path_hash_prefix has been substituted with paths!')

    # If both paths and path_hash_prefix are missing, then something is wrong.
    else:
      raise tuf.RepositoryError('Missing both paths and path_hash_prefix!')

  return needs_update





def generate_rsa_keys(passwords):
  """Return the IDs of RSA keys encrypted in order with the given passwords."""

  rsa_keys = []

  for password in passwords:
    # Generate the RSA key and save it to 'keystore_directory'.
    rsa_key = \
      signerlib.generate_and_save_rsa_key(keystore_directory=KEYSTORE_DIRECTORY,
                                          password=password, bits=KEY_SIZE)
    rsa_key_id = rsa_key['keyid']
    rsa_keys.append(rsa_key_id)

  return rsa_keys





def get_absolute_delegated_paths(files_directory, recursive_walk=True,
                                 followlinks=True,
                                 file_predicate=signerlib.accept_any_file):
  """Given the directory which contains the target files of interest to the
  delegatee (files_directory), walk the directory recursively (or not: see
  recursive_walk) and follow symbolic links (or not: see followlinks) to
  determine and return all target files satisfying a predicate (any file is
  accepted by default: see file_predicate)."""

  # Retrieve for the targets role targets matching the given file predicate.
  absolute_delegated_paths = \
    signerlib.get_targets(files_directory, recursive_walk=recursive_walk,
                          followlinks=followlinks,
                          file_predicate=file_predicate)

  return absolute_delegated_paths





def get_expiration_date(time_delta):
  # TODO: Adjust for UTC.
  # http://stackoverflow.com/a/2775982
  future_date = datetime.datetime.now() + time_delta
  expiration_date = formats.format_time(time.mktime(future_date.timetuple()))
  return expiration_date





def get_keys_for_targets_role(targets_role_name):
  """Given the name of a targets role (targets_role_name) and its list of
  passwords (targets_role_passwords), return the RSA key IDs for a targets role.

  Side effect: Load the aforementioned RSA keys into the global TUF
  keystore."""

  # Get the list of passwords for this role.
  targets_role_passwords = ROLE_NAME_TO_PASSWORDS[targets_role_name]

  # Get all the target roles and their respective keyids.
  # These keyids will let the user know which roles are currently known.
  # signerlib.get_target_keyids() returns a dictionary that looks something
  # like this: {'targets': [keyid1, ...], 'targets/role1': [keyid1, ...] ...}
  targets_roles = signerlib.get_target_keyids(METADATA_DIRECTORY)

  # Either get extant keys or create new ones for the targets role.
  # NOTE: Yes, suppose we have generated these keys before but never associated
  # them with the targets role. Then we would unnecessarily create new keys.
  # One solution is a tool that finds unassociated keys and offers to delete
  # them. 
  if targets_role_name in targets_roles:
    targets_role_keys = targets_roles[targets_role_name]
  else:
    targets_role_keys = generate_rsa_keys(targets_role_passwords)

  # Decrypt and load the keys of the targets role.
  loaded_targets_role_keys = \
    keystore.load_keystore_from_keyfiles(KEYSTORE_DIRECTORY, targets_role_keys,
                                         targets_role_passwords)
  assert targets_role_keys == loaded_targets_role_keys

  return targets_role_keys





def get_keys_for_top_level_role(top_level_role_name):
  # What are the keys of the top-level role?
  configuration = signerlib.read_config_file(CONFIGURATION_FILE)
  top_level_role_configuration = configuration[top_level_role_name]
  top_level_role_keys = top_level_role_configuration['keyids']
  top_level_role_passwords = ROLE_NAME_TO_PASSWORDS[top_level_role_name]

  # Decrypt and load the keys of the timestamp role.
  loaded_top_level_role_keys = \
    keystore.load_keystore_from_keyfiles(KEYSTORE_DIRECTORY,
                                         top_level_role_keys,
                                         top_level_role_passwords)
  assert top_level_role_keys == loaded_top_level_role_keys

  return top_level_role_keys




def get_relative_delegated_paths(absolute_delegated_paths):
  relative_delegated_paths = []

  # Map absolute delegated paths to be relative to the TARGETS_DIRECTORY.
  # This means that they must start with the relative "targets/" path.
  for absolute_delegated_path in absolute_delegated_paths:
    assert absolute_delegated_path.startswith(TARGETS_DIRECTORY+'/')
    relative_delegated_path = \
      absolute_delegated_path[len(REPOSITORY_DIRECTORY)+1:]
    relative_delegated_paths.append(relative_delegated_path)

  return relative_delegated_paths





# TODO: Verify signature on metadata!
def get_version_number(metadata_filename):
  version_number = None

  if os.path.isfile(metadata_filename):
    metadata_dict = signerlib.read_metadata_file(metadata_filename)
    signed_metadata = metadata_dict['signed']
    version_number = signed_metadata['version']
    logger.info('Previous version for {0}: {1}'.format(metadata_filename,
                version_number))
    version_number += 1
    logger.info('Current version for {0}: {1}'.format(metadata_filename,
                version_number))
  else:
    logger.warn('{0} does not exist! Assuming first version...'.format(
                metadata_filename))
    version_number = 1

  return version_number





def make_delegation(delegator_targets_role_name, delegatee_targets_role_name,
                    relative_delegated_paths=None,
                    path_hash_prefix=None):

  # The name of the delegatee contain the name of its delegator as a prefix.
  assert \
    delegatee_targets_role_name.startswith(delegator_targets_role_name+'/')

  # relative_delegated_paths XOR path_hash_prefix
  assert (relative_delegated_paths is None and path_hash_prefix is not None) \
          or \
         (relative_delegated_paths is not None and path_hash_prefix is None)

  # Load targets roles keys into memory, and get their key IDs.
  delegator_targets_role_keys = \
    get_keys_for_targets_role(delegator_targets_role_name)
  delegatee_targets_role_keys = \
    get_keys_for_targets_role(delegatee_targets_role_name)

  # We need to extract the relative name of the full delegatee targets role
  # name. For example, if the delegator is 'targets/a' and its delegatee is
  # 'targets/a/b', then the relative name of the delegatee is 'b'.
  relative_delegatee_targets_role_name = \
    delegatee_targets_role_name[len(delegator_targets_role_name)+1:]

  # Update the delegator metadata file.
  update_delegator_metadata(delegator_targets_role_name,
                            relative_delegatee_targets_role_name,
                            delegator_targets_role_keys,
                            delegatee_targets_role_keys,
                            relative_delegated_paths=relative_delegated_paths,
                            path_hash_prefix=path_hash_prefix)





def need_delegation(targets_role_name, files_directory, recursive_walk=True,
                    followlinks=True,
                    file_predicate=signerlib.accept_any_file):
  """Given a targets role name (targets_role_name) and the directory which
  contains the target files of interest (files_directory), walk the directory
  recursively (or not: see recursive_walk) and follow symbolic links (or not:
  see followlinks) to see whether any target file satisfying a predicate (any
  file is accepted by default: see file_predicate) needs to be added, updated
  or deleted."""

  matched = False

  try:
    matched = check.metadata_matches_data(METADATA_DIRECTORY,
                                          TARGETS_DIRECTORY,
                                          targets_role_name, files_directory,
                                          recursive_walk=recursive_walk,
                                          followlinks=followlinks,
                                          file_predicate=file_predicate)
  except check.MissingTargetMetadataError:
    # The metadata for this targets role is missing, so it certainly needs
    # delegation!
    matched = False

  return not matched





def update_delegator_metadata(delegator_targets_role_name,
                              relative_delegatee_targets_role_name,
                              delegator_targets_role_keys,
                              delegatee_targets_role_keys,
                              relative_delegated_paths=None,
                              path_hash_prefix=None):

  # relative_delegated_paths XOR path_hash_prefix
  assert (relative_delegated_paths is None and path_hash_prefix is not None) \
          or \
         (relative_delegated_paths is not None and path_hash_prefix is None)

  if delegator_needs_update(delegator_targets_role_name,
                            relative_delegatee_targets_role_name,
                            relative_delegated_paths,
                            path_hash_prefix):
    signercli._update_parent_metadata(METADATA_DIRECTORY,
                              relative_delegatee_targets_role_name,
                              delegatee_targets_role_keys,
                              delegator_targets_role_name,
                              delegator_targets_role_keys,
                              delegated_paths=relative_delegated_paths,
                              path_hash_prefix=path_hash_prefix)
  else:
    logger.warn('{0} does not need to be updated about {1}'.format(
                delegator_targets_role_name,
                relative_delegatee_targets_role_name))





# TODO: Update delegatee only if necessary to do so.
def update_targets_metadata(targets_role_name, relative_delegated_paths,
                            targets_role_keys, time_delta):

  # TODO: Ensure that targets_role_name is of the correct form.
  assert targets_role_name == 'targets' or \
         targets_role_name.startswith('targets/')

  # The first time a parent role creates a delegation, a directory containing
  # the parent role's name is created in the metadata directory.  For example,
  # if the targets roles creates a delegated role 'role1', the metadata
  # directory would then contain:
  # '{METADATA_DIRECTORY}/targets/role1.txt', where 'role1.txt' is the
  # delegated role's metadata file.
  # If delegated role 'role1' creates its own delegated role 'role2', the
  # metadata directory would then contain:
  # '{METADATA_DIRECTORY}/targets/role1/role2.txt'.
  # When creating a delegated role, if the parent directory already exists,
  # this means a prior delegation has been performed by the parent.

  parent_role_name = os.path.dirname(targets_role_name)
  child_role_name = os.path.basename(targets_role_name)

  parent_role_directory = os.path.join(METADATA_DIRECTORY, parent_role_name)
  if not os.path.isdir(parent_role_directory):
    os.mkdir(parent_role_directory)

  # Set the filename of the targets role metadata.
  targets_role_filename = child_role_name+'.txt'
  targets_role_filename = os.path.join(parent_role_directory,
                                       targets_role_filename)

  expiration_date = get_expiration_date(time_delta)
  version_number = get_version_number(targets_role_filename)

  # Prepare the targets metadata.
  targets_metadata = \
    signerlib.generate_targets_metadata(REPOSITORY_DIRECTORY,
                                        relative_delegated_paths,
                                        version_number, expiration_date)

  # Sign and write the targets role metadata.
  signercli._sign_and_write_metadata(targets_metadata, targets_role_keys,
                                     targets_role_filename)





def update_release(time_delta):
  expiration_date = get_expiration_date(time_delta)
  release_role_keys = get_keys_for_top_level_role(RELEASE_ROLE_NAME)
  version_number = get_version_number(RELEASE_ROLE_FILE)

  # Generate and write the signed release metadata.
  signerlib.build_release_file(release_role_keys, METADATA_DIRECTORY,
                               version_number, expiration_date)





def update_timestamp(time_delta):
  expiration_date = get_expiration_date(time_delta)
  timestamp_role_keys = get_keys_for_top_level_role(TIMESTAMP_ROLE_NAME)
  version_number = get_version_number(TIMESTAMP_ROLE_FILE)

  # Generate and write the signed timestamp metadata.
  signerlib.build_timestamp_file(timestamp_role_keys, METADATA_DIRECTORY,
                               version_number, expiration_date)





########################### GLOBAL STATEMENTS #################################

# Perform sanity checks when this module is imported.
check_sanity()





