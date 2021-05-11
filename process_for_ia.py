import logging
import fire
from tqdm import tqdm
from os import path
from lxml import etree
import joblib
from joblib import Parallel
import pandas as pd
import numpy as np


logging.basicConfig(format='%(asctime)s,%(msecs)03d - '
                           '%(levelname)-8s - '
                           '[%(filename)s:%(lineno)d] '
                           '%(message)s',
                    level='INFO',
                    datefmt='%Y-%m-%d %H:%M:%S')


genericity_map = {"GEN": "g", "SPE": "", "": ""}


def extract_orgs_xml(xml):
    """
    Parse the xml and extract respective fields.
    :param xml: input xml
    :return: final_orgs_strings: All org details from xml or False when failure
    """
    try:
        logging.debug("Process for IA : Starting to run extract_orgs_xml")
        final_orgs = []
        final_orgs_strings = []
        root = etree.fromstring('<affiliations xmlns:ce="_">' + str(xml).strip() + '</affiliations>')
        logging.debug("Process for IA : Get details from organization")
        organization = root.xpath('.//organization')
        logging.debug("Process for IA : Get details from org")
        orgs = root.xpath('.//org')
        logging.debug("Process for IA : Get details from multi-org")
        multi_orgs = root.xpath('.//multi-org')
        final_orgs.extend(organization)
        final_orgs.extend(orgs)
        final_orgs.extend(multi_orgs)
        for org in final_orgs:
            final_orgs_strings.append(org.text)
        logging.debug("Process for IA : Successfully completed run of extract_orgs_xml")
        return final_orgs_strings
    except Exception:
        logging.error(f"Process for IA : Error found while processing xml : {xml}")
        logging.error(f"Process for IA : Error is => ", exc_info=True)
        return "EXTRACTION FAILED WITH EXCEPTIONS"


def _update_attributes(organization, generic_iter):
    for org in organization:
        classification = next(generic_iter)
        if org.text:
            org.set("type", genericity_map[classification])
            # Is escape needed because of the data seen in vendor tagged xml on 4th column?
            # org.text = unescape_html.escape(org.text)


def update_org_tags(xml, generic_iter):
    """
    Parse the xml, update the classification.
    :param
    xml: input xml
    generic_iter : iterable
    :return: xml containing respective classification or False if failure/exception
    """
    try:
        logging.debug("Process for IA : Starting to run update_org_tags")
        logging.debug("Process for IA : Process organization")
        root = etree.fromstring('<affiliations xmlns:ce="_">' + str(xml).strip() + '</affiliations>')
        organization = root.xpath('.//organization')
        _update_attributes(organization, generic_iter)
        logging.debug("Process for IA : Process org")
        orgs = root.xpath('.//org')
        _update_attributes(orgs, generic_iter)
        logging.debug("Process for IA : Process multi-org")
        multi_orgs = root.xpath('.//multi-org')
        _update_attributes(multi_orgs, generic_iter)
        logging.debug("Process for IA : Successfully completed run of update_org_tags")
        return etree.tostring(root, encoding='utf-8').\
            decode('utf-8').\
            replace('<affiliations xmlns:ce="_">', "").\
            replace("</affiliations>", "")
    except Exception:
        logging.error(f"Process for IA : Error found while processing xml : {xml}")
        logging.error(f"Process for IA : Error is => ", exc_info=True)
        return "PROCESSING FAILED WITH EXCEPTIONS"


def _check_regex_xml_org_diff(orgs, orgs_regex):
    # Use below code to check if there are issues between
    # xml and regex parsing's extraction of org, but for that regex code is needed.
    # Please refer to processForImpactAnalysis.py for regex code.
    df_dict = {'orgs_xml': orgs,
               'orgs_regex': orgs_regex
               }
    df = pd.DataFrame({key: pd.Series(value) for key, value in df_dict.items()})
    df['compare'] = np.where((df['orgs_xml'] == df['orgs_regex']), True, False)
    df.to_csv('output.csv', encoding='utf-8')


def main(in_file, out_file, model_path=None, batch_size=32000):
    """
    main method which invokes other functions.
    :param
    in_file: input file
    out_file : output file for which the output is written
    model_path: pkl file path
    batch_size : batch size to use, default 32000
    :return:
    """
    logging.info("Process for IA : Staring the process to extract details and run through GC")
    if in_file is None or not path.exists(in_file):
        logging.error(f"Process for IA : Input file not found in location passed as argument : {model_path}")
        exit(-1)

    if model_path is None or not path.exists(model_path):
        logging.error(f"Process for IA : Model not found in location passed as argument : {model_path}")
        exit(-1)

    with open(in_file, 'r', encoding='utf-8') as fin:
        input_lines = fin.readlines()

    logging.info(f'Process for IA : Extracting orgs from file: {in_file}')
    orgs = []
    check_if_extraction_failed = False
    for aff in tqdm(input_lines, desc="Extracting"):
        fields = aff.strip(' \n\r').split("\t")
        if len(fields) == 15:
            field_4 = extract_orgs_xml(fields[3])
            field_5 = extract_orgs_xml(fields[4])
            if field_4 == "EXTRACTION FAILED WITH EXCEPTIONS":
                logging.error(f"Process for IA : Error while processing 4th column having row {fields[3]}")
                check_if_extraction_failed = True
            elif field_5 == "EXTRACTION FAILED WITH EXCEPTIONS":
                logging.error(f"Process for IA : Error while processing 5th column having row {fields[4]}")
                check_if_extraction_failed = True
            orgs.extend(field_4)
            orgs.extend(field_5)
        else:
            field_3 = extract_orgs_xml(fields[2])
            field_4 = extract_orgs_xml(fields[3])
            if field_3 == "EXTRACTION FAILED WITH EXCEPTIONS":
                logging.error(f"Process for IA : Error while processing 3rd column having row {fields[2]}")
                check_if_extraction_failed = True
            elif field_4 == "EXTRACTION FAILED WITH EXCEPTIONS":
                logging.error(f"Process for IA : Error while processing 4th column having row {fields[3]}")
                check_if_extraction_failed = True
            orgs.extend(field_3)
            orgs.extend(field_4)

    if check_if_extraction_failed:
        logging.error(f"Process for IA : There was error while extracting orgs from aff xml, "
                      f"please see above logs for more information.. exiting now..")
        exit(-1)
    logging.info(f'Process for IA : Found a total of {len(orgs)} orgs')

    logging.info(f'Process for IA: Loading classifier: {model_path}')
    classifier = joblib.load(model_path)

    # the classifier breaks on empty strings so we need to take them out
    indices_non_empty, orgs_non_empty = zip(*[(i, org) for i, org in enumerate(orgs) if org])
    logging.info('Process for IA : Filtered out %d org strings' % (len(orgs) - len(orgs_non_empty)))
    logging.info('Process for IA : Predicting in batch (size=%d)' % batch_size)
    preds = [''] * len(orgs)

    with Parallel(n_jobs=2, backend='multiprocessing') as parallel:
        ml_preds = classifier.classifyOrgBatch(orgs_non_empty, "", parallel, batch_size=batch_size)
    for i, ml_pred in zip(indices_non_empty, ml_preds):
        preds[i] = ml_pred

    logging.info(f'Process for IA : Starting to fill generic classifier predictions into: {out_file}, '
                 f'i.e. output file will be created and updated.')
    preds_iter = iter(preds)
    check_update_failed = False
    with open(out_file, "w", encoding='utf-8') as fout:
        for aff in tqdm(input_lines, desc="Writing"):
            fields = aff.strip(' \n\r').split("\t")
            if len(fields) == 15:
                field_4 = update_org_tags(fields[3], preds_iter)
                field_5 = update_org_tags(fields[4], preds_iter)
                if field_4 == "PROCESSING FAILED WITH EXCEPTIONS":
                    logging.error(f"Process for IA : Error while processing 4th column having row {fields[3]}")
                    check_update_failed = True
                elif field_5 == "PROCESSING FAILED WITH EXCEPTIONS":
                    logging.error(f"Process for IA : Error while processing 5th column having row {fields[4]}")
                    check_update_failed = True
                fields[3] = field_4
                fields[4] = field_5
            else:
                field_3 = update_org_tags(fields[2], preds_iter)
                field_4 = update_org_tags(fields[3], preds_iter)
                if field_3 == "PROCESSING FAILED WITH EXCEPTIONS":
                    logging.error(f"Process for IA : Error while processing 3rd column having row {fields[3]}")
                    check_update_failed = True
                elif field_4 == "PROCESSING FAILED WITH EXCEPTIONS":
                    logging.error(f"Process for IA : Error while processing 4th column having row {fields[4]}")
                    check_update_failed = True
                fields[2] = field_3
                fields[3] = field_4
            fout.write("\t".join(fields))
            fout.write("\n")
    if check_update_failed:
        logging.error(f"Process for IA : There was error while updating the output file {out_file},"
                      f" please check for issues above and remediate if needed.")
    logging.info(f'Process for IA : Completed filling of generic classifier predictions into: {out_file}')
    # assert next(preds_iter, "<end>") == "<end>"


if __name__ == "__main__":
    fire.Fire(main)
