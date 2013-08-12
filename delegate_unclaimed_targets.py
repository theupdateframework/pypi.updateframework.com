#!/usr/bin/env python





from __future__ import division

import datetime
import os.path

from tuf.log import logger

import tuf.hash as hasher
import tuf.repo.signercli as signercli
import tuf.repo.signerlib as signerlib

import delegate





HASH_FUNCTION = 'sha256'
NUMBER_OF_BINS = 1024
# Strip the '0x' from the Python hex representation.
PREFIX_LENGTH =  len(hex(NUMBER_OF_BINS-1)[2:])
MAX_NUMBER_OF_BINS = 16**PREFIX_LENGTH





def update_unclaimed_targets():
  # For simplicity, ensure that we can evenly distribute MAX_NUMBER_OF_BINS
  # over NUMBER_OF_BINS.
  assert MAX_NUMBER_OF_BINS % NUMBER_OF_BINS == 0

  # Get all possible targets.
  absolute_delegated_paths = signerlib.get_targets(delegate.TARGETS_DIRECTORY,
                                                   recursive_walk=True,
                                                   followlinks=True)

  logger.info('There are {0} total PyPI targets.'.format(len(
              absolute_delegated_paths)))


  # Record the absolute delegated paths that fall into each bin.
  absolute_delegated_paths_in_bin = \
    {bin_index: [] for bin_index in xrange(MAX_NUMBER_OF_BINS)}

  # Assign every path to its bin.
  for absolute_delegated_path in absolute_delegated_paths:
    assert absolute_delegated_path.startswith(delegate.TARGETS_DIRECTORY+'/')

    relative_delegated_path = \
      absolute_delegated_path[len(delegate.TARGETS_DIRECTORY)+1:]
    relative_delegated_path_digest = hasher.digest(algorithm=HASH_FUNCTION)
    relative_delegated_path_digest.update(relative_delegated_path)
    relative_delegated_path_hash = relative_delegated_path_digest.hexdigest()
    relative_delegated_path_hash_prefix = \
      relative_delegated_path_hash[:PREFIX_LENGTH]

    # Convert a base-16 (hex) number to a base-10 (dec) number.
    bin_index = int(relative_delegated_path_hash_prefix, 16)
    assert bin_index > -1
    assert bin_index < MAX_NUMBER_OF_BINS

    absolute_delegated_paths_in_bin[bin_index] += [absolute_delegated_path] 


  # Delegate every target to the "unclaimed" targets role.
  # Presently, every target falls under the "simple/" and "packages/"
  # directories.
  unclaimed_relative_delegated_paths = ["targets/simple/", "targets/packages/"]

  # TODO: Update delegatee only if necessary to do so.
  unclaimed_relative_target_paths = []
  delegate.update_targets_metadata(delegate.UNCLAIMED_TARGETS_ROLE_NAME,
                                   unclaimed_relative_target_paths,
                                   datetime.timedelta(days=365))

  # TODO: Comment on shared keys, and why this must come after
  # update_targets_metadata.
  unclaimed_targets_role_keys = \
    delegate.get_keys_for_targets_role(delegate.UNCLAIMED_TARGETS_ROLE_NAME)

  delegate.make_delegation(delegate.TARGETS_ROLE_NAME,
                           delegate.UNCLAIMED_TARGETS_ROLE_NAME,
                           relative_delegated_paths=unclaimed_relative_delegated_paths)

  # Delegate from the "unclaimed" targets role to each bin.

  bin_offset = MAX_NUMBER_OF_BINS // NUMBER_OF_BINS
  for global_bin_index in xrange(0, MAX_NUMBER_OF_BINS, bin_offset):
    # The bin index in hex padded from the left with zeroes for up to the
    # PREFIX_LENGTH.
    global_bin_index_in_hex = hex(global_bin_index)[2:].zfill(PREFIX_LENGTH)

    relative_binned_targets_role_name = global_bin_index_in_hex
    absolute_binned_targets_role_name = \
      os.path.join(delegate.UNCLAIMED_TARGETS_ROLE_NAME,
                   relative_binned_targets_role_name)
    absolute_delegated_paths_in_this_bin = []
    path_hash_prefixes = []

    for local_bin_index in xrange(global_bin_index,
                                  global_bin_index+bin_offset):
      absolute_delegated_paths_in_this_bin.extend(
        absolute_delegated_paths_in_bin[local_bin_index])
      local_bin_index_in_hex = hex(local_bin_index)[2:].zfill(PREFIX_LENGTH)
      path_hash_prefixes.append(local_bin_index_in_hex)

    relative_delegated_paths_in_this_bin = \
      delegate.get_relative_delegated_paths(absolute_delegated_paths_in_this_bin)

    # TODO: Update delegator only if necessary to do so.
    delegate.update_delegator_metadata(delegate.UNCLAIMED_TARGETS_ROLE_NAME,
                                       relative_binned_targets_role_name,
                                       unclaimed_targets_role_keys,
                                       unclaimed_targets_role_keys,
                                       path_hash_prefixes=path_hash_prefixes)

    logger.info('Delegated from {0} to {1}'.format(
                delegate.UNCLAIMED_TARGETS_ROLE_NAME,
                absolute_binned_targets_role_name))

    # TODO: Update delegatee only if necessary to do so.
    delegate.update_targets_metadata(absolute_binned_targets_role_name,
                                     relative_delegated_paths_in_this_bin,
                                     datetime.timedelta(days=3),
                                     targets_role_keys=unclaimed_targets_role_keys)

    logger.info('Wrote {0}'.format(absolute_binned_targets_role_name))

  # Compress "unclaimed" targets role metadata.
  unclaimed_targets_role_filename = \
    os.path.join(delegate.METADATA_DIRECTORY,
                 '{0}.txt'.format(delegate.UNCLAIMED_TARGETS_ROLE_NAME))
  delegate.compress_metadata(unclaimed_targets_role_filename)

  # Compute statistics and check sanity.

  expected_number_of_paths_per_bin = \
    len(absolute_delegated_paths)/MAX_NUMBER_OF_BINS

  observed_number_of_paths_in_all_bins = \
    sum((len(paths) for paths in absolute_delegated_paths_in_bin.values()))

  observed_number_of_bins = len(absolute_delegated_paths_in_bin)

  observed_number_of_paths_per_bin = \
    observed_number_of_paths_in_all_bins/observed_number_of_bins

  # Each of the delegated paths must have been assigned to a bin.
  assert observed_number_of_paths_in_all_bins == len(absolute_delegated_paths)
  # The observed number of bins must be equal to the expected number of bins.
  assert observed_number_of_bins == MAX_NUMBER_OF_BINS

  logger.info('Expected number of paths per bin: {0}'.format(
              expected_number_of_paths_per_bin))
  logger.info('Observed number of paths per bin: {0}'.format(
              observed_number_of_paths_per_bin))





if __name__ == '__main__':
  update_unclaimed_targets()





