import sys
import xml.etree.ElementTree as ET
import re
import fire
from tqdm import tqdm

import classifyGeneric
import joblib

# input is:
#  - list of org strings
# output is list of 3-ples, one for each org:
#  - seq number
#  - "generic" or "specific"
#  - name of org
def classifyOneAffilGeneric(classifier, orgs):
    if not orgs: return []
    if hasattr(classifier, 'classifyOrgBatch'):
        preds = classifier.classifyOrgBatch(orgs)
    else:
        preds = [classifier.classifyOrg(org) for org in orgs]
    return [(idx, pred, org) for idx, (pred, org) in enumerate(zip(preds, orgs))]


def classifyOrgsGeneric(classifier, affRec):
    #affRec=affRec.decode("utf-8")

    # First extract just the xml part
    fields = affRec.strip().split("\t")
    rawXml = fields[0]

    xml = "<affiliationString>" + rawXml + "</affiliationString>"
    
    xml = re.sub('&', 'and', xml)
    try:
        root = ET.fromstring(xml)
    except:
        print('Error at this snippet:', xml)
        raise

    # Now check that XML is as expected
    
    if root.tag != "affiliationString":
        print("ERROR: root element is not <affiliation>")
        print(affRec)
        return []

    # Check that all top-level tags are <affiliation>
    for child in root:
        if child.tag != "affiliation":
            print("ERROR: affiliation string has non-<affiliation> top-level tags")
            return []

        
    # Check that all <affiliation>s are one level down from root
    levOneAffs = list(root.findall("affiliation"))
    numAffs = len(list(root.iter("affiliation")))
    if numAffs != len(levOneAffs):
        print("ERROR: not all affiliations are at first level")
        print(affRec)
        return []

        
    affList = []

    for aff in levOneAffs:
        # Check that all <org>s and <multi-org>s are one level down from affiliation
        levOneOrgs = list(aff.findall("org"))
        numOrgs = len(list(aff.iter("org")))
        if numOrgs != len(levOneOrgs):
            print("ERROR: not all orgs are at first level")
            print(affRec)
            return []

        levOneMultiOrgs = list(aff.findall("multi-org"))
        numMultiOrgs = len(list(aff.iter("multi-org")))
        if numMultiOrgs != len(levOneMultiOrgs):
            print("ERROR: not all multi-orgs are at first level")
            print(affRec)
            return []

        levOneOrganizations = list(aff.findall("organization"))
        numOrganizations = len(list(aff.iter("organization")))
        if numOrganizations != len(levOneOrganizations):
            print("ERROR: not all organizations are at first level")
            print(affRec)
            return []

        # Check that orgs and multi-orgs have no sub-elements
        for org in levOneOrgs:
            if len(org) != 0:
                print("ERROR: <org> has sub-elements")
                print(affRec)
                return []

        for morg in levOneMultiOrgs:
            if len(morg) != 0:
                print("ERROR: <multi-org> has sub-elements")
                print(affRec)
                return []

        for organization in levOneOrganizations:
            if len(organization) != 0:
                print("ERROR: <organization> has sub-elements")
                print(affRec)
                return []

        orgs = [c.text for c in aff if c.tag in ["org", "multi-org", "organization"]]
        affList.append(classifyOneAffilGeneric(classifier, orgs))

    return augmentXML(rawXml, affList)


# xml is an affiliation string, possibly with multiple <affiliation>
# elements. Each <affiliation> has one generics list in affList. A
# generics list is a list of 3-ples of the form (org seq, generic|specific,
# name).
#   Note: in genericsList, the seqs increase incrementally from 0 for
# each <affiliation>, and are not distinct across <affiliation>s. In
# the returned XML they are all distinct, increasing incrementally
# from 0 for the first <org> in the first <affiliation>.
#   For now, assumes the xml string already has empty generic attributes.
def augmentXML(xml, genericsList):
    affParts = re.split("(<affiliation(?=\s|>)[^>]*>)", xml)
    affSeqCnt = 0
    globalOrgSeqCnt = 0
    res = []
    for affIdx in range(len(affParts)):
        #print("%d '%s'" % (affIdx, affParts[affIdx]))
        if affIdx == 0:
            if re.match("<affiliation[>\s]", affParts[affIdx]) is not None:
                print("ERROR: unexpected <affiliation> tag")
                print(xml)
                sys.exit(1)
            res.append(affParts[affIdx])
        elif affIdx % 2 == 1:
            if re.match("<affiliation[>\s]", affParts[affIdx]) is None:
                print("ERROR: expected <affiliation> tag")
                print(xml)
                sys.exit(1)
            res.append(affParts[affIdx])
        else:            
            if re.match("<affiliation[>\s]", affParts[affIdx]) is not None:
                print("ERROR: unexpected <affiliation> tag")
                print(xml)
                sys.exit(1)
            #orgParts = re.split("(<(?:multi-)?org(?=\s|>)[^>]*>)", affParts[affIdx])
            orgParts = re.split("(<(?:multi-)?org(?:anization)?(?=\s|>)[^>]*>)", affParts[affIdx])
            orgSeqCnt = 0
            orgSeqOffset = globalOrgSeqCnt
            for orgIdx in range(len(orgParts)):
                if orgIdx % 2 == 0:
                    if re.match("<(multi-)?org(anization)?", orgParts[orgIdx]) is not None:
                        print("ERROR")
                    res.append(orgParts[orgIdx])
                else:
                    if re.match("<(multi-)?org(anization)?", orgParts[orgIdx]) is None:
                        print("ERROR")
                        
                    #print("%d %d '%s'" % (affSeqCnt, orgSeqCnt, xml))
                    #print(str(genericsList))

                    if re.search("type=\"\"", orgParts[orgIdx]) is None:
                        print("ERROR: expected empty type attribute")
                        print(orgParts[orgIdx])
                        print(xml)
                        sys.exit(1)

                    classif = genericsList[affSeqCnt][orgSeqCnt][1]
                    if classif == "GEN":
                        augmented = re.sub("type=\"\"", "type=\"g\"", orgParts[orgIdx])
                    elif classif == "SPE":
                        augmented = orgParts[orgIdx]
                        pass
                    else:
                        print("ERROR: unrecognized classification '%s'" % classif)

                    res.append(augmented)

                    orgSeqCnt += 1
                    globalOrgSeqCnt += 1
            affSeqCnt +=1 
    return ''.join(res)

def main(inFile, outFile, model_path=None):
    if model_path:
        print('Loading classifier:', model_path)
        classifier = joblib.load(model_path)
    else: 
        classifier = classifyGeneric
    print('Processing file:', inFile)
    with open(inFile,'r', encoding='utf-8') as fin, open(outFile, "w", encoding='utf-8') as fout:
        lines = fin.readlines() # so that we can display a progress bar
        for aff in tqdm(lines, desc="processing"):
            fields=aff.split("\t")
            augmentedAff = classifyOrgsGeneric(classifier, fields[4])
            fields[4] = augmentedAff
            fout.write("\t".join(fields))


if __name__ == "__main__":
    fire.Fire(main)
