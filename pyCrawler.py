
import logging
import os
import httplib as http
import urllib2 
import time
import urlparse
import sys  
import configargparse
import validators

from bs4 import BeautifulSoup
from queue import Queue
from HTMLParser import HTMLParser

reload(sys)  
sys.setdefaultencoding('utf8')

logging.basicConfig(format='%(asctime)s [%(module)10s] [%(levelname)6s] %(message)s')
log = logging.getLogger()
#log.setLevel(logging.DEBUG)
#log.setLevel(logging.INFO)

visitedUrl = []
visitedDomain = []
urlQueue = Queue()
currentDomain = "";
config = {}

def get_args():
	parser = configargparse.ArgParser()
	parser.add_argument('-sd', '--scan-delay',
                        help='Time delay between requests in scan threads',
                        type=float, default=1)
	parser.add_argument('-d', '--debug', help='Debug Mode', action='store_true')
	parser.add_argument('-l', '--link',help='Entry link url')

	args = parser.parse_args()
	return args

def getPage(url):
	try:
		if validators.url(url):
			headers = {'User-Agent' : 'Mozilla 5.10'}
			req = urllib2.Request(url, None, headers)
			r = urllib2.urlopen(req)
			log.debug(r.code)
			visitedUrl.append(url)
			return r.read()
	except urllib2.URLError as e:
		log.error(e)
		return ""

def getDomaine(url):
	try:
		dm = urlparse.urljoin(url, '/')
		if dm not in visitedDomain:
			visitedDomain.append(dm)
			log.info(visitedDomain)
		return dm
	except e: 
		log.error(e)

def parsePage(page):
	try:
		soup = BeautifulSoup(page, "html.parser")

		for a in soup.find_all('a', href=True):
			if "http" not in a['href'] and len(a['href']) > 0:
				if a['href'][0] == '/':
					a['href'] = a['href'][1:]
					a['href'] = currentDomain + a['href']
					urlQueue.put(a['href'])
				else:
					a['href'] = currentDomain + a['href']
					urlQueue.put(a['href'])
			else:
				urlQueue.put(a['href'])
	except:
		log.error('parsing error : %s' % sys.exc_info()[0])

		#log.debug("Url : %s " % a['href'])
	log.debug("Queue Size : %s "  % urlQueue.qsize())


def search(entryUrl):
	#fetch the first page
	firstPage = getPage(entryUrl)
	currentDomain = getDomaine(entryUrl)
	parsePage(firstPage)
	
	#Fill the queue
	while True:
		url = urlQueue.get()
		log.info("Current page %s" % url)
		if not url in visitedUrl:
			currentDomain = getDomaine(url)
			data = getPage(url)
			parsePage(data)
			time.sleep(config.scan_delay)
			log.debug("Visited page %s" % len(visitedUrl))
		else:
			log.debug("%s already visited" % url)

if __name__ == '__main__':
	args = get_args()
	config = args
	if args.debug:
		log.setLevel(logging.DEBUG)
	else:
		log.setLevel(logging.INFO)

	if(args.link):
		entryUrl = args.link
	else:
		entryUrl = "http://fossbytes.com/"

	#entryUrl = "http://fossbytes.com/"
	currentDomain = getDomaine(entryUrl)
	search(entryUrl)
	