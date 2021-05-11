import re

typeDictFile = "dicts/typesDict.txt"
subjectDictFile = "dicts/subjectsDict.txt"
subjectModifierDictFile = "dicts/subjectModifiersDict.txt"
orgModifierDictFile = "dicts/orgModifiersDict.txt"
connectorsDictFile =  "dicts/connectorsDict.txt"
wordEndingsDictFile = "dicts/wordEndingsDict.txt"
whiteListFile = "dicts/whiteListDict.txt"
blackListFile = "dicts/blackListDict.txt"
commonDictFile = 'dicts/commonSubjectsDict.txt'
allLocDictFile = 'dicts/allLocDict.txt'
SWDictFile = 'dicts/sw_dict.txt'
CNDictFile = 'dicts/companyNames.txt'
univDictFile = 'dicts/univKeywords.txt'
CSDictFile = 'dicts/companySuffixes.txt'
CTDictFile = 'dicts/companyTypes.txt'


def removeBullet(name):
    bullet = re.compile("^(\(?[a-zA-Z0-9][\)\.]?|\d{2}[\)\.])\s+")
    name = bullet.sub("", name)

    return name

def removeAnd(name):
    startAnd = re.compile("^\s?and ", flags=re.I)
    name = startAnd.sub("", name)

    return name

def removeThe(name):
    startThe = re.compile("^\s?(from )?the ", flags=re.I)
    name = startThe.sub("", name)

    return name

def removeSW(name):
    x = [k for k in name.split(' ') if k not in sw]
    return ' '.join(x)

def removeNumbering(name):
    startNumbering = re.compile("^(1st|2nd|3rd|4th|first|second|third|fourth)\s", flags=re.I)
    name = startNumbering.sub("", name)

    endNumbering = re.compile(" ([1-9]|i|ii|iii|iv|v|a|b|c)$", flags=re.I)
    name = endNumbering.sub("", name)

    return name

def removeAffiliated(name):
    affil = re.compile("^affiliated\s", flags=re.I)
    name = affil.sub("", name)

    return name

def normalizeToken(tok):
    if re.findall('^[A-Z\.\,]+$', tok) != []:
        return tok
    else:
        return tok.lower()

# normalize name
# *** should do something smarter with entities
def normalizeName(name):
    pieces=name.split(' ')
    name=' '.join([normalizeToken(k) for k in pieces])

    entities = re.compile("\&[\#x]*[0-9A-Za-z]+;")
    name = entities.sub("", name)
    
    andAmp = re.compile(" & ")
    name = andAmp.sub(" and ", name)

    d = re.compile(" d'")
    name = d.sub(" de ", name)

    punc = re.compile("[^a-zA-Z0-9\s]")
    name = punc.sub("", name)

    space = re.compile("\s+")
    name = space.sub(" ", name)

    return name.strip()



# Generates all Levenshtein distance 1 variants of the terms in
# 'terms', but only for terms of at least minLength characters.
# Purpose is to have a fixed such dictionary that new terms
# can be compared to with a simple lookup.
# The universe of allowable characters is [a-z0-9\s].
#
# Note: the input and output 'dictionaries' here are python sets, not
# python dicts.
def generateApproxDict(terms):
    smallLetters = list(map(chr, range(ord('a'), ord('z')+1) ))
    #bigLetters   = map(chr, range(ord('A'), ord('Z')+1) )
    digits       = list(map(chr, range(ord('0'), ord('9')+1) ))
    universe = smallLetters + digits + [' ']
    #universe = smallLetters + bigLetters + digits + [' ']

    minLength = 5
    res = set()
    for term in terms:
        res.add(term)
        if len(term) < minLength:
            continue

        for pos in range(len(term)):
            res.add(term[0:pos] + term[pos+1:])  # delete character
            for c in universe:
                if c != term[pos]:
                    res.add(term[0:pos] + c + term[pos+1:])  # change character
                res.add(term[0:pos] + c + term[pos:])        # insert character
        for c in universe:
            res.add(term + c)                                # insert character at end

    return res


# Note: this 'dictionary' is a python set, not a dict.
def loadDict(files):
    res = set()
    for file in files:
        with open(file, 'r', encoding = 'utf-8') as f:
            for line in f:
                term = normalizeName(line)
                res.add(term)

    return res
            

def isSingleSubject(subject, subjects, modifiers):
    if subject in subjects:
        return True

    m = re.match("(\S+)\s(.+)$", subject)
    if m is not None:
        mod = m.group(1)
        tail = m.group(2)
        if isModifier(mod, modifiers) and isSingleSubject(tail, subjects, modifiers):
            return True
            
    return False

# e.g. Experimental and Theoretical Physics
# Assumption is each modifier (except possibly the last) is a single
# token
def isCompoundModifiedSubject(subject, subjects, modifiers):
    # X and Y <subj>
    m = re.match("(\S+) (and|&|y|und|e) (\S+) (.+)$", subject)
    if m is not None:
        X = m.group(1)
        Y = m.group(3)
        tail = m.group(4)
        if isModifier(X, modifiers) and isModifier(Y, modifiers) and isSingleSubject(tail, subjects, modifiers):
            return True

    # X, Y and Z <subj>
    m = re.match("(\S+) (\S+) (and|&|y|und|e) (\S+) (.+)$", subject)
    if m is not None:
        X = m.group(1)
        Y = m.group(2)
        Z = m.group(4)
        tail = m.group(5)
        if isModifier(X, modifiers) and isModifier(Y, modifiers) and isModifier(Z, modifiers) and isSingleSubject(tail, subjects, modifiers):
            return True

    return False

def isSubject(subject, subjects, modifiers):
    if isSingleSubject(subject, subjects, modifiers):
        return True

    if isCompoundModifiedSubject(subject, subjects, modifiers):
        return True

    # X and Y
    twoMatch = re.match("(.+?) (and|&|y|und|e) (.+)$", subject)
    if twoMatch is not None:
        X = twoMatch.group(1)
        Y = twoMatch.group(3)
        if isSingleSubject(X, subjects, modifiers) and isSingleSubject(Y, subjects, modifiers):
            return True

    # X and Y and Z
    threeMatch = re.match("(.+) (and|&|y|und|e) (.+) (and|&|y|und|e) (.+)$", subject)
    if threeMatch is not None:
        X = threeMatch.group(1)
        Y = threeMatch.group(3)
        Z = threeMatch.group(5)
        if isSingleSubject(X, subjects, modifiers) and isSingleSubject(Y, subjects, modifiers) and isSingleSubject(Z, subjects, modifiers):
            return True
        if isSingleSubject(X, subjects, modifiers) and isSingleSubject("%s and %s" % (Y, Z), subjects, modifiers):
            return True
        if isSingleSubject("%s and %s" % (X, Y), subjects, modifiers) and isSingleSubject(Z, subjects, modifiers):
            return True

    # X, Y and Z
    threeMatch = re.match("(.+) (.+) and (.+)$", subject)
    if threeMatch is not None:
        X = threeMatch.group(1)
        Y = threeMatch.group(2)
        Z = threeMatch.group(3)
        if isSingleSubject(X, subjects, modifiers) and isSingleSubject(Y, subjects, modifiers) and isSingleSubject(Z, subjects, modifiers):
            return True

    return False


def isType(type, types):
    if type in types:
        return True

    return False

def isModifier(mod, modifiers):
    if mod in modifiers:
        return True

    return False


def hasAcronym(org, types, subjects, subjApprox, subjModifiers, orgModifiers):
    flag=0
    tokens = org.split()

    if len(tokens) == 1:
        # Check if single token, mixed case, not title/camel-case
        if (org != org.upper()) and (org != org.lower()) and (not org.istitle()):
            return True

        # Check if single token, all caps, not strict dict match
        if (org == org.upper()) and normalizeName(org) not in subjects:
            return True

        return False
    
    
    # One token all-caps or mixed, others not
    tokens = re.sub("[^a-zA-Z0-9]", " ", org).split()
    allUpper = True
    anyAcroLike = False
    for token in tokens:
        if re.match("(ENT|HIV|AIDS|GI)$", token) is not None:
            continue
        if re.match("(I|II|III|IV|V)$", token) is not None:
            flag=1
            continue

        if token != token.upper():
            allUpper = False

        # Remove special prefixes
        token = re.sub("^[a-f0-9]", "", token)
        while re.match("(Bio|Geo|Nano|Neuro|Cardio)", token) is not None:
            token = re.sub("^(Bio|Geo|Nano|Neuro|Cardio)", "", token)
        numUpper = sum([1 for x in token if x.isupper()])
        #numLower = sum([1 for x in token if x.islower()])
        if (numUpper >= 3):
            anyAcroLike = True

    if anyAcroLike and (not allUpper):
        return True
    
    if re.findall('.+\([A-Z\.\s]+\)$', org) != [] and flag==0:
        return True
    
    if re.findall('^[A-Z\.\s]+[\s\-]+.+$', org) != [] and flag==0:
        return True
    
    return False

# n-grams combination of normalized org    
def allGram(x):
    normNG=[]
    oneg = [k.strip() for k in x.strip().split(' ')]
    tok_len = range(len(oneg))
    for i in tok_len:
        tmp=[]
        t=oneg[i]
        for j in range(i+1,len(oneg)):
            t=t+' '+oneg[j]
            tmp.append (t)
        normNG += tmp
    return normNG+oneg

def isCompany(org):
    for i in companySuffixes:
        if re.findall('^[a-zA-Z]+\s'+i+'$', org) != []:
            return True
    return False

def classifyOrg(org):
    # Department/Dept./Dep. of ECE/CSE/EEE/ICE/MAE
    if re.findall("^Dep[a-z]*\.* of [A-Z]{1,2}E$", org) != []:
        return "GEN"

    # ECE/EEE/EE/CS Dep.
    if re.findall("^[A-Z]{2,3} Dep[a-z]*\.*", org) != []:
        return "GEN"
    
    norm = normalizeName(org)
    norm = removeBullet(norm)
    norm = removeAnd(norm)
    norm = removeThe(norm)
    norm = removeNumbering(norm)
    norm = removeAffiliated(norm)
    
    if set(allGram(norm)).intersection(allLoc) != set():
        return "SPE"
    
    if set(allGram(norm)).intersection(cn) != set():
        return "SPE"
    
    if set(allGram(norm)).intersection(companyTypes) != set():
        return "SPE"
    
    if set(allGram(norm)).intersection(univ) != set():
        if set(allGram(norm)).intersection(['Department', 'Dep.']) != set():
            return "GEN"
        else:
            return "SPE"
    
    if isCompany(norm):
        return "SPE"
    
    norm = removeSW(norm)

    if norm in whiteList:
        return "GEN"

    if norm in blackList:
        return "SPE"
    
    # ECE/CSE/EEE/ICE/MAE Department/Dept./Dep.
    if re.findall("^[A-Z]{1,2}E Dep[a-z]*\.*$", org) != []:
        return "GEN"

    if hasAcronym(org, typeDict, subjectDict, subjApproxDict, subjModDict, orgModDict):
        return "SPE"
    
    # Department/Dept./Dep. of xyz University
    if re.findall("^Dep[a-z]*\.*.+University", org) != []:
        return "SPE"
    
    # Department/Dept./Dep. of xyz commonSubjects
    for i in commonSubjectsDict:
        if re.findall("^dep[a-z]*\.*.+"+i, norm) != []:
            return "GEN"

    # Dept/College/etc of <subj>
    m = re.match("(.+?) (of|de|des|di|fur|fr|for|in) (.+)$", norm)
    if m is not None:
        type = m.group(1)
        subject = m.group(3)
        if isType(type, typeDict) and isSubject(subject, subjApproxDict, subjModDict):
            return "GEN"
    
    # Dept/College/etc <subj>
    m = re.match("(\S+) (.+)$", norm)
    if m is not None:
        type = m.group(1)
        subject = m.group(2)
        if isType(type, typeDict) and isSubject(subject, subjApproxDict, subjModDict):
            return "GEN"

    # <subj> Dept/College/etc.
    m = re.match("(.+) (\S+)$", norm)
    if m is not None:
        subject = m.group(1)
        type = m.group(2)
        if isType(type, typeDict) and isSubject(subject, subjApproxDict, subjModDict):
            return "GEN"
        if isType(type, typeDict) and isModifier(subject, subjModDict):
            return "GEN"

    # University <subj> Dept/College/etc.
    m = re.match("university (.+) (\S+)$", norm)
    if m is not None:
        subject = m.group(1)
        type = m.group(2)
        if isType(type, typeDict) and isSubject(subject, subjApproxDict, subjModDict):
            return "GEN"
        if isType(type, typeDict) and isModifier(subject, subjModDict):
            return "GEN"
    
    # Department of Studies in <subj>
    m = re.match("Department of Studies in (\S+)$", org)
    if m is not None:
        subject = m.group(1).lower()
        if isSubject(subject, subjApproxDict, subjModDict):
            return "GEN"
        if isModifier(subject, subjModDict):
            return "GEN"

    if isSubject(norm, subjApproxDict, subjModDict):
        return "GEN"

    if isType(norm, typeDict):
        return "GEN"

    # Central/General/Graduate/etc. <generic>
    m = re.match("(\S+)\s(.+)$", norm)
    if m is not None:
        firstToken = m.group(1)
        tail = m.group(2)
        if isModifier(firstToken, orgModDict) and (classifyOrg(tail) == "GEN"):
            return "GEN"


    # LOWER CONFIDENCE MATCHES

    # Stricter pattern but with unknown subject
    # Dept/College/etc of <subj>
    m = re.match("(.+) (of|de|des|di|fur|fr|for|in) (\S+)$", norm)
    if m is not None:
        type = m.group(1)
        if (re.search("hospital", type, flags=re.I) is None) and isType(type, typeDict):
            return "GEN"

    # Bag of known words
    tokens = norm.split()
    OK = True
    for tok in tokens:
        if re.match("(of|de|des|di|fur|fr|for|in)$", tok) is not None:
            continue
        if tok in typeDict:
            continue
        if tok in subjectDict:
            continue
        if tok in orgModDict:
            continue
        OK = False
        break
    if OK:
        return "GEN"

    # Bag of known words and words with subject-like endings
    tokens = norm.split()
    OK = True
    for tok in tokens:
        if re.match("(of|de|des|di|fur|fr|for|in)$", tok) is not None:
            continue
        if tok in typeDict:
            continue
        if tok in subjectDict:
            continue
        if tok in orgModDict:
            continue
        suffixOK = False
        for idx in range(4, len(tok)-3):
            suf = tok[idx:]
            if suf in wordEndingsDict:
                suffixOK = True
                break
        if suffixOK:
            continue
        OK = False
        break
    if OK:
        return "GEN"

    return "GEN"


typeDict = loadDict([typeDictFile])
subjectDict = loadDict([subjectDictFile, subjectModifierDictFile])
commonSubjectsDict = loadDict([commonDictFile])
subjModDict = loadDict([subjectModifierDictFile])
orgModDict = loadDict([orgModifierDictFile])
wordEndingsDict = loadDict([wordEndingsDictFile])
whiteList = loadDict([whiteListFile])
blackList = loadDict([blackListFile])
allLoc = loadDict([allLocDictFile])
subjApproxDict = generateApproxDict(subjectDict)
sw = loadDict([SWDictFile])
cn = loadDict([CNDictFile])
univ = loadDict([univDictFile])
companySuffixes = loadDict([CSDictFile])
companyTypes = loadDict([CTDictFile])
