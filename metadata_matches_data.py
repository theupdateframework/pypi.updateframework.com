#!/usr/bin/env python


"""
A simple command-line utility to determine whether the metadata for a targets
role matches its target files.

Usage:
    # Given the repository directory, does the targets/unstable metadata match
    # its target files?
    $ metadata_matches_data.py repository targets/unstable
"""


import argparse
import json
import os.path
import sys
import traceback

import tuf.formats
import tuf.hash
import tuf.repo.signerlib as signerlib


class MissingTargetMetadataError(Exception):
  """Denotes which target metadata is missing."""

  def __init__(self, filename):
    Exception.__init__(self)
    self.filename = filename


# TODO:
# - Check that delegating target paths of parent/delegator matches all target
# paths of full_role_name?
def metadata_matches_data(metadata_directory, targets_directory, full_role_name,
                          files_directory, recursive_walk=False,
                          followlinks=True):
  """
  Return True if metadata matches data for the target role; False otherwise.
  """

  # Assume that metadata lives in a file specified by the full role name.
  metadata_filename = full_role_name + ".txt"
  metadata_filename = os.path.join(metadata_directory, metadata_filename)

  try:
    metadata_file = open(metadata_filename)
  except:
    raise MissingTargetMetadataError(metadata_filename)
  else:
    all_metadata = json.load(metadata_file)
    metadata_file.close()

    # TODO: Use TUF to verify that all_metadata is correctly signed.
    signed_metadata = all_metadata["signed"]
    # Check that the metadata is well-formed.
    signed_metadata = tuf.formats.TargetsFile.from_metadata(signed_metadata)
    expected_targets = signed_metadata.info["targets"]

    # We begin by assuming that everything is all right.
    matched = True

    # For expected_file in metadata, does it match the observed_file in targets?
    for expected_file in expected_targets:
      observed_file = os.path.join(targets_directory, expected_file)
      if os.path.exists(observed_file):
        # Does expected_file describe observed_file?
        expected_file_metadata = expected_targets[expected_file]

        # Compare every hash of the expected file with the equivalent hash of
        # the observed file.
        expected_file_hashes = expected_file_metadata["hashes"]
        for hash_algorithm, expected_file_digest in expected_file_hashes.iteritems():
          observed_file_digest_object = \
            tuf.hash.digest_filename(observed_file, algorithm=hash_algorithm)
          observed_file_digest = observed_file_digest_object.hexdigest()
          if observed_file_digest != expected_file_digest:
            # Metadata has probably diverged from data.
            matched = False
            break
      else:
        # expected_file was deleted, so metadata has diverged from data.
        matched = False
        break

    # For observed_file in targets, does it match the expected_file in metadata?
    if matched:
      # Get the list of observed target files.
      observed_targets = signerlib.get_targets(files_directory,
                                               recursive_walk=recursive_walk,
                                               followlinks=followlinks)

      for observed_file in observed_targets:
        # Ensure that form of observed_file conforms to that of expected_file.
        # Presently, this means that they do not share the "targets/" prefix.
        assert observed_file.startswith(targets_directory)
        observed_file = observed_file[len(targets_directory)+1:]
        # observed_file was added, so metadata has diverged from data.
        if observed_file not in expected_targets:
          matched = False
          break

    return matched


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Given a TUF repository, " + \
    "does the metadata for a targets role match its target files?")

  parser.add_argument('repository_directory', type=str,
                      help='/path/to/repository')
  parser.add_argument('full_role_name', type=str, help='Full role name.')
  parser.add_argument('files_directory', type=str,
                      help='/path/to/repository/targets(/subdirectory)?')
  parser.add_argument('recursive_walk', type=str,
                      help='Recursively walk files_directory? [Y]es/[N]o')

  args = parser.parse_args()
  repository_directory = args.repository_directory
  full_role_name = args.full_role_name
  files_directory = args.files_directory
  recursive_walk = args.recursive_walk

  repository_directory = os.path.abspath(repository_directory)
  # Assume that metadata is in /path/to/repository/metadata
  metadata_directory = os.path.join(repository_directory, "metadata")
  # Assume that metadata is in /path/to/repository/targets
  targets_directory = os.path.join(repository_directory, "targets")
  files_directory = os.path.abspath(files_directory)

  # Sanity checks.
  assert os.path.isdir(repository_directory)
  assert metadata_directory.startswith(repository_directory)
  assert os.path.isdir(metadata_directory)
  assert targets_directory.startswith(repository_directory)
  assert os.path.isdir(targets_directory)
  assert files_directory.startswith(targets_directory)
  assert os.path.isdir(files_directory)
  assert recursive_walk in ('Y', 'N')

  if recursive_walk == 'Y':
    recursive_walk = True
  else:
    recursive_walk = False

  # Focus only on the given target role.
  # Assume we exit with code 0, which means that metadata matches data.
  exit_code = 0

  try:
    matched = metadata_matches_data(metadata_directory, targets_directory,
                                    full_role_name, files_directory,
                                    recursive_walk=recursive_walk)
    # (matched == True) <=> (exit_code == 0)
    # (matched == False) <=> (exit_code == 1)
    exit_code = 1 - int(matched)
  except:
    traceback.print_exc()
    # Something unexpected happened; we exit with code 2.
    exit_code = 2
  finally:
    sys.exit(exit_code)


