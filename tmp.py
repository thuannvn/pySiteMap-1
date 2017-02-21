#!/usr/bin/env python
__author__ = 'Ronak Kogta<rixor786@gmail.com>'

__description__ = \
''' Generates sitemap for any website based on siteamp protocol given at https://sitemap.org'''

import sys; 
if sys.version_info < (2, 7):
    print ('This script requires Python 2.7 or later.')
    print ('Currently run with version: %s' % sys.version)
    sys.exit(1);

import requests;
from bs4 import BeautifulSoup;
import multiprocessing;
from multiprocessing.dummy import Pool as ThreadPool;
import copy_reg
import types;
import time;
import re; 
import logging;
import datetime;
import argparse;
from xmlSyntax import * 

# pickle class functions for multiprocessing module  
def _pickle_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)
copy_reg.pickle(types.MethodType, _pickle_method)

class siteMapGenerator:
	def __init__(self,args):
		self.DEBUG_MODE = int(args.debug); 
		self.OUTPUT = args.output;
		self.WORKERS = multiprocessing.cpu_count();	#Setting parameters
		self.BROKER = None;
		self.PERMISSIBLE_FILES = None;
		self.IGNORE_FILES = None;
		POOL = None;
		configFile = args.config;

		with open(configFile,'r') as f: 
			for line in f:
				if (line[0] != '#' or line[0] != '\n'):
					parameters = line.split(" ");

					if (parameters[0] == "PERMISSIBLE_FILES"):
						self.PERMISSIBLE_FILES = parameters[1].split('\n')[0].split(",");
										
					if (parameters[0] == "IGNORE_FILES"):
						self.IGNORE_FILES = parameters[1].split('\n')[0].split(",");

					if (parameters[0] == "WORKERS"):
						self.WORKERS = int(parameters[1].split('\n')[0]);	

					if (parameters[0] == "BROKER"):
						self.BROKER = int(parameters[1].split('\n')[0]);
						if (self.BROKER == 0):
							POOL = multiprocessing.Pool(self.WORKERS);
						else:
							POOL = ThreadPool(self.WORKERS);

		self.SITEURL = args.url;
		self.DISTINCT_URL_SET = set();			# Visited URL List 					
		self.DISTINCT_URL_SET.add(self.SITEURL);
		self.KEEP_ALIVE_SESSION = requests.Session()	# Using Keepalive Connection for target site
		self.UNPROCESSED_URL_QUEUE = [self.SITEURL];		# Not Visited  URL List
		
		#sys.exit(1);			
		self.run(POOL);						

	def url_encoder(self,url):
		url = url.decode("utf-8");

		if url[0] == '/':										
				url = self.SITEURL + url 						# relative urls
		elif not (url[0:4] == 'http'):
				url = 'https://' + url;							# Making url append with http
		
		for filetype in self.PERMISSIBLE_FILES:							# Checking for permissible files
			if (len(url.split(filetype)) > 1):
				if url[-1] == "/":
					url = str(url[:-1]);

		for filetype in self.IGNORE_FILES:							# Checking for ignore files
			if (len(url.split(filetype)) > 1):
				return -1;

		if (url.split("/")[2] == self.SITEURL.split("/")[2]): 					# link of another domain
				pass; 
		else:
			return -1;

		url = str(re.split('[#\?]',url)[0]);							# Removing Anchors and query based things
		
		url = str(re.split('/$',url)[0]);							# Removing Trailing '/' from the links
						
			
		return url;

	def run(self,POOL):
		s_time = 0;										# Computing time  
		if (self.DEBUG_MODE):
			s_time = time.time();
		else: 
			del s_time;	

		XMLSitemap = "";
		while(len(self.UNPROCESSED_URL_QUEUE) != 0):
			
			results = POOL.map(self.xmlPerURL, self.UNPROCESSED_URL_QUEUE) 			# [discoverd urls,xmlperURL]
				
			tmpQueue = [];
			for i in results:
				tmpQueue += i[0];
				XMLSitemap += i[1]

			self.UNPROCESSED_URL_QUEUE = []; 						# Only process distinct urls 
			for i in tmpQueue:
				if i in self.DISTINCT_URL_SET:
					continue;
				else: 
					self.DISTINCT_URL_SET.add(i);
					self.UNPROCESSED_URL_QUEUE.append(i)
		
		with open(self.OUTPUT,'w') as f:							# Writing XML to the file
			f.write(SITEMAP_HEADER);
			f.write(XMLSitemap);
			f.write(SITEMAP_FOOTER);
		
		POOL.close()										# Close Parallel Resources 
		POOL.join()

		if (self.DEBUG_MODE):
			print("Total Time taken to generate Sitemap: %f" %(time.time()-s_time));

	def writeXML(self,soup,url):
		tmpXML = URL_HEADER;									# Writing XML Entry for this url 
		tmpXML += (URL_ENTRY % str(url));  
		
		# add image sources if exist
		imgSources = soup.find_all('img');
		if(len(imgSources)>0):
			for a in soup.find_all('img'):
				src = str(a['src']);
				src = src.split("?")[0]
				alt=""; 
				try:
					alt =  a['alt'];
				except:
					pass;
				mapattributes = {'imageurl':str(src),'caption':str(alt)};	
				tmpXML += (IMAGE_ENTRY % mapattributes); 		
		tmpXML += URL_FOOTER;
		return tmpXML;		
	
	def xmlPerURL(self,url):
		pageObject = self.fetchPage(url);
		pageData = pageObject[0];

		if(pageObject[1] != ""):								# Change url if redirect happens 
			url = pageObject[1]
		
		url = self.url_encoder(url);		

		soup = BeautifulSoup(pageData);	 
		tmpXML = self.writeXML(soup,url);							# Generates XML sting for this url 

		allLinks = [];
		for a in soup.find_all('a', href = True):
			link = a['href'];
			link = self.url_encoder(link);
			
			if (link == -1):
				continue;
			allLinks.append(link);

		return [allLinks,tmpXML]		

	''' fetchPage: Extracts the pages from website via requests'''	
	def fetchPage(self,url):
	    redirectLink = ""
	    try:
	    	req = self.KEEP_ALIVE_SESSION.get(url);
	    	
	    	if req.history:
	    		redirectLink = req.url
	    except:
	    	return [-1,redirectLink];
		
	    return [req.text,redirectLink];    

def parseconfig(configure_options):
	configure_options.add_argument('-u','--url', help='Enter url', required=True);
	configure_options.add_argument('-d','--debug', help='Debug Mode', default='0');
	configure_options.add_argument('-o','--output', help='Output file', default='sitemap.xml');
	configure_options.add_argument('-c','--config', help='Configuration file', default='config.yml');

	    
if __name__ == '__main__':

	configure_options = argparse.ArgumentParser(description = __description__);
	parseconfig(configure_options);
	args = configure_options.parse_args();

	init_sitemap = siteMapGenerator(args);
    	
   		
    
