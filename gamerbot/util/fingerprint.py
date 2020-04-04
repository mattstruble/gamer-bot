# Copyright (c) 2020 Matt Struble. All Rights Reserved.
#
# Use is subject to license terms.
#
# Author: Matt Struble
# Date: Feb. 22 2020
import re
import sys

import numpy as np


# https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf
class Fingerprint(object):
    # base is 158 to allow non-english ascii letters to be hashed properly
    def __init__(self, kgram_len=50, window_len=100, modulo=sys.maxsize, base=158, allow_space=False):
        self.kgram_len = kgram_len
        self.window_len = window_len
        self.modulo = modulo
        self.base = base

        if allow_space:
            self.alpha_pattern = re.compile('[^a-zA-z0-9_ ]+', flags=re.MULTILINE) # only alphanumeric, underscore, and space
        else:
            self.alpha_pattern = re.compile('[^a-zA-z0-9_]+', flags=re.MULTILINE)  # only alphanumeric and underscore

        self.url_pattern = re.compile('(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])?')
        self.patterns = [self.url_pattern, self.alpha_pattern]

        # add 1 so that 'a' has some effect on the hash instead of always equating to 0
        self.ch_to_int = lambda x: ord(x) - ord('a') + 1

    def _sanitize(self, str):
        # remove urls
        sanitized = str
        for pattern in self.patterns:
            sanitized = pattern.sub('', sanitized)

        return sanitized.lower()

    def _isvalid(self, str):
        return len(str) >= self.window_len

    def _gen_kgrams(self, str):
        return [str[i:i + self.kgram_len] for i in range(len(str) - self.kgram_len+1)]

    # https://courses.csail.mit.edu/6.006/spring11/rec/rec06.pdf
    def _karp_rabin(self, prev_hash, prev_char, new_char):
        hash = (( (prev_hash - (self.ch_to_int(prev_char) * (self.base ** (self.kgram_len -1)))) * self.base) + self.ch_to_int(new_char))

        return hash % self.modulo

    def _hash(self, kgram):
        hash = 0
        for i, c in enumerate(kgram):
            hash += self.ch_to_int(c) * (self.base ** (self.kgram_len -1 - i))

        return hash % self.modulo

    def _hash_kgrams(self, kgrams):
        prev_kgram = kgrams[0]
        prev_hash = self._hash(prev_kgram)

        hashes = [prev_hash]

        for kgram in kgrams[1:]:
            hash = self._karp_rabin(prev_hash, prev_kgram[0], kgram[-1])
            hashes.append(hash)

            prev_hash = hash
            prev_kgram = kgram

        return hashes

    def _gen_fingerprints(self, hashes):
        windows = [hashes[i:i + self.window_len] for i in range(len(hashes) - self.window_len + 1)]

        fingerprints = [[-1,-1]]
        min_pos = 0
        min_val = sys.maxsize
        for i, window in enumerate(windows):
            # base search off last min position, so long as min is in winnow
            if min_pos - i <= 0:
                min_pos = 0
                start_pos = 0
                min_val = sys.maxsize
            else:
                # only need to start at the end of the window and check the newly added value if the previous min is still
                # in the winnow
                start_pos = self.window_len - 1

            for j in range(start_pos, self.window_len):
                if window[j] <= min_val: # sigmod says to use rightmost min_val
                    min_val = window[j]
                    min_pos = j+i


            # don't record the same fingerprint twice
            if fingerprints[-1][0] != min_val and fingerprints[-1][1] != min_pos:
                fingerprints.append([min_val, min_pos])

        return fingerprints[1:] # remove dummy finger print added in beginning [-1, -1]

    def generate(self, str):
        sanitized = self._sanitize(str)
        kgrams = self._gen_kgrams(sanitized)
        hashes = self._hash_kgrams(kgrams)
        fingerprints = self._gen_fingerprints(hashes)

        return fingerprints


def template_match_hashes(template_hashes, source_hashes, match_percent=0.6):
    """
    Takes in array of template fingerprint hashes, and an array of hashes to search through. Looks through the search
    array for the template, and registers a match so long as the percent of matches exceeds the provided match_percent.

    i.e:
    template = [171, 808]
    source = [1442, 2938, 1107, 171, 808, 2780, 3169, 1435]
    return = [range(3, 4)]

    template = [171, 808, 2863, 2938, 1436, 2148, 482, 178]
    source = [1279, 2393, 3570, 2055, 172, 2237, 3886, 1107, 171, 808, 2863, 2938, 176, 726, 1436, 2148, 3168, 1269, 726,
              482, 178, 3096, 337, 3096, 170, 1915, 2306, 1279, 2393, 3570, 2055, 172, 2237, 3886, 1107, 171, 808, 2863,
              2938, 176, 726, 1436, 2148, 3168, 1273, 1441, 2938, 482, 178, 3096, 2853, 1429, 1114, 1284, 3096, 2227]
    return = [range(8, 20), range(35, 48)]

    template = [171, 808, 2863, 2938, 1436, 2148, 482, 178]
    source = [1436, 2148, 1107, 171, 726, 1107, 171, 808, 2863, 2938, 1436, 2148, 482, 178]
    return = [range(6, 14)]

    :param template_prints: Searched template.
    :param source_prints: Array where the search is running.
    :param match_percent: Percent of acceptance for template to match.
    :return: Array of ranges that match the provided template in the source.
    """
    # Store staring indexes for each template hash
    template_locs = {}
    for t_hash in template_hashes:
        template_locs[t_hash] = np.where(np.array(source_hashes) == t_hash)[0]

    checked_idxs = []
    matched_ranges = []
    template_len = len(template_hashes)
    for i in range(int(template_len/2)): # only first half of template can "start" the template
        start_idxs = template_locs[template_hashes[i]]
        for start_idx in start_idxs: # Try to find a template match for each starting index
            if start_idx in checked_idxs:
                continue # don't recount already counted starts

            matched = 0
            counted = 0
            template_idx = i
            # Look for matching hashes starting from the start index, extend search range to allow for filler values
            for j in range(start_idx, min(len(source_hashes), start_idx + int(template_len * 1.8))):
                # only match if not already seen and only if comes after the current value in the template
                if source_hashes[j] in template_hashes[template_idx:] and j not in checked_idxs:
                    # update template index to force progression through the template instead of allowing multiple loops
                    template_idx = template_hashes.index(source_hashes[j], template_idx, len(template_hashes))
                    matched += 1

                counted += 1

                if source_hashes[j] == template_hashes[-1] or (source_hashes[j] == template_hashes[i] and j != start_idx):
                    break # early break for hitting end of template, or hitting another of the same start

                checked_idxs.append(j)

            # only record if both the percent matched and number of counted is greater than match_percent.
            if matched / counted >= match_percent and counted >= template_len * match_percent:
                matched_ranges.append(range(start_idx, j+1))

    return matched_ranges


def template_match_fingerprints(template_fingerprints, source_fingerprints, match_percent=0.6):
    template_hashes = [y[0] for y in sorted(template_fingerprints, key= lambda x: x[1])]
    source_hashes = [y[0] for y in sorted(source_fingerprints, key= lambda x: x[1])]

    return template_match_hashes(template_hashes, source_hashes, match_percent)
