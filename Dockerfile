FROM bvlc/caffe:cpu

RUN apt-get update && apt-get install unzip python-tk -qy

RUN wget https://github.com/developius/colorization/archive/master.zip && unzip master.zip
WORKDIR /workspace/colorization-master
RUN wget http://eecs.berkeley.edu/~rich.zhang/projects/2016_colorization/files/demo_v2/colorization_release_v2.caffemodel -O ./models/colorization_release_v2.caffemodel

RUN wget https://i1.wp.com/digital-photography-school.com/wp-content/uploads/old/black-and-white.jpg?ssl=1 -O test.jpg

ENV fprocess="python colorize.py"
ENV read_timeout="60"

CMD python colorize.py
