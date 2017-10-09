FROM bvlc/caffe:cpu

RUN apt-get update && apt-get install unzip python-tk -qy

#RUN wget https://github.com/developius/colorization/archive/master.zip && unzip master.zip
ADD https://github.com/developius/colorization/archive/master.zip .
RUN unzip master.zip
WORKDIR /workspace/colorization-master
RUN wget http://eecs.berkeley.edu/~rich.zhang/projects/2016_colorization/files/demo_v2/colorization_release_v2.caffemodel -O ./models/colorization_release_v2.caffemodel

ENV fprocess="python colorize.py"
ENV read_timeout="60"

COPY colorize.py colorize.py
CMD python -u colorize.py
