FROM ubuntu:16.04

# Install the repo that has Python 3.6 distributions
RUN apt-get -y update && \
	apt-get install -y software-properties-common --no-install-recommends && \
	add-apt-repository ppa:deadsnakes/ppa && \
	apt-get -y update

# Set up python3.6 repo info
RUN	apt-get install -y  \
# For the classifier
		python3.6-dev gcc ca-certificates \
# An HTTP server
		nginx \
# Some utils for manual debugging
		vim curl wget

# Get python packages
COPY requirements.txt /tmp/requirements.txt
RUN wget https://bootstrap.pypa.io/get-pip.py && \
	python3.6 get-pip.py && \
# Some packages need Cython to be installed first
	pip3.6 install Cython==0.29.15 && \
# Now, let's install requirements
	pip3.6 install -r /tmp/requirements.txt && \
	apt-get autoremove -y && \
# Remove pip cache at end
	rm -rf /root/.cache

# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering our standard
# output stream, which means that logs can be delivered to the user quickly. PYTHONDONTWRITEBYTECODE
# keeps Python from writing the .pyc files which are unnecessary in this case. We also update
# PATH so that the train and serve programs are found when the container is invoked.

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="${PATH}:/opt/program"
ENV LOG_LEVEL="DEBUG"

# Set up the program in the image
COPY container/* dicts/* ./classifyGenericModified.py ./model.py ./processForImpactAnalysis.py /opt/program/
RUN chmod +x /opt/program/serve
WORKDIR /opt/program