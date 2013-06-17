#!/usr/bin/env python


"""
A simple command-line utility to determine whether the metadata for a targets
role matches its target files.

Usage:
    # Given the repository directory,
    # does the targets/simple/Django metadata match its target files?
    $ metadata_matches_data.py repository targets/simple/Django
"""


import argparse
import json
import os.path
import sys
import traceback

import tuf.formats
import tuf.hash


class MissingTargetMetadataError(Exception):
  """Denotes which target metadata is missing."""

  def __init__(self, filename):
    Exception.__init__(self)
    self.filename = filename


# TODO:
# - Check that delegating target paths of parent/delegator matches all target
# paths of full_role_name?
def metadata_matches_data(repository_directory, metadata_directory,
                          targets_directory, full_role_name):
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
      role_targets_directory = os.path.join(repository_directory, full_role_name)

      # Get the list of observed target files.
      observed_targets = []
      for dirpath, dirnames, filenames in os.walk(role_targets_directory):
        observed_targets.extend(filenames)
        # Do not recursively walk role_targets_directory.
        del dirnames[:]

      for observed_file in observed_targets:
        # Ensure that form of observed_file conforms to that of expected_file.
        # Presently, this means that they do not share the "targets/" prefix.
        observed_file = os.path.join(full_role_name, observed_file)
        observed_file = observed_file.split("targets/", 2)[1]
        # observed_file was added, so metadata has diverged from data.
        if observed_file not in expected_targets:
          matched = False
          break

    return matched


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Given a TUF repository, " + \
    "does the metadata for a targets role match its target files?")

  parser.add_argument('repository_directory', type=str, help='/path/to/repository')
  parser.add_argument('--full_role_name', type=str, help='Full role name.')

  args = parser.parse_args()

  # Assume that metadata is in /path/to/repository/metadata
  metadata_directory = os.path.join(args.repository_directory, "metadata")
  # Assume that metadata is in /path/to/repository/targets
  targets_directory = os.path.join(args.repository_directory, "targets")

  # Walk over all the metadata and targets in repository_directory.
  if args.full_role_name is None:
    for dirpath, dirnames, filenames in os.walk(targets_directory, followlinks=True):
      full_role_name = dirpath.split(args.repository_directory, 2)[1].lstrip('/')

      try:
        if not metadata_matches_data(args.repository_directory,
                                        metadata_directory, targets_directory,
                                        full_role_name):
          print("UpdateMetadata: " + full_role_name)
      except MissingTargetMetadataError as missing_target_metadata_error:
        print("MissingMetadata: " + full_role_name)

  # Focus only on the given target role.
  else:
    # Assume we exit with code 0, which means that metadata matches data.
    exit_code = 0

    try:
      matched = metadata_matches_data(args.repository_directory,
                                      metadata_directory, targets_directory,
                                      args.full_role_name)
      # (matched == True) <=> (exit_code == 0)
      # (matched == False) <=> (exit_code == 1)
      exit_code = 1 - int(matched)
    except:
      traceback.print_exc()
      # Something unexpected happened; we exit with code 2.
      exit_code = 2
    finally:
      sys.exit(exit_code)
