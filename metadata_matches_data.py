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

import tuf.formats
import tuf.hash


def metadata_matches_data(repository_directory, full_role_name):
  """
  Return True if metadata matches data for the target role; False otherwise.
  """

  # Assume that metadata is in /path/to/repository/metadata
  metadata_directory = os.path.join(repository_directory, "metadata")
  # Assume that metadata is in /path/to/repository/targets
  targets_directory = os.path.join(repository_directory, "targets")

  # Assume that metadata lives in a file specified by the full role name.
  metadata_filename = full_role_name + ".txt"
  metadata_filename = os.path.join(metadata_directory, metadata_filename)

  with open(metadata_filename) as metadata_file:
    all_metadata = json.load(metadata_file)
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
      else:
        # expected_file was deleted, so metadata has diverged from data.
        matched = False

    # For observed_file in targets, does it match the expected_file in metadata?
    if matched:
      role_targets_directory = os.path.join(targets_directory, full_role_name)
      observed_targets = os.listdir(role_targets_directory)
      for observed_file in observed_targets:
        # observed_file was added, so metadata has diverged from data.
        if observed_file not in expected_targets:
          matched = False

    return matched


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Given a TUF repository, " + \
    "does the metadata for a targets role match its target files?")

  parser.add_argument('repository_directory', type=str, help='/path/to/repository')
  parser.add_argument('full_role_name', type=str, help='Full role name.')

  args = parser.parse_args()

  # Assume we exit with code 0, which means that metadata matches data.
  exit_code = 0
  try:
    matched = metadata_matches_data(args.repository_directory, args.full_role_name)
    # (matched == True) <=> (exit_code == 0)
    # (matched == False) <=> (exit_code == 1)
    exit_code = 1 - int(matched)
  except:
    # Something unexpected happened; we exit with code 2.
    exit_code = 2
  finally:
    sys.exit(exit_code)
