import os
from io import BytesIO
from minio.error import ResponseError
import requests
from os.path import basename
import re
from urllib.parse import parse_qs, urlparse
from minio import Minio

COLORIZE_API = 'http://gateway.openfaas:8080/async-function/colorization'

urls_re = re.compile(r'https?://\S+')

minioClient = Minio(os.environ.get('MINIO_URL'),
                    access_key=os.environ.get('MINIO_ACCESS_KEY'),
                    secret_key=os.environ.get('MINIO_SECRET_KEY'),
                    secure=False)


def handle(st):
    text = parse_qs(st).get('text')[0]
    url = urls_re.findall(text)[0].replace('>', '')
    filename = basename(urlparse(url).path)
    res = requests.get(url)

    try:
        fp = BytesIO(res.content)
        minioClient.put_object(
            'colorization', filename, fp, len(res.content)
        )
    except ResponseError as err:
        print(err)
        return

    requests.post(COLORIZE_API, json={'image': filename})


if __name__ == '__main__':
    handle('''token=dEQML5vtsQNXn4GfCLyimUWq&team_id=T1H9ZN51Q&team_domain=elementai&service_id=294973395829&channel_id=C8NLU2M42&channel_name=openfaas-colorize&timestamp=1515181592.000124&user_id=U5ZESBXNZ&user_name=pgranger&text=colorize+%3Chttps%3A%2F%2Fupload.wikimedia.org%2Fwikipedia%2Fcommons%2F3%2F3d%2FOld_Car2.jpg%3E&trigger_word=colorize''') # NOQA
