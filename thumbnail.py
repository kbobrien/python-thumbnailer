import cgi
import Image
from StringIO import StringIO
import os
import sys

# Attempt to use memcached
cache_available = True
try:
    import memcache
    cache = memcache.Client(['127.0.0.1:11211'], debug=0)
    cache_ttl = 900  # seconds
except ImportError:
    cache_available = False


image_directory = '/home/kobrien/Pictures/'

def generate_thumbnail(filename, size):   
    """ Generates a thumbnail of the file and returns response body, 
    mimetype"""
    
    cache_key = filename + '_' + size
    
    # TODO: Abstract caching out into a class so memcached is easily changed
    
    # Try cache first
    if cache_available:
        data = cache.get(cache_key)
    else:
        data = None
        
    if data is not None:
        print >> sys.stderr, 'Cache hit for ' + cache_key
        return data
    else:
        i = Image.open(image_directory + filename)
        try:
            i.thumbnail((int(size), int(size)))
        except:
            pass
        s = StringIO()
        i.save(s, 'JPEG')
        
        # Populate cache is available
        if cache_available:
            cache.add(cache_key, s.getvalue(), cache_ttl)
            print >> sys.stderr, 'Added thumb to cache: ' + cache_key        
        
        return (s.getvalue())


def application(environ, start_response):
    """ Entrypoint to the request  """
    
    # Get filename from path
    filename = environ['PATH_INFO']
    
    # Get size from query_string
    query_string = environ.get('QUERY_STRING', False)
    size = cgi.parse_qs(query_string)
    size = size['w'][0]
            
    # Make sure file exists        
    if os.path.isfile(image_directory + filename) and filename.lower().endswith('.jpg'):
        status = '200 OK'    
        mime_type = 'image/jpeg'
        output = generate_thumbnail(filename, size)
    else:
        output = 'File not found: ' + filename
        mime_type = 'text/plain'
        status = '404 Not Found'     
        
    response_headers = [('Content-type', mime_type),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]

    

