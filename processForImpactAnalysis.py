import sys
import re
import fire
from tqdm import tqdm
from lxml import etree as ET
from lxml.etree import XMLSyntaxError
from joblib import Parallel
import classifyGeneric
import joblib
import html

# use "recover=True" to deal with <ce:text> and other issues
parser = ET.XMLParser(recover=True)
org_tag_names = ["org", "multi-org", "organization"]
genericity_map = {"GEN": "g", "SPE": "", "": ""}
strip_quotes_re = re.compile('^"?(.*?)"?$')

def extract_orgs(s):

    orgParts = re.split("(</?(?:multi-)?org(?:anization)?(?=\s|>)[^>]*>)", s)
    it = iter(orgParts)
    try:
        while True:
            part = next(it)
            if re.match("^<(multi-)?org(anization)?(.*[^/])?>$", part) is not None:
                content = next(it)
                yield content
                close_tag = next(it)
                assert re.match("</(multi-)?org(anization)?", close_tag)
    except StopIteration:
        pass

# adapted from processTaggedAffils.py
def augmentXML(xml, genericities_iter):
    affParts = re.split("(<affiliation(?=\s|>)[^>]*>)", xml)
    res = []
    for affIdx, affPart in enumerate(affParts):
        #print("%d '%s'" % (affIdx, affPart))
        if affIdx == 0:
            assert re.match("<affiliation[>\s]", affPart) is None, "ERROR: unexpected <affiliation> tag"
            res.append(affPart)
        elif affIdx % 2 == 1:
            assert re.match("<affiliation[>\s]", affPart) is not None, "ERROR: expected <affiliation> tag"
            res.append(affPart)
        else:
            assert re.match("<affiliation[>\s]", affPart) is None, "ERROR: unexpected <affiliation> tag"
            #orgParts = re.split("(<(?:multi-)?org(?=\s|>)[^>]*>)", affPart)
            orgParts = re.split("(<(?:multi-)?org(?:anization)?(?=\s|>)[^>]*>)", affPart)
            for orgIdx, orgPart in enumerate(orgParts):

                if orgIdx % 2 == 0:
                    assert re.match("</(multi-)?org(anization)?", orgPart) is None, "ERROR"
                    res.append(orgPart)
                else:
                    if re.match("^<(multi-)?org(anization)?(.*[^/])?>$", orgPart) is not None:
                        assert re.match("<(multi-)?org(anization)?", orgPart) is not None
                        assert re.search("type=\"\"", orgPart) is None, "ERROR: expect no type attribute"
                        classif = next(genericities_iter)
                        classif = genericity_map[classif]
                        augmented = re.sub(">", " type=\"%s\">" % classif, orgPart)
                        res.append(augmented)
                    else:
                        res.append(orgPart)
    res = ''.join(res)
    assert re.sub(' type="g?"', '', res) == xml, \
        "Found potential problem: strings are modified more than necessary:\n- Input: %s\n- Output: %s\n" % (xml, res)
    return res

def main(inFile, outFile, model_path=None, batch_size=32000):
    with open(inFile, 'r', encoding='utf-8') as fin:
        input_lines = fin.readlines()

    print('Extracting orgs from file:', inFile)
    orgs = []
    for aff in tqdm(input_lines, desc="Extracting"):
        fields=aff.strip(' \n\r').split("\t")

        if len(fields) == 15:
            orgs.extend(extract_orgs(fields[3]))
            orgs.extend(extract_orgs(fields[4]))
        else:
            orgs.extend(extract_orgs(fields[2]))
            orgs.extend(extract_orgs(fields[3]))
    print('Found %d orgs' % len(orgs))

    assert model_path
    print('Loading classifier:', model_path)
    classifier = joblib.load(model_path)

    # the classifier breaks on empty strings so we need to take them out
    indices_non_empty, orgs_non_empty = zip(*[(i, org) for i, org in enumerate(orgs) if org])
    print('Filtered out %d org strings' % (len(orgs) - len(orgs_non_empty)))

    print('Predicting in batch (size=%d)' % batch_size)
    # notice: the default backend (loky) sometimes fails to use more than one process
    preds = [''] * len(orgs)
    # with Parallel(n_jobs=-1, verbose=3, backend='multiprocessing') as parallel:
    # ml_preds = classifier.classifyOrgBatch(orgs_non_empty, parallel, batch_size=batch_size)
    ml_preds = classifier.classifyOrgBatch(orgs_non_empty, None, batch_size=batch_size)
    for i, ml_pred in zip(indices_non_empty, ml_preds):
        preds[i] = ml_pred

    print('Filling genericity predictions into:', outFile)
    preds_iter = iter(preds)
    with open(outFile, "w", encoding='utf-8') as fout:
        for aff in tqdm(input_lines, desc="Writing"):
            fields=aff.strip(' \n\r').split("\t")
            if len(fields) == 15:
                fields[3] = augmentXML(fields[3], preds_iter)
                fields[4] = augmentXML(fields[4], preds_iter)
            else:
                fields[2] = augmentXML(fields[2], preds_iter)
                fields[3] = augmentXML(fields[3], preds_iter)
            fout.write("\t".join(fields))
            fout.write("\n")
    assert next(preds_iter, "<end>") == "<end>"

if __name__ == "__main__":
    fire.Fire(main)
