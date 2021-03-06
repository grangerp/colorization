import os
os.environ['GLOG_minloglevel'] = '3'

import requests
import numpy as np
import sys
import time
import warnings
import skimage.color as color
import matplotlib.pyplot as plt
import scipy.ndimage.interpolation as sni
import caffe, contextlib, io, tempfile
import json

from minio import Minio

MINIO_URL = os.environ.get('MINIO_URL')


@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.BytesIO()
    yield
    sys.stdout = save_stdout


minioClient = Minio(
    MINIO_URL,
    access_key=os.environ.get('MINIO_ACCESS_KEY'),
    secret_key=os.environ.get('MINIO_SECRET_KEY'),
    secure=False
)

caffe.set_mode_cpu()

# Select desired model
net = caffe.Net(
    './models/colorization_deploy_v2.prototxt',
    './models/colorization_release_v2.caffemodel',
    caffe.TEST
)

(H_in,W_in) = net.blobs['data_l'].data.shape[2:] # get input shape
(H_out,W_out) = net.blobs['class8_ab'].data.shape[2:] # get output shape

pts_in_hull = np.load('./resources/pts_in_hull.npy') # load cluster centers
net.params['class8_ab'][0].data[:,:,0,0] = pts_in_hull.transpose((1,0)) # populate cluster centers as 1x1 convolution kernel


def send_slack(text, webhook=os.environ.get('SLACK_WEBHOOK')):
    data = {
        'text': text,
        'unfurl_links': True,
    }
    res = requests.post(webhook, json=data)

    return res.status_code

"""
Input:
{
  "image": "minio_path_to_image.jpg"
}
"""

def handle(json_in):
    json_in = json.loads(json_in)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        now = str(int(round(time.time() * 1000)))
        filename_in = now + '.jpg'
        filename_out = now + '_output.png'
        file_path_in = tempfile.gettempdir() + '/' + filename_in
        file_path_out = tempfile.gettempdir() + '/' + filename_out

        with nostdout():
            minioClient.fget_object('colorization', json_in['image'], file_path_in)

        # load the original image
        img_rgb = caffe.io.load_image(file_path_in)

        start = time.time()

        img_lab = color.rgb2lab(img_rgb) # convert image to lab color space
        img_l = img_lab[:,:,0] # pull out L channel
        (H_orig,W_orig) = img_rgb.shape[:2] # original image size

        # create grayscale version of image (just for displaying)
        img_lab_bw = img_lab.copy()
        img_lab_bw[:,:,1:] = 0
        img_rgb_bw = color.lab2rgb(img_lab_bw)

        # resize image to network input size
        img_rs = caffe.io.resize_image(img_rgb,(H_in,W_in)) # resize image to network input size
        img_lab_rs = color.rgb2lab(img_rs)
        img_l_rs = img_lab_rs[:,:,0]


        net.blobs['data_l'].data[0,0,:,:] = img_l_rs-50 # subtract 50 for mean-centering
        net.forward() # run network

        ab_dec = net.blobs['class8_ab'].data[0,:,:,:].transpose((1,2,0)) # this is our result
        ab_dec_us = sni.zoom(ab_dec,(1.*H_orig/H_out,1.*W_orig/W_out,1)) # upsample to match size of original image L
        img_lab_out = np.concatenate((img_l[:,:,np.newaxis],ab_dec_us),axis=2) # concatenate with original image L
        img_rgb_out = (255*np.clip(color.lab2rgb(img_lab_out),0,1)).astype('uint8') # convert back to rgb

        duration = time.time() - start

        plt.imsave(file_path_out, img_rgb_out, format='png')

        original_name = json_in['image']
        json_out = json_in
        json_out['image'] = filename_out
        json_out['duration'] = duration

        filename_out = 'results/' + filename_out

        from datetime import timedelta


        with nostdout():
            minioClient.fput_object('colorization', filename_out, file_path_out)
            presigned = minioClient.presigned_get_object('colorization', filename_out, expires=timedelta(days=2))
            presigned = presigned.replace(MINIO_URL, '13.82.43.24')
            presigned_original = minioClient.presigned_get_object('colorization', original_name, expires=timedelta(days=2))
            presigned_original = presigned_original.replace(MINIO_URL, '13.82.43.24')

        send_slack("{} => {} ".format(presigned_original, presigned))
        return json_out
