#!/usr/bin/env python





"""A simple program to automatically delegate "stable" targets (i.e. targets
older than, say, a month). This is useful for automation of the development
environment on pypi.updateframework.com.

NOTE: This process *MUST NOT* be done automatically in a production
environment, as it would defeat the secure practice of separating "stable"
targets with offline keys from "unstable" targets with online keys."""


import datetime
import os.path

import tuf.repo.keystore as keystore
import tuf.repo.signercli as signercli
import tuf.repo.signerlib as signerlib

from metadata_matches_data import (MissingTargetMetadataError,
                                   metadata_matches_data)





########################### GLOBAL VARIABLES ##################################
KEY_SIZE=2048

TARGETS_ROLE_NAME = "targets"
STABLE_TARGETS_ROLE_NAME = "stable"

TARGETS_ROLE_PASSWORDS = ["targets"]
STABLE_TARGETS_ROLE_PASSWORDS = ["stable"]

KEYSTORE_DIRECTORY = os.path.abspath("keystore")
REPOSITORY_DIRECTORY = os.path.abspath("repository")
# Assume that metadata is in /path/to/repository/metadata
METADATA_DIRECTORY = os.path.join(REPOSITORY_DIRECTORY, "metadata")
# Assume that metadata is in /path/to/repository/targets
TARGETS_DIRECTORY = os.path.join(REPOSITORY_DIRECTORY, "targets")

# Recursively walk the targets directory?
RECURSIVE_WALK = True
# Follow symbolic links in the targets directory?
FOLLOWLINKS = True





def check_sanity():
  """Check that we correctly set some parameters."""

  assert os.path.isdir(KEYSTORE_DIRECTORY)
  assert os.path.isdir(REPOSITORY_DIRECTORY)
  assert METADATA_DIRECTORY.startswith(REPOSITORY_DIRECTORY)
  assert os.path.isdir(METADATA_DIRECTORY)
  assert TARGETS_DIRECTORY.startswith(REPOSITORY_DIRECTORY)
  assert os.path.isdir(TARGETS_DIRECTORY)





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





def load_targets_roles_keys():
  """Return the RSA key IDs for the targets and stable targets roles.

  Side effect: Load the aforementioned RSA keys into the TUF keystore.
  """

  # Get all the target roles and their respective keyids.
  # These keyids will let the user know which roles are currently known.
  # signerlib.get_target_keyids() returns a dictionary that looks something
  # like this: {'targets': [keyid1, ...], 'targets/role1': [keyid1, ...] ...}
  targets_roles = signerlib.get_target_keyids(METADATA_DIRECTORY)

  # By the time we call this program, we should already have the targets role.
  assert TARGETS_ROLE_NAME in targets_roles
  targets_role_keys = targets_roles[TARGETS_ROLE_NAME]

  # Decrypt and load targets role keys.
  loaded_targets_role_keys = \
    keystore.load_keystore_from_keyfiles(KEYSTORE_DIRECTORY, targets_role_keys,
                                         TARGETS_ROLE_PASSWORDS)
  assert targets_role_keys == loaded_targets_role_keys

  # Either get extant keys or create new ones for the stable targets role.
  # NOTE: Yes, suppose we have generated these keys before but never associated
  # them with the stable targets role. Then we would unnecessarily create new
  # keys. One solution is a tool that finds unassociated keys and offers to
  # delete them. 
  if STABLE_TARGETS_ROLE_NAME in targets_roles:
    stable_targets_role_keys = targets_roles[STABLE_TARGETS_ROLE_NAME]
  else:
    stable_targets_role_keys = generate_rsa_keys(STABLE_TARGETS_ROLE_PASSWORDS)

  # Decrypt and load stable targets role keys.
  loaded_stable_targets_role_keys = \
    keystore.load_keystore_from_keyfiles(KEYSTORE_DIRECTORY,
                                         stable_targets_role_keys,
                                         STABLE_TARGETS_ROLE_PASSWORDS)
  assert stable_targets_role_keys == loaded_stable_targets_role_keys

  return targets_role_keys, stable_targets_role_keys





# Set the default test for the "stability" of a target file.
def file_predicate(full_target_path, now=datetime.datetime.now()):
  """Was this file last modified at least a month ago?"""

  # We must fix a "now" time for the file "stability" test.
  # Note that "now" is fixed between calls to this function because in Python,
  # default parameters are evaluated once:
  # http://docs.python-guide.org/en/latest/writing/gotchas.html

  stat = os.stat(full_target_path)
  then = datetime.datetime.fromtimestamp(stat.st_mtime)
  time_delta = now - then
  if time_delta.days >= 30:
    return True
  else:
    return False





def need_delegation():
  """We need a delegation if the stable targets metadata does not match the
  data."""

  matched = False

  try:
    stable_targets_role_name = os.path.join(TARGETS_ROLE_NAME,
                                            STABLE_TARGETS_ROLE_NAME)
    matched = metadata_matches_data(METADATA_DIRECTORY, TARGETS_DIRECTORY,
                                    stable_targets_role_name,
                                    TARGETS_DIRECTORY,
                                    recursive_walk=RECURSIVE_WALK,
                                    followlinks=FOLLOWLINKS,
                                    file_predicate=file_predicate)
  except MissingTargetMetadataError:
    matched = False
  except:
    raise
  finally:
    return not matched





def make_delegation():
  """Make the delegation from targets to the stable targets roles."""

  # Retrieve "stable" targets for the stable targets role.
  delegated_paths = signerlib.get_targets(TARGETS_DIRECTORY,
                                          recursive_walk=RECURSIVE_WALK,
                                          followlinks=FOLLOWLINKS,
                                          file_predicate=file_predicate)

  # Filter delegated_paths to be relative to the TARGETS_DIRECTORY.
  # Presently, this means that they share the "targets/" prefix.
  for index in xrange(len(delegated_paths)):
    full_target_path = delegated_paths[index]
    assert full_target_path.startswith(TARGETS_DIRECTORY)
    relative_target_path = full_target_path[len(REPOSITORY_DIRECTORY)+1:]
    delegated_paths[index] = relative_target_path

  # Load targets roles keys into memory, and get the key IDs.
  targets_role_keys, stable_targets_role_keys = load_targets_roles_keys()

  # Create, sign, and write the delegated role's metadata file.
  signercli._make_delegated_metadata(METADATA_DIRECTORY, delegated_paths,
                                     TARGETS_ROLE_NAME,
                                     STABLE_TARGETS_ROLE_NAME,
                                     stable_targets_role_keys)

  # Update the parent role's metadata file.  The parent role's delegation
  # field must be updated with the newly created delegated role.
  signercli._update_parent_metadata(METADATA_DIRECTORY,
                                    STABLE_TARGETS_ROLE_NAME,
                                    stable_targets_role_keys, delegated_paths,
                                    TARGETS_ROLE_NAME, targets_role_keys)





############################# MAIN FUNCTION ###################################
if __name__ == "__main__":
  check_sanity()
  if need_delegation():
    make_delegation()





