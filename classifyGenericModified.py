#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Implementing various versions of generic classifier: a rule-based solution as it was before 2020,
an extension with multilingual word lists, and a machine learning-powered solution.
"""

import re
from glob import glob
from time import time
import unicodedata
import logging
import joblib
from joblib import Parallel, delayed
import numpy as np
import scipy


class OriginalConfig(object):
    """
    The location of resources as it was before 2020.
    """
    typeDictFile = "dicts/typesDict.txt"
    subjectDictFile = "dicts/subjectsDict-new.txt"
    subjectModifierDictFile = "dicts/subjectModifiersDict.txt"
    orgModifierDictFile = "dicts/orgModifiersDict.txt"
    connectorsDictFile = "dicts/connectorsDict.txt"
    wordEndingsDictFile = "dicts/wordEndingsDict.txt"
    whiteListFile = "dicts/whiteListDict.txt"
    blackListFile = "dicts/blackListDict.txt"
    commonDictFile = 'dicts/commonSubjectsDict.txt'
    allLocDictFile = 'dicts/allLocDict.txt'
    SWDictFile = 'dicts/sw_dict.txt'
    # translation of company names doesn't make sense so I'll use the original list only
    CNDictFile = 'dicts/companyNames.txt'
    univDictFile = 'dicts/univKeywords.txt'
    CSDictFile = 'dicts/companySuffixes.txt'
    CTDictFile = 'dicts/companyTypes.txt'
    acronym_whitelist_path = 'dicts/acronym_whitelist.txt'
    expandedSubjectDictFile = 'dicts/subject.txt'


class MultilingualConfig(object):
    """
    The location of resources including translations into multiple languages.
    """
    typeDictFile = "dicts/typesDict.*txt"
    subjectDictFile = "dicts/subjectsDict-new.*txt"
    subjectModifierDictFile = "dicts/subjectModifiersDict.*txt"
    orgModifierDictFile = "dicts/orgModifiersDict.*txt"
    connectorsDictFile = "dicts/connectorsDict.*txt"
    wordEndingsDictFile = "dicts/wordEndingsDict.*txt"
    whiteListFile = "dicts/whiteListDict.txt"
    blackListFile = "dicts/blackListDict.txt"
    commonDictFile = 'dicts/commonSubjectsDict.*txt'
    allLocDictFile = 'dicts/allLocDict.txt'
    SWDictFile = 'dicts/sw_dict.txt'
    # translation of company names doesn't make sense so I'll use the original list only
    CNDictFile = 'dicts/companyNames.txt'
    univDictFile = 'dicts/univKeywords.*txt'
    CSDictFile = 'dicts/companySuffixes.*txt'
    CTDictFile = 'dicts/companyTypes.*txt'
    acronym_whitelist_path = 'dicts/acronym_whitelist.txt'
    expandedSubjectDictFile = 'dicts/subject.txt'


# this should happend out of a function (and therefore loops)
_pattern_entities = re.compile(r"\&[\#x]*[0-9A-Za-z]+;")
_pattern_andAmp = re.compile(r"\s&|&amp;\s")
_pattern_d = re.compile(" d'")
_pattern_punc = re.compile(r"[^a-zA-Z0-9\s]")
_pattern_space = re.compile(r"\s+")
_pattern_latin_numbers = re.compile(r"\b(I|II|III|IV|V|VI|VII|VIII|IX|X"
                                    r"|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX)$")
_pattern_bullet = re.compile(r"^(\(?[a-zA-Z0-9][\)\.]?|\d{2}[\)\.])\s+")
_pattern_startAnd = re.compile(r"^\s?and ", flags=re.I)
_pattern_startThe = re.compile(r"^\s?(from )?the ", flags=re.I)
_pattern_startNumbering = re.compile(r"^(1st|2nd|3rd|4th|first|second|third|fourth)\s", flags=re.I)
_pattern_endNumbering = re.compile(" ([1-9]|i|ii|iii|iv|v|a|b|c)$", flags=re.I)
_pattern_affil = re.compile(r"^affiliated\s", flags=re.I)
_pattern_capitalized = re.compile(r'^[A-Z\.\,]+$')
_pattern_in_parenthese = re.compile(r'.+\(([A-Z\.\s]+)\)$')
_ands = '(?:and|&|y|und|e|og|i|και|ja|et|és|en|ból|ve)'
_ofs = '(?:of|de|des|der|di|fur|fr|for|für|voor|in|zu|és)'
_ins = '(?:in|a|op|zu)'
_pattern_subj_and = re.compile(r"(\S+) %s (\S+) (.+)$" % _ands)  # X and Y <subj>
_pattern_subj_and2 = re.compile(r"(\S+) (\S+) %s (\S+) (.+)$" % _ands)  # X, Y and Z <subj>
_pattern_two_match = re.compile("(.+?) %s (.+)$" % _ands)
_pattern_three_match = re.compile("(.+) %s (.+) %s (.+)$" % (_ands, _ands))
_pattern_zipcode_us = re.compile(r'\w\w,\s+[0-9]{5}(?:-[0-9]{4})?')


def removeBullet(name):
    """ Remove list enumeration (e.g. "1.", "a.") """
    name = _pattern_bullet.sub("", name)
    return name


def removeAnd(name):
    """ Remove the word "and" """
    name = _pattern_startAnd.sub("", name)
    return name


def removeThe(name):
    """ Remove the words "the" and "from the" """
    name = _pattern_startThe.sub("", name)
    return name


def removeNumbering(name):
    """ Remove enumeration ("1", "i", "ii", etc.) """
    name = _pattern_startNumbering.sub("", name)
    name = _pattern_endNumbering.sub("", name)
    return name


def removeAffiliated(name):
    """ Remove "affiliated" """
    name = _pattern_affil.sub("", name)
    return name


def normalizeToken(tok):
    """
    Normalize a token slightly: if it's all-caps, let it be,
    otherwise, convert to lower case.
    """
    if _pattern_capitalized.match(tok):
        return tok
    else:
        return tok.lower()


# normalize name
# *** should do something smarter with entities
def normalizeName(name):
    """
    Normalize names by removing special characters and turn characters
    into lower case when appropriate.
    """
    name = unicodedata.normalize('NFC', name)
    name = ' '.join(normalizeToken(k) for k in name.split())
    name = _pattern_entities.sub("", name)
    name = _pattern_andAmp.sub(" and ", name)
    name = _pattern_d.sub(" de ", name)
    name = _pattern_punc.sub("", name)
    name = _pattern_space.sub(" ", name)
    return name.strip()


def generateApproxDict(terms):
    """
    Generates all Levenshtein distance 1 variants of the terms in
    'terms', but only for terms of at least minLength characters.
    Purpose is to have a fixed such dictionary that new terms
    can be compared to with a simple lookup.
    The universe of allowable characters is [a-z0-9\\s].

    Note: the input and output 'dictionaries' here are python sets, not
    python dicts.
    """
    smallLetters = list(map(chr, range(ord('a'), ord('z') + 1)))
    # bigLetters   = map(chr, range(ord('A'), ord('Z')+1) )
    digits = list(map(chr, range(ord('0'), ord('9') + 1)))
    universe = smallLetters + digits + [' ']
    # universe = smallLetters + bigLetters + digits + [' ']

    minLength = 5
    res = set()
    for term in tqdm(terms, desc="generating approximate dict", position=0, leave=True):
        res.add(term)
        if len(term) < minLength:
            continue

        for pos in range(len(term)):
            res.add(term[0:pos] + term[pos + 1:])  # delete character
            for c in universe:
                if c != term[pos]:
                    res.add(term[0:pos] + c + term[pos + 1:])  # change character
                res.add(term[0:pos] + c + term[pos:])  # insert character
        for c in universe:
            res.add(term + c)  # insert character at end

    return res


def loadDict(path_patterns):
    """
    Load word lists from a list of file paths (possibly with wildcards) into a dictionary.
    Note: this 'dictionary' is a python set, not a dict.
    """
    paths = [p for path_pattern in path_patterns for p in glob(path_pattern)]
    assert len(paths) > 0, "No file found for %s" % path_patterns
    res = set()
    for path in paths:
        with open(path, 'r', encoding='utf-8') as f:
            res.update(normalizeName(line) for line in f if line != '\n')
    return res


def isSingleSubject(s, subjects, modifiers):
    """
    Check if a string is a single subject (e.g. physics)

    :param str s: an org-string or a part of an org-string
    :param set subjects: a collection of known subject words
    :param set modifiers: a collection of known modifiers
    """
    if s in subjects:
        return True

    m = re.match(r"(\S+)\s(.+)$", s)
    if m is not None:
        mod = m.group(1)
        tail = m.group(2)
        if isModifier(mod, modifiers) and isSingleSubject(tail, subjects, modifiers):
            return True

    return False


def isSubjectOrg(org, subjects):
    """ Check if an org-string is in the list of subjects """
    return org in subjects


def isCompoundModifiedSubject(s, subjects, modifiers):
    """
    Check if a string is a compound of subjects.
    For example: Experimental and Theoretical Physics
    Assumption is each modifier (except possibly the last) is a single token

    :param str s: an org string or part of an org string
    :param set subjects: a collection of known subject words
    :param set modifiers: a collection of known modifiers
    """
    m = _pattern_subj_and.match(s)
    if m is not None:
        X = m.group(1)
        Y = m.group(3)
        tail = m.group(4)
        if isModifier(X, modifiers) \
                and isModifier(Y, modifiers) \
                and isSingleSubject(tail, subjects, modifiers):
            return True

    m = _pattern_subj_and2.match(s)
    if m is not None:
        X = m.group(1)
        Y = m.group(2)
        Z = m.group(4)
        tail = m.group(5)
        if isModifier(X, modifiers) \
                and isModifier(Y, modifiers) \
                and isModifier(Z, modifiers) \
                and isSingleSubject(tail, subjects, modifiers):
            return True

    return False


def isSubject(s, subjects, modifiers):
    """
    Check if a string is a subject, either single or compound.
    For example: Experimental and Theoretical Physics
    Assumption is each modifier (except possibly the last) is a single token

    :param str s: an org string or part of an org string
    :param set subjects: a collection of known subject words
    :param set modifiers: a collection of known modifiers
    """
    if isSingleSubject(s, subjects, modifiers):
        return True

    if isCompoundModifiedSubject(s, subjects, modifiers):
        return True

    # X and Y
    twoMatch = _pattern_two_match.match(s)
    if twoMatch is not None:
        X = twoMatch.group(1)
        Y = twoMatch.group(3)
        if isSingleSubject(X, subjects, modifiers) and isSingleSubject(Y, subjects, modifiers):
            return True

    # X and Y and Z
    threeMatch = _pattern_three_match.match(s)
    if threeMatch is not None:
        X = threeMatch.group(1)
        Y = threeMatch.group(3)
        Z = threeMatch.group(5)
        if isSingleSubject(X, subjects, modifiers) \
                and isSingleSubject(Y, subjects, modifiers) \
                and isSingleSubject(Z, subjects, modifiers):
            return True
        if isSingleSubject(X, subjects, modifiers) \
                and isSingleSubject("%s %s %s" % (Y, _ands, Z), subjects, modifiers):
            return True
        if isSingleSubject("%s %s %s" % (X, _ands, Y), subjects, modifiers) \
                and isSingleSubject(Z, subjects, modifiers):
            return True
    # X, Y and Z
    threeMatch = re.match("(.+) (.+) %s (.+)$" % _ands, s)
    if threeMatch is not None:
        X = threeMatch.group(1)
        Y = threeMatch.group(2)
        Z = threeMatch.group(3)
        if isSingleSubject(X, subjects, modifiers) \
                and isSingleSubject(Y, subjects, modifiers)\
                and isSingleSubject(Z, subjects, modifiers):
            return True

    return False


def isType(s, types):
    """ Check if a string is in a list of known types """
    return s in types


def isModifier(s, modifiers):
    """ Check if a string is in a list of known modifiers """
    return s in modifiers


def extract_acronyms(org):
    """ Extract acronym-look-alikes from an org string """
    tokens = org.split()
    # One token all-caps or mixed, others not
    tokens = re.sub("[^a-zA-Z0-9]", " ", org).split()
    acronym_likes = []
    for token in tokens:
        if re.match("(ENT|HIV|AIDS|GI)$", token) is not None:
            continue
        if _pattern_latin_numbers.match(token) is not None:
            continue
        if token != token.upper():
            continue

        # Remove special prefixes
        token = re.sub("^[a-f0-9]", "", token)
        token = re.sub("^(Bio|Geo|Nano|Neuro|Cardio)", "", token)
        numUpper = sum([1 for x in token if x.isupper()])
        # numLower = sum([1 for x in token if x.islower()])
        if numUpper >= 3:
            acronym_likes.append(token)

    in_parenthese = _pattern_in_parenthese.findall(org)
    in_parenthese_filtered = (w for w in in_parenthese if len(w) >= 3 and
                              not _pattern_latin_numbers.match(w) and w not in acronym_likes)
    acronym_likes.extend(in_parenthese_filtered)

    return acronym_likes


def allGram(x):
    """ Generate all n-gram combinations of normalized org. """
    normNG = []
    oneg = [k.strip() for k in x.strip().split()]
    tok_len = range(len(oneg))
    for i in tok_len:
        tmp = []
        t = oneg[i]
        for j in range(i + 1, len(oneg)):
            t = t + ' ' + oneg[j]
            tmp.append(t)
        normNG += tmp
    return normNG + oneg


def cl_null(*args, **kwargs):
    """ Always returns None, to be used as a placeholder when a rule is disabled. """
    return None


class ExperimentalClassifier(object):
    """
    A configurable and extensible generic classifier that we can use in experiments.
    """

    def __init__(self,
                 name,
                 use_multilingual_dicts=True,
                 use_acronym_rule=True,
                 use_zipcode_us_rule=True,
                 use_approx_subj_dict=False):
        """

        """
        self.name = name
        self.use_multilingual_dicts = use_multilingual_dicts
        self.dict_conf = MultilingualConfig() if self.use_multilingual_dicts else OriginalConfig()
        self.use_approx_subj_dict = use_approx_subj_dict
        self._init_dicts()
        self.classification_functions = [
            self.cl_empty, self.cl_org_department1,
            self.cl_org_department2, self.cl_expanded_subject,
            self.cl_location, self.cl_cn, self.cl_company_types, self.cl_university,
            self.cl_company, self.cl_zipcode_us if use_zipcode_us_rule else cl_null,
            self.cl_department1, self.cl_department2, self.cl_department3, self.cl_department4,
            self.cl_department5, self.cl_department6, self.cl_department7, self.cl_department8,
            self.cl_subj, self.cl_type, self.cl_central, self.cl_hospital,
            self.cl_bag_of_known_words, self.cl_bag_of_known_words2,
            self.cl_acronym if use_acronym_rule else cl_null, self.cl_default
        ]

    def _init_dicts(self):
        print("Loading dictionary...")
        start_sec = time()
        conf = self.dict_conf
        self.typeDict = loadDict([conf.typeDictFile])
        self.subjectDict = loadDict([conf.subjectDictFile, conf.subjectModifierDictFile])
        self.commonSubjectsDict = loadDict([conf.commonDictFile])
        self.subjModDict = loadDict([conf.subjectModifierDictFile])
        self.orgModDict = loadDict([conf.orgModifierDictFile])
        self.wordEndingsDict = loadDict([conf.wordEndingsDictFile])
        self.whiteList = loadDict([conf.whiteListFile])
        self.blackList = loadDict([conf.blackListFile])
        self.allLoc = loadDict([conf.allLocDictFile])
        if self.use_approx_subj_dict:
            self.subjApproxDict = generateApproxDict(self.subjectDict)
        else:
            self.subjApproxDict = self.subjectDict
        self.sw = loadDict([conf.SWDictFile])
        self.cn = loadDict([conf.CNDictFile])
        self.univ = loadDict([conf.univDictFile])
        self.companySuffixes = loadDict([conf.CSDictFile])
        self.acronym_whitelist = loadDict([conf.acronym_whitelist_path])
        self.companyTypes = loadDict([conf.CTDictFile])
        d = loadDict([conf.expandedSubjectDictFile])
        self.expandedSubjectDict = set(t.lower() for t in d)
        print("Loading dictionary done in %.2f sec." % (time() - start_sec))

    def __getstate__(self):
        state = dict(self.__dict__)
        del state['subjApproxDict']
        return state

    def __setstate__(self, state):
        self.__dict__ = state
        if self.use_approx_subj_dict:
            self.subjApproxDict = generateApproxDict(self.subjectDict) # pylint: disable=attribute-defined-outside-init
        else:
            self.subjApproxDict = self.subjectDict # pylint: disable=attribute-defined-outside-init

    def classifyOrg(self, org):
        """
        Classify one orgString into either generic or specific.

        :param str org: an org string (e.g. "Department of Physics")
        :return: either "GEN" (generic) or "SPE" (specific)
        """
        org, norm, norm_no_sw = self.preprocess(org)
        if norm_no_sw in self.whiteList:
            return "GEN"
        if norm_no_sw in self.blackList:
            return "SPE"
        predictions = map(lambda f: f(org, norm, norm_no_sw), self.classification_functions)
        return next(item for item in predictions if item is not None)

    def preprocess(self, org):
        """
        Compute some transformations of the org-strings that are used in various rules.
        Returns a tuple: (the original org-string, normalized org-string,
        normalized org-string without stop words)
        """
        norm = normalizeName(org)
        norm = removeBullet(norm)
        norm = removeAnd(norm)
        norm = removeThe(norm)
        norm = removeNumbering(norm)
        norm = removeAffiliated(norm)
        norm_no_sw = self.removeSW(norm)
        return org, norm, norm_no_sw

    def removeSW(self, name):
        """ Remove stop word """
        x = [k for k in name.split() if k not in self.sw]
        return ' '.join(x)

    def cl_empty(self, org, norm, norm_no_sw):
        """ If the org-string is empty, returns some value to avoid an error. """
        if not org:
            return 'SPE'
        return None

    def cl_expanded_subject(self, org, norm, norm_no_sw):
        """ Check the expanded subject dictionary for a match """
        if isSubjectOrg(normalizeName(org).lower(), self.expandedSubjectDict):
            return 'GEN'
        return None

    def cl_org_department1(self, org, norm, norm_no_sw):
        """ Department/Dept./Dep. of ECE/CSE/EEE/ICE/MAE """
        if re.findall(r"^Dep[a-z]*\.* %s [A-Z]{1,2}E$" % _ofs, org) != []:
            return "GEN"
        return None

    def cl_org_department2(self, org, norm, norm_no_sw):
        """ ECE/EEE/EE/CS Dep. """
        if re.findall(r"^[A-Z]{2,3} Dep[a-z]*\.*", org) != []:
            return "GEN"
        return None

    def cl_location(self, org, norm, norm_no_sw):
        """ If an org-string contain location-look-alike, returns SPE """
        if set(allGram(norm)).intersection(self.allLoc) != set():
            return "SPE"
        return None

    def cl_cn(self, org, norm, norm_no_sw):
        """ Look up in the list of known company names for a match; if found, return SPE """
        if set(allGram(norm)).intersection(self.cn) != set():
            return "SPE"
        return None

    def cl_company_types(self, org, norm, norm_no_sw):
        """ If the org-string contains a company type, returns SPE """
        if len(norm.split()) >= 2 and set(allGram(norm)).intersection(self.companyTypes):
            return "SPE"
        return None

    def cl_university(self, org, norm, norm_no_sw):
        """
        Look for university-like words (e.g. "university", "institute"). If no department is
        specified, return GEN, otherwise returns SPE.
        """
        if len(norm.split()) >= 2 and set(allGram(norm)).intersection(self.univ) != set():
            if set(allGram(norm)).intersection(['Department', 'Dep.']) != set():
                return "GEN"
            else:
                return "SPE"
        return None

    def cl_company(self, org, norm, norm_no_sw):
        """ Returns SPE if the org-string looks like a company name """
        for i in self.companySuffixes:
            if re.findall(r'^[a-zA-Z]+\s' + i + '$', org) != []:
                return "SPE"
        return None

    def cl_department1(self, org, norm, norm_no_sw):
        """ ECE/CSE/EEE/ICE/MAE Department/Dept./Dep. """
        if re.findall(r"^[A-Z]{1,2}E Dep[a-z]*\.*$", org) != []:
            return "GEN"
        return None

    def cl_acronym(self, org, norm, norm_no_sw):
        """ Acronyms or org-strings containing acronyms are often specific """
        if len(org.split()) == 1 and org not in self.acronym_whitelist:
            # Check if single token, mixed case, not title/camel-case
            if (org != org.upper()) and (org != org.lower()) and (not org.istitle()):
                return "SPE"

            # Check if single token, all caps, not strict dict match
            if (org == org.upper()) and normalizeName(org) not in self.subjectDict:
                return "SPE"

        acronym = ' '.join(extract_acronyms(org))
        # shorter acronyms tend to be generic and too long ones are likely misclassified
        if len(acronym) >= 4 and len(acronym) <= 12 and acronym not in self.acronym_whitelist:
            return "SPE"
        return None

    def cl_department2(self, org, norm, norm_no_sw):
        """ Department/Dept./Dep. of xyz University """
        if re.findall(r"^Dep[a-z]*\.*.+University", org) != []:
            return "SPE"
        return None

    def cl_department3(self, org, norm, norm_no_sw):
        """ Department/Dept./Dep. of xyz commonSubjects """
        m = re.match(r"([\w\.?]+) %s (.+)$" % _ofs, norm_no_sw)
        if m:
            type_, subj = m.groups()
            if isType(type_, self.typeDict) and isType(subj, self.commonSubjectsDict):
                return "GEN"
        return None

    def cl_department4(self, org, norm, norm_no_sw):
        """ Dept/College/etc of <subj> """
        m = re.match("(.+?) %s (.+)$" % _ofs, norm_no_sw)
        if m is not None:
            type_, subject = m.groups()
            if isType(type_, self.typeDict) \
                    and isSubject(subject, self.subjApproxDict, self.subjModDict):
                return "GEN"
        return None

    def cl_department5(self, org, norm, norm_no_sw):
        """ Dept/College/etc <subj> """
        m = re.match(r"(\S+) (.+)$", norm_no_sw)
        if m is not None:
            type_ = m.group(1)
            subject = m.group(2)
            if isType(type_, self.typeDict) \
                    and isSubject(subject, self.subjApproxDict, self.subjModDict):
                return "GEN"
        return None

    def cl_department6(self, org, norm, norm_no_sw):
        """ <subj> Dept/College/etc. """
        m = re.match(r"(.+) (\S+)$", norm_no_sw)
        if m is not None:
            subject = m.group(1)
            type_ = m.group(2)
            if isType(type_, self.typeDict) \
                    and isSubject(subject, self.subjApproxDict, self.subjModDict):
                return "GEN"
            if isType(type_, self.typeDict) \
                    and isModifier(subject, self.subjModDict):
                return "GEN"
        return None

    def cl_department7(self, org, norm, norm_no_sw):
        """ University <subj> Dept/College/etc. """
        m = re.match(r"(\w+) (.+) (\S+)$", norm_no_sw)
        if m is not None:
            univ, subject, type_ = m.groups()
            if isType(univ, self.univ) and isType(type_, self.typeDict):
                if isSubject(subject, self.subjApproxDict, self.subjModDict):
                    return "GEN"
                if isModifier(subject, self.subjModDict):
                    return "GEN"
        return None

    def cl_department8(self, org, norm, norm_no_sw):
        """ Department of Studies in <subj> """
        m = re.match(r"(\w+) %s \w+ %s (\S+)$" % (_ofs, _ins), org)
        if m is not None:
            type_ = m.group(1)
            subject = m.group(2).lower()
            if isType(type_, self.typeDict):
                if isSubject(subject, self.subjApproxDict, self.subjModDict):
                    return "GEN"
                if isModifier(subject, self.subjModDict):
                    return "GEN"
        return None

    def cl_subj(self, org, norm, norm_no_sw):
        """ Returns GEN if the org-string is a subject """
        if isSubject(norm_no_sw, self.subjApproxDict, self.subjModDict):
            return "GEN"
        return None

    def cl_type(self, org, norm, norm_no_sw):
        """ A type is generic """
        if isType(norm_no_sw, self.typeDict):
            return "GEN"
        return None

    def cl_central(self, org, norm, norm_no_sw):
        """ entral/General/Graduate/etc. <generic> """
        m = re.match(r"(\S+)\s(.+)$", norm_no_sw)
        if m is not None:
            firstToken = m.group(1)
            tail = m.group(2)
            if isModifier(firstToken, self.orgModDict) and (self.classifyOrg(tail) == "GEN"):
                return "GEN"
        return None

    def cl_zipcode_us(self, org, norm, norm_no_sw):
        """ If we can find an US zip code, return SPE """
        if _pattern_zipcode_us.search(org):
            return "SPE"
        return None

    # LOWER CONFIDENCE MATCHES

    def cl_hospital(self, org, norm, norm_no_sw):
        """ Stricter pattern but with unknown subject: Dept/College/etc of <subj> """
        m = re.match(r"(.+) %s (\S+)$" % _ofs, norm_no_sw)
        if m is not None:
            type_ = m.group(1)
            if (re.search("hosp", type_, flags=re.I) is None) and isType(type_, self.typeDict):
                return "GEN"
        return None

    def cl_bag_of_known_words(self, org, norm, norm_no_sw):
        """ If an org string contain only known words, return GEN. """
        tokens = norm_no_sw.split()
        OK = True
        for tok in tokens:
            if re.match("%s$" % _ofs, tok) is not None:
                continue
            if tok in self.typeDict:
                continue
            if tok in self.subjectDict:
                continue
            if tok in self.orgModDict:
                continue
            OK = False
            break
        if OK:
            return "GEN"
        return None

    def cl_bag_of_known_words2(self, org, norm, norm_no_sw):
        """ Bag of known words and words with subject-like endings """
        tokens = norm_no_sw.split()
        OK = True
        for tok in tokens:
            if re.match("%s$" % _ofs, tok) is not None:
                continue
            if tok in self.typeDict:
                continue
            if tok in self.subjectDict:
                continue
            if tok in self.orgModDict:
                continue
            suffixOK = False
            for idx in range(4, len(tok) - 3):
                suf = tok[idx:]
                if suf in self.wordEndingsDict:
                    suffixOK = True
                    break
            if suffixOK:
                continue
            OK = False
            break
        if OK:
            return "GEN"
        return None

    def cl_default(self, org, norm, norm_no_sw):
        """ Always return GEN """
        return "GEN"


class ExperimentalHybridClassifier(object):
    """
    A generic classifier that combines rules and machine learning. It uses another
    rule-based system to generate features, combines that with its own features,
    and pass the matrix through a support vector machine.
    """

    def __init__(self, rule_classifier, feature_extractor, ml_classifier, rule_mask=None,
                 input_col='input', rule_pred_col='rule_predictions'):
        self.rule_classifier = rule_classifier
        self.feature_extractor = feature_extractor
        self.ml_classifier = ml_classifier
        rules = self.rule_classifier.classification_functions
        if rule_mask is None:
            self.rfuncs = list(rules)
        else:
            self.rfuncs = [f for b, f in zip(rule_mask, rules) if b]
        self.input_col = input_col
        self.rule_pred_col = rule_pred_col
        self.cols = [self.input_col, self.rule_pred_col]

    def fit(self, batch, labels, parallel, sample_weight=None, batch_size=10000, **hyperparams):
        """
        Train the ML classifier inside on a set of examples.

        :param list(str) batch: a list of org-strings
        :param list(str) labels: a list of labels (either GEN or SPE)
        :param joblib.Parallel parallel: a parallel instance to parallelize computation
        :param list(float) sample_weight: samples with higher weights will be treated 
                                          as more important
        :param int batch_size: how many samples to put on a CPU process
        :param hyperparams: scikit-learn-style hyperparams
        """
        preprocessed_input = self._apply_batch(self._preprocess_batch,
                                               batch,
                                               parallel,
                                               batch_size)
        bw_preds = self._apply_batch(self._match_black_whitelist_batch,
                                     preprocessed_input,
                                     parallel,
                                     batch_size)
        accepted_indices = [i for i in range(len(labels)) if not bw_preds[i]]
        # better convert them into np array than indexing
        # them directly because you don't know how they'd behave
        batch = np.array(batch)[accepted_indices]
        labels = np.array(labels)[accepted_indices]
        # don't use zip here because if preprocessed_input is a tuple,
        # it will break _apply_rules_batch
        preprocessed_input = np.array(preprocessed_input)[accepted_indices]
        if sample_weight is not None:
            sample_weight = np.array(sample_weight)[accepted_indices]
        rule_predictions = self._apply_batch(self._apply_rules_batch,
                                             preprocessed_input,
                                             parallel,
                                             batch_size)
        features = self.feature_extractor.fit_transform((batch, rule_predictions))
        self.ml_classifier.fit(features, y=labels, sample_weight=sample_weight, **hyperparams)

    def classifyOrg(self, org):
        """
        Classify an org-string as either GEN or SPE
        """
        preprocessed_input = self.rule_classifier.preprocess(org)
        pred = self._match_black_whitelist(preprocessed_input)
        if pred is None:
            rule_predictions = self._apply_rules(preprocessed_input)
            ml_input = ([org], [rule_predictions])
            pred, = self.ml_classifier.predict(ml_input)
        return pred

    def classifyOrgBatch(self, batch, tracker_id, parallel=None, batch_size=10000):
        '''
        Classify org strings in batch. Pass a joblib Parallel into `parallel`
        to reuse it accross calls. Pass `False` to disable joblib parallelism.
        Pass `None` (the default) to have it created automatically for you.
        '''
        if len(batch) < batch_size * 2:
            parallel = False
        elif parallel is None:
            # the default backend (loky) sometimes fails to use more than one process
            with Parallel(n_jobs=-1, backend='multiprocessing') as parallel:
                return self.classifyOrgBatch(batch, parallel, batch_size)
        preprocessed_input = self._apply_batch(self._preprocess_batch,
                                               batch,
                                               tracker_id,
                                               parallel,
                                               batch_size)
        rule_predictions = self._apply_batch(self._apply_rules_batch,
                                             preprocessed_input,
                                             tracker_id,
                                             parallel,
                                             batch_size)
        features = self._apply_batch(self.feature_extractor.transform,
                                     (batch, rule_predictions),
                                     tracker_id,
                                     parallel,
                                     batch_size)
        ml_preds = self.ml_classifier.predict(features)
        preds = [self._match_black_whitelist(i) or p
                 for i, p in zip(preprocessed_input, ml_preds)]
        return preds

    def _apply_batch(self, func, data, tracker_id, parallel=None, batch_size=None):
        assert batch_size, 'Please provide a batch size'
        data_len = (len(data[0]) if isinstance(data, tuple) else len(data))
        logging.debug(f"- {tracker_id} - GC API Service : Executing method %s", func.__name__)
        if parallel is False or data_len < batch_size * 2:
            return func(data)

        if isinstance(data, tuple):
            a, b = data  # we only use 2-tuple for now
            batches = [(a[i:i + batch_size], b[i:i + batch_size])
                       for i in range(0, data_len, batch_size)]
        else:
            batches = [data[i:i + batch_size] for i in range(0, data_len, batch_size)]
        # results = parallel(delayed(func)(b) for b in batches)
        logging.debug("GC API Service : Started to process batch"
                      " using %d workers", joblib.cpu_count())
        results = Parallel(n_jobs=joblib.cpu_count())(delayed(func)(b) for b in batches)
        logging.debug("GC API Service : Completed processing batch"
                      " using %d workers", joblib.cpu_count())
        if scipy.sparse.issparse(results[0]):
            return scipy.sparse.vstack(results)

        return np.concatenate(results)

    def _match_black_whitelist(self, preprocessed_input):
        _, _, norm_no_sw = preprocessed_input
        if norm_no_sw in self.rule_classifier.whiteList:
            return "GEN"
        elif norm_no_sw in self.rule_classifier.blackList:
            return "SPE"

    def _apply_rules(self, val):
        preds = [f(*val) or 'None' for f in self.rfuncs]
        preds.append(self._first_not_none(preds))
        return preds

    def _apply_rules_batch(self, batch):
        return [self._apply_rules(val) for val in batch]

    def _preprocess_batch(self, batch):
        return [self.rule_classifier.preprocess(val) for val in batch]

    def _match_black_whitelist_batch(self, batch):
        return [self._match_black_whitelist(val) for val in batch]

    def _first_not_none(self, list_):
        for value in list_:
            if value != 'None':
                return value
        return 'None'


if __name__ == "__main__":
    import pandas as pd
    from sklearn.metrics import precision_recall_fscore_support
    from tqdm import tqdm
    classifier = ExperimentalClassifier('test',
                                        use_multilingual_dicts=False,
                                        use_zipcode_us_rule=False)
    dataset = pd.read_csv('../GenericClassifier_re_evaluation_2.txt',
                          sep='\t',
                          header=None,
                          names=['verified_label', 'label', '?', 'input'])
    dataset['verified_label'] = dataset.verified_label.str.replace('VER_', '')
    tqdm.pandas(desc="classifying", position=0, leave=True)
    dataset['predictions_orig'] = dataset.input.progress_apply(classifier.classifyOrg)
    score = lambda preds: precision_recall_fscore_support(dataset.verified_label,
                                                          preds, labels=['GEN'])
    print(score(dataset.predictions_orig))
