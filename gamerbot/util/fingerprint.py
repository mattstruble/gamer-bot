# Copyright (c) 2020 Matt Struble. All Rights Reserved.
#
# Use is subject to license terms.
#
# Author: Matt Struble
# Date: Feb. 22 2020
import re
import sys


# https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf
class Fingerprint(object):
    # base is 158 to allow non-english ascii letters to be hashed properly
    def __init__(self, kgram_len=50, window_len=100, modulo=sys.maxsize, base=158):
        self.kgram_len = kgram_len
        self.window_len = window_len
        self.modulo = modulo
        self.base = base

        self.alpha_pattern = re.compile('[\W\d_]+', flags=re.MULTILINE) # only alphanumeric and underscore
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
