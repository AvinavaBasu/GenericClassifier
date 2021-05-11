"""
Defines various features and utilities to be used in ML models
"""

import re
from collections import Counter, OrderedDict
import pandas as pd
from sklearn.base import TransformerMixin
import numpy as np


def identity_analyzer(x):
    """
    This is verbose but a lambda can't be serialized
    """
    return x


class NonparametricTransformer(TransformerMixin):
    """ A handy base class for transformers that do not have any parameters to fit. """
    def fit(self, x, y=None):
        """ No fitting is needed here. """
        return self


class WordSplitter(NonparametricTransformer):
    """ Split words that are linked together by slashes, dots, etc. """
    def transform(self, strings):
        """ Split words in the given list, returns a list of lists """
        new_strings = []
        for s in strings:
            new_parts = []
            for part in s.split():
                m_dot = re.match(r'^([a-z]\w{2,}\.){2,}$', part.lower())
                m_slash = re.match(r'^([a-z]{3,}\.?)(/[a-z]{3,}\.?)+$', part.lower())
                if m_dot:
                    new_parts.extend(re.findall(r'\w+\.', part))
                elif m_slash:
                    new_parts.extend(re.findall(r'\w+\.?', part))
                else:
                    new_parts.append(part)
            new_strings.append(' '.join(new_parts))
        return new_strings


class TokenTranslator(NonparametricTransformer):
    """
    Translate all matching tokens in a string according to a given dictionary. Tokens
    that do not match any entry of the dictionary are left intact. This transformer
    is mainly for translating known abbreviations (e.g. Sci. = Science).
    """
    def __init__(self, dict_path):
        df = pd.read_csv(dict_path, dtype=str, na_values='')
        self.dictionary = {row['abbreviation']: row['replacement'] for _, row in df.iterrows()}

    def transform(self, strings):
        """ For a list of strings, return new strings with matching tokens translated. """
        new_strings = []
        for s in strings:
            parts = s.split()
            for i, part in enumerate(parts):
                part = part.lower()
                if part in self.dictionary:
                    parts[i] = self.dictionary[part]
            new_strings.append(' '.join(parts))
        return new_strings


class CharLenFeature(NonparametricTransformer):
    """ A trasnformer that turns a string into its length in characters """

    def transform(self, strings):
        """ Recieves a list of strings, returns their lengths in characters """
        return [[len(s)] for s in strings]


class WordLenFeature(NonparametricTransformer):
    """ A transformer that turns a string into its length in tokens """

    def transform(self, strings):
        """ Return the approximate length in tokens of strings """
        # assuming words are separated by one space only
        # this approximation is to cut down running time
        return [[s.count(' ')+1] for s in strings]


def _count_all_caps(l):
    return sum(w.isupper() for w in l)


def _freq_all_caps(l):
    if len(l) > 0:
        return _count_all_caps(l) / float(len(l))
    return 0.0


class FreqCapitalsFeature(NonparametricTransformer):
    """
    A transformer that turns a string into the frequency of capital characters.
    Many capital letters indicate the existence of a proper name therefore
    of a specific entity (SPE).
    For example: "ABC Hospital" --> 4/11
    """

    def transform(self, strings):
        """ Receives a list of strings, returns a list of capital frequency """
        return [[_freq_all_caps(s)] for s in strings]


class FreqAllCapsFeature(NonparametricTransformer):
    """ A transformer that returns the ratio of all-caps tokens compared to all tokens """

    def transform(self, strings):
        """ Returns the frequency of all-caps tokens in the given strings """
        return [[_freq_all_caps(s.split())] for s in strings]


class WordFrequencyFeatures(NonparametricTransformer):
    """
    Return the specified statistics of the frequency of tokens as recorded in a table.
    The transformer can return the min, max, mean frequency of tokens in an org-string,
    or any combination of those stats.
    """

    def __init__(self, freq, stats=('min', 'max', 'mean')):
        self.freq = freq
        assert all(s in ('min', 'max', 'mean') for s in stats)
        self.stats = stats

    def _compute_stats(self, arr):
        return (([arr.min()] if 'min' in self.stats else []) +
                ([arr.max()] if 'max' in self.stats else []) +
                ([arr.mean()] if 'mean' in self.stats else []))

    def _normalize(self, s):
        # avoid using regular expression to cut down running time
        return s.replace('(', '').replace(')', '').replace(',', '')

    def transform(self, strings):
        """ Turns a list of strings into a list of tuples composed of frequency statistics """
        tokens = ([t.lower() for t in self._normalize(s).split()] for s in strings)
        sentinent = 1 # so that the list is never empty
        freqs = (np.array([sentinent] + [self.freq[t] for t in ts]) for ts in tokens)
        minmax = [self._compute_stats(fs) for fs in freqs]
        return minmax


class WordListTagger(TransformerMixin):
    """ Turns tokens in a string into a list of tags, one for each match in a dictionary. """

    def __init__(self, word2tag, num_top_freq_words, default_tag):
        self.word2tag = word2tag
        self.num_top_freq_words = num_top_freq_words
        self.default_tag = default_tag
        self.top_freq_words = OrderedDict()

    def _collapse(self, list_):
        if not list_:
            return []
        new_list = [list_[0]]
        for prev, curr in zip(list_[:-1], list_[1:]):
            if curr != prev:
                new_list.append(curr)
        return new_list

    def _map_word(self, w):
        if w in self.top_freq_words:
            return w
        if w in self.word2tag:
            return self.word2tag[w]
        return self.default_tag

    def fit(self, strings, y=None):
        """ Measure and remember necessary statistics based on the given dataset """
        self.top_freq_words.clear()
        if self.num_top_freq_words > 0:
            tokens_flat = (t for s in strings for t in s.lower().split())
            tokens_counts = Counter(tokens_flat)
            tokens_ordered = (v for v in tokens_counts.most_common())
            self.top_freq_words.update(tokens_ordered[:self.num_top_freq_words])
        return self

    def transform(self, strings):
        """ Transforms strings in the given list into new strings that contain tags """
        tokens = ((t for t in s.lower().split()) for s in strings)
        tags = ([self._map_word(t) for t in ts] for ts in tokens)
        tags = [self._collapse(ts) for ts in tags]
        return tags


class StringConcat(NonparametricTransformer):
    """ Turns lists of strings into strings by concatenation """

    def transform(self, strings):
        """
        Turns lists of strings into strings by concatenation.

        :param list(list(str)) strings: lists of strings to transform
        :return: one list of strings
        """
        return [['_'.join(s)] for s in strings]


class RuleFeatures(NonparametricTransformer):
    """ Processes the output of a rule-based classifier into a form suitable for scikit-learn """

    def transform(self, arr):
        """ 
        Processes the output of a rule-based classifier into a form suitable for scikit-learn 
        """
        return [row for row in arr]


class ItemSelector(NonparametricTransformer):
    """ A transformer that selects one item in a tuple """

    def __init__(self, idx):
        self.idx = idx

    def transform(self, tuple_):
        """ Returns the item specified in __init__ """
        return tuple_[self.idx]
