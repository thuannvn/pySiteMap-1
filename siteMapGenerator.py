#!/usr/bin/env python
""" 
Generates sitemap.xml of a website. 
Uses Workers to extract site dependencies from url
""" 

__author__='Ronak Kogta<rixor786@gmail.com>'

import requests;
from bs4 import BeautifulSoup;
import multiprocessing;
import copy_reg,types;
from multiprocessing.dummy import Pool as ThreadPool;
import lxml;
import os;
import sys;
import time;


Workers = multiprocessing.cpu_count();

# pickle class functions for multiprocessing module  
def _pickle_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)

copy_reg.pickle(types.MethodType, _pickle_method)

class siteMapGenerator:
	SITEURL = ""
	
	KEEP_ALIVE_SESSION = ""
	
	XMLSitemap = '''<?xml version = "1.0" encoding = "UTF-8"?>
<urlset
  xmlns = "http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:xsi = "http://www.w3.org/2001/XMLSchema-instance"
  xmlns:xhtml = "http://www.w3.org/1999/xhtml"
  xmlns:image = "http://www.google.com/schemas/sitemap-image/1.1"
  xmlns:video = "http://www.google.com/schemas/sitemap-video/1.1"
  xsi:schemaLocation = "
        http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
	'''

	
	def __init__(self,url):
		self.SITEURL = url
		self.KEEP_ALIVE_SESSION = requests.Session()
		UNPROCESSED_URL_QUEUE = [url];
		DISTINCT_URL_SET = set();
		
		if(url[0] != "/"):
			url = url+"/"
		
		DISTINCT_URL_SET.add(url)
		
		# split work  
		pool = multiprocessing.Pool(Workers); # in processes
		#pool = ThreadPool(Workers); # in threads 
		
		while(len(UNPROCESSED_URL_QUEUE) != 0):
			# returns a list of [undiscoverd urls,xmlString]
			 
			results = pool.map(self.xmlPerURL, UNPROCESSED_URL_QUEUE)
			tmpQueue = [];
			for i in results:
				tmpQueue += i[0];
				self.XMLSitemap += i[1]

			# time to process only distinct urls
			UNPROCESSED_URL_QUEUE = [];
			
			for i in tmpQueue:
				if i in DISTINCT_URL_SET:
					continue;
				else: 
					DISTINCT_URL_SET.add(i);
					UNPROCESSED_URL_QUEUE.append(i)
					

		# Writing XMLsitemap
		self.XMLSitemap += "\n</urlset>"
		f = open("sitemap.xml","w");
		f.write(self.XMLSitemap);
		f.close();
		
		#close the pool and wait for the work to finish 
		pool.close() 
		pool.join()
		
	
	
	def xmlPerURL(self,url):
		''' Returns perURL XML string and undiscovered urls list '''
		pageObject = self.fetchPage(url);
		pageData = pageObject[0];
		if(pageObject[1] != ""):
			url = pageObject[1] 
		tmpXML = ""	
		# Writing url data
		tmpXML = tmpXML+'''\n<url>\n\t<loc> '''+url+''' </loc>'''  
		
		soup = BeautifulSoup(pageData);

		# add image sources if exist
		imgSources = soup.find_all('img');
		if(len(imgSources)>0):
			for a in soup.find_all('img'):
				src = str(a['src']);
				src = src.split("?")[0]
				tmpXML = tmpXML+'''\n\t  <image:image>'''
				try:
					alt =  a['alt'];
					tmpXML = tmpXML+'''\n\t\t<image:caption>'''+str(alt)+'</image:caption>'
				except:
					pass;
				tmpXML = tmpXML+'''\n\t\t<image:loc> '''+str(src)+''' </image:loc>\n\t </image:image>'''		
		tmpXML = tmpXML+'''\n</url>'''

		# add distinct urls encountered to the queue
		allLinks = [];
		for a in soup.find_all('a', href = True):
			link = a['href']

			# patch up relative links if exists 
			if (link[0]=='/'):
				link = self.SITEURL+link
			elif(len(link.split("http"))==1):
				link = self.SITEURL+"/"+link;
				
			# ignore redirect links, some redirect links will have multiple http in it. 
			if (len(link.split("http"))>2):
				continue;
			
			# if base url belongs to differnt domain 
			try:
				if (link.split("/")[2] != self.SITEURL.split("/")[2]):
					continue; 
			except:
				print "Error in processing ", link
				continue;

			# Removing Anchors
			link = link.split('#')[0];

			# Removing Query on pages "?"
			link = link.split('?')[0];

			# checking file types links and adding '/' in the end for html links
			if(len(link.split('pdf'))>1 or len(link.split('ppt'))>1):
				a = 'Do nothing'		
			elif(link[-1] != "/"):
				link = link+"/"

			# Removing rss/atom from sitemap.xml as they are equivalent
			if(len(link.split("/rss"))>1 or len(link.split("/atom"))>1):
				continue;

			# Creating a list for discoverd urls 	
			allLinks.append(link);

		#print allLinks;
		#print tmpXML;
		return [allLinks,tmpXML]		

	''' fetchPage: Extracts the pages from website via requests'''	
	def fetchPage(self,url):
	    redirectLink = ""
	    try:
	    	req = self.KEEP_ALIVE_SESSION.get(url);
	    	if req.history:
	    		redirectLink = req.url.split("#_=_")[0]
	    		

	    except:
	    	return [-1,redirectLink];
		
	    return [req.text,redirectLink];    
	    
if __name__ == '__main__':
    
    if(len(sys.argv)<2):
    	print '''Usage:\n\t python sitemap.py <link>: Generates sitemap.xml in current directory\n\t python sitemap.py test: Generate sitemaps of other sites''' 
    	sys.exit(-1);
    
    # Checking for url	
    if (len(sys.argv[1].split("http"))>1):
    	s_time = time.time();
    	itStartsHere = siteMapGenerator(sys.argv[1]);
    	print "Total Time taken:",time.time()-s_time;
    	sys.exit();
    elif (sys.argv[1]=="test"):
    	urls = ["https://jvns.ca"];
    	for u in urls:
    		print "Testing for ", u;
    		while(Workers != 32):
    			s_time = time.time();
    			testSitemap = siteMapGenerator(u);
    			#testSitemap.init(u);
    			print Workers," ",time.time()-s_time
    			Workers*=2;
    		Workers = multiprocessing.cpu_count();	 
    else:
    	sys.exit(-2);		
    
