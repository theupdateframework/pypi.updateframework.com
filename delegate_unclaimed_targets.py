#!/usr/bin/env python





from __future__ import division

import os.path

import tuf.hash as hasher
import tuf.repo.signercli as signercli
import tuf.repo.signerlib as signerlib

from tuf.log import logger

import delegate





HASH_FUNCTION = 'sha256'
NUMBER_OF_BINS = 4096
# Strip the '0x' from the Python hex representation.
PREFIX_LENGTH =  len(hex(NUMBER_OF_BINS-1)[2:])





def make_delegation():
  # Get all possible targets.
  absolute_delegated_paths = signerlib.get_targets(delegate.TARGETS_DIRECTORY,
                                                   recursive_walk=True,
                                                   followlinks=True)

  logger.info('There are {0} total PyPI targets.'.format(len(
              absolute_delegated_paths)))


  # Record the absolute delegated paths that fall into each bin.
  absolute_delegated_paths_in_bin = \
    {bin_index: [] for bin_index in xrange(NUMBER_OF_BINS)}

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
    assert bin_index < NUMBER_OF_BINS

    absolute_delegated_paths_in_bin[bin_index] += [absolute_delegated_path] 


  # FIXME: Delegate every target to the "unclaimed" targets role.
  # Presently, the master branch does not recognize directories yet.
  # TODO: This needs to happen only once.
  unclaimed_relative_delegated_paths = []
  delegate.make_delegation(delegate.TARGETS_ROLE_NAME,
                           delegate.UNCLAIMED_TARGETS_ROLE_NAME,
                           unclaimed_relative_delegated_paths)

  # Delagate from the "unclaimed" targets role to each bin.
  for bin_index in xrange(NUMBER_OF_BINS):
    # The bin index in hex padded from the left with zeroes for up to the
    # PREFIX_LENGTH.
    bin_index_in_hex = hex(bin_index)[2:].zfill(PREFIX_LENGTH) 
    absolute_delegated_paths_in_this_bin = \
      absolute_delegated_paths_in_bin[bin_index]
    relative_delegated_paths_in_this_bin = \
      delegate.get_relative_delegated_paths(absolute_delegated_paths_in_this_bin)
    relative_binned_targets_role_name = bin_index_in_hex
    unclaimed_targets_role_keys = \
      delegate.get_keys_for_targets_role(delegate.UNCLAIMED_TARGETS_ROLE_NAME)

    # Write and sign the delegatee metadata file.
    # TODO: Update delegatee only if necessary to do so.
    signercli._make_delegated_metadata(delegate.METADATA_DIRECTORY,
                                       relative_delegated_paths_in_this_bin,
                                       delegate.UNCLAIMED_TARGETS_ROLE_NAME,
                                       relative_binned_targets_role_name,
                                       unclaimed_targets_role_keys)

    # Write and sign the delegator metadata file.
    # TODO: This needs to happen only once.
    signercli._update_parent_metadata(delegate.METADATA_DIRECTORY,
                                      relative_binned_targets_role_name,
                                      unclaimed_targets_role_keys,
                                      relative_delegated_paths_in_this_bin,
                                      delegate.UNCLAIMED_TARGETS_ROLE_NAME,
                                      unclaimed_targets_role_keys,
                                      path_hash_prefix=bin_index_in_hex)

    logger.info('Delegated from {0} to {1}'.format(
                delegate.UNCLAIMED_TARGETS_ROLE_NAME,
                relative_binned_targets_role_name))


  # Compute statistics and check sanity.

  expected_number_of_paths_per_bin = \
    len(absolute_delegated_paths)/NUMBER_OF_BINS

  observed_number_of_paths_in_all_bins = \
    sum(absolute_delegated_paths_in_bin.values())

  observed_number_of_bins = len(absolute_delegated_paths_in_bin)

  observed_number_of_paths_per_bin = \
    observed_number_of_paths_in_all_bins/observed_number_of_bins

  # Each of the delegated paths must have been assigned to a bin.
  assert observed_number_of_paths_in_all_bins == len(absolute_delegated_paths)
  # The observed number of bins must be equal to the expected number of bins.
  assert observed_number_of_bins == NUMBER_OF_BINS

  logger.info('Expected number of paths per bin: {0}'.format(
              expected_number_of_paths_per_bin))
  logger.info('Observed number of paths per bin: {0}'.format(
              observed_number_of_paths_per_bin))





if __name__ == '__main__':
  make_delegation()





