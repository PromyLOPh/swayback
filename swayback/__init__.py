import os
from io import BytesIO
from urllib.parse import urlparse, urlunparse

from flask import Flask, render_template, send_file, request, make_response
from warcio.archiveiterator import ArchiveIterator
from warcio.recordloader import ArcWarcRecordLoader
from warcio.bufferedreaders import DecompressingBufferedReader

app = Flask(__name__)
app.url_map.host_matching = True

htmlindex = []
urlmap = {}
for filename in os.listdir ('.'):
    if not filename.endswith ('.warc.gz'):
        continue
    print ('using', filename)
    with open(filename, 'rb') as stream:
        ai = ArchiveIterator(stream)
        for record in ai:
            if record.rec_type == 'response':
                u = urlparse (record.rec_headers.get_header('WARC-Target-URI'))
                if u not in urlmap:
                    urlmap[u] = (filename, ai.get_record_offset (), ai.get_record_length ())
                httpHeaders = record.http_headers
                if httpHeaders.get_header ('content-type', '').startswith ('text/html'):
                    rewrittenUrl = urlunparse (('http', u.hostname + '.swayback.localhost:5000', u[2], u[3], u[4], u[5]))
                    htmlindex.append ((urlunparse (u), rewrittenUrl, record.rec_headers.get_header ('warc-date')))

@app.route('/', host='swayback.localhost:5000')
def index ():
    """ A simple index of all HTML pages inside the WARCs """
    return render_template ('index.html', index=htmlindex)

@app.route('/raw', host='swayback.localhost:5000', methods=['OPTIONS'])
def rawPreflight ():
    """ CORS preflight request, allow user-defined fetch() headers """
    resp = make_response ('', 200)
    resp.headers.add ('Access-Control-Allow-Origin', '*')
    resp.headers.add ('Access-Control-Allow-Headers', 'Content-Type')
    resp.headers.add ('Access-Control-Allow-Methods', 'POST')
    return resp

def lookupRecord (url):
    """ Look up URL in database. """
    try:
        filename, offset, length = urlmap[url]
        with open(filename, 'rb') as stream:
            stream.seek (offset, 0)
            buf = BytesIO (stream.read (length))
            loader = ArcWarcRecordLoader ()
            return loader.parse_record_stream (DecompressingBufferedReader (buf))
    except KeyError:
        return None

@app.route('/raw', host='swayback.localhost:5000', methods=['POST'])
def raw ():
    """ Retrieve the original response for a given request """
    data = request.get_json ()
    url = urlparse (data['url'])
    record = lookupRecord (url)
    if record:
        statuscode = record.http_headers.get_statuscode ()
        record.http_headers.remove_header ('Content-Security-Policy')
        record.http_headers.replace_header ('Access-Control-Allow-Origin', '*')
        headers = record.http_headers.headers
        return record.content_stream().read(), statuscode, headers
    else:
        resp = make_response ('', 404)
        resp.headers.add ('Access-Control-Allow-Origin', '*')
        return resp

@app.route('/static/sw.js', host='<host>')
def sw (host=None):
    """ Service worker script needs additional headers """
    return send_file ('static/sw.js'), {'Service-Worker-Allowed': '/'}

# each subdomain will need its own service worker registration
@app.route('/<path:path>', host='<domain>.swayback.localhost:5000', methods=['GET', 'POST'])
def register (path=None, domain=None):
    """ Register a service worker for this origin """
    return render_template ('sw.html')

