"""
Init module when running as standard flask code.
"""

import traceback
from glob import glob
from threading import Lock
import json
import logging
import os
import joblib
import flask
import timeit


lock = Lock()

logging.basicConfig(format='%(asctime)s,%(msecs)03d - '
                           '%(levelname)-8s - '
                           '[%(filename)s:%(lineno)d] '
                           '%(message)s',
                    level=os.environ.get('LOG_LEVEL', 'DEBUG'),
                    datefmt='%Y-%m-%d %H:%M:%S')


class ScoringService:
    """
    Class which invokes code for model.
    """
    parallel = None
    model = None
    n_jobs = joblib.cpu_count()

    @classmethod
    def get_model(cls):
        """
        Load the model.
        """
        with lock:
            if cls.model is None:
                model_path, = glob('/opt/ml/model/*.pkl')
                logging.info(f'GC API Service : Loading model from {model_path}...')
                cls.model = joblib.load(model_path)
                logging.info('GC API Service : Model load done')
                cls.parallel = joblib.Parallel(n_jobs=cls.n_jobs,
                                               verbose=3,
                                               backend='multiprocessing')
        return cls.model

    @classmethod
    def predict_org(cls, orgs_non_empty, tracker_id, batch_size=10000):
        """
        Invoke the classifyOrgBatch method for classification.
        :param orgs_non_empty: org strings input.
        :param batch_size: batch size split used to parallelize.
        :param tracker_id: tracker_id
        """
        try:
            predictions = cls.get_model().classifyOrgBatch(orgs_non_empty,
                                                           tracker_id,
                                                           cls.parallel,
                                                           batch_size=batch_size)
        except Exception:
            err_msg = _build_tagging_error_message()
            logging.error(f"- {tracker_id} - GC API Service : PROCESSING ERROR:")
            logging.error(err_msg)
            predictions = err_msg
        return predictions


def _build_tagging_error_message():
    trace = traceback.format_exc().replace('\n', ' ')
    error_template = f'GENERIC_CLASSIFIER - PROCESSING ERROR WHILE PARSING: {trace}'
    return error_template


# The flask app for serving predictions
app = flask.Flask(__name__)


@app.route('/execution-parameters', methods=['GET'])
def execution_parameters():
    """
    Default execution params.
    """
    logging.info("GC API Service: Started to invoke end-point execution_parameters.")
    params = {
        'MaxConcurrentTransforms': 1,
        'BatchStrategy': 'MULTI_RECORD',
        'MaxPayloadInMB': 5
    }
    logging.info("GC API Service: Completed invocation of end-point execution_parameters.")
    return flask.jsonify(params)


@app.route('/ping', methods=['GET'])
def ping():
    """
    Determine if the container is working and healthy.
    In our case this means if we can load the model.
    """
    logging.info(f"GC API Service : Invoking ping api,  "
                 f"checks for presence of model and if model can be"
                 f" loaded or if it is already loaded.")
    health = ScoringService.get_model() is not None
    logging.info(f"GC API Service : Completed ping API.")
    status = 200 if health else 500
    if status == 200:
        message = '{"message": "Successful Health check."}'
    else:
        message = '{"message": "Failure Health check."}'
    return flask.Response(response=message,
                          status=status,
                          mimetype='application/json')


@app.route('/invocations', methods=['POST'])
def transformation():
    """
    Do an inference on a single batch of data.
    Data as plaintext is input, one org string per line
    """
    start_time = timeit.default_timer()
    tracker_id = flask.request.headers.get("Tracker-Id")
    set_log_level = flask.request.headers.get("Log-Level")
    if set_log_level:
        set_log_level = set_log_level.upper()
        if set_log_level not in ("INFO", "DEBUG", "ERROR", "WARNING"):
            os.environ['LOG_LEVEL'] = "INFO"
        else:
            os.environ['LOG_LEVEL'] = set_log_level
        logging.getLogger().setLevel(os.environ.get('LOG_LEVEL'))
    else:
        logging.getLogger().setLevel("INFO")
    if tracker_id:
        logging.debug(f"GC API Service : tracker_id - {tracker_id}")
    else:
        logging.debug("GC API Service : tracker_id is not specified, "
                      "setting it to default value - NOT SPECIFIED")
        tracker_id = "NOT SPECIFIED"
    logging.info(f"- {tracker_id} - GC API Service : "
                 f"Invocations API invoked, started to process a request.")
    if flask.request.content_type == 'text/plain':
        data = flask.request.data.decode('utf-8')
        data = data.split('\n')
    else:
        logging.error(f"- {tracker_id} - GC API Service : "
                      f"This predictor accepts only plain text, returning status code 415.")
        return flask.Response(
            response='This predictor accepts only plain text',
            status=415,
            mimetype='text/plain')

    logging.info(f"- {tracker_id} - GC API Service : Invoked with {len(data)} records.")
    predictions = ScoringService.predict_org(data, tracker_id)
    logging.info(f"- {tracker_id} - GC API Service : Completed Invocations API.")
    logging.debug(f"- {tracker_id} - GC API Service: Time taken for "
                  f"processing request - {str(timeit.default_timer() - start_time)}")
    message = {"generic_classifier": predictions}
    return flask.Response(
        response=json.dumps(message),
        status=200,
        mimetype='text/plain')


if __name__ == "__main__":
    # only for debugging
    app.run(host='0.0.0.0', port=8080)
