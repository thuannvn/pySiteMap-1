#!/usr/bin/env python
# https://stackoverflow.com/questions/9942594/unicodeencodeerror-ascii-codec-cant-encode-character-u-xa0-in-position-20
# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

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
		self.dumpfile = args.output;
		self.workers = multiprocessing.cpu_count();	#Setting parameters
		self.broker = None;
		self.permissible_files = None;
		self.ignore_ext = None;
		configFile = args.config;

		with open(configFile,'r') as f: 
			for line in f:
				if (line[0] != '#' or line[0] != '\n'):
					parameters = line.split(" ");

					if (parameters[0] == "PERMISSIBLE_FILES"):
						self.permissible_files = parameters[1].split('\n')[0].split(",");
										
					if (parameters[0] == "IGNORE_FILES"):
						self.ignore_ext = parameters[1].split('\n')[0].split(",");

					if (parameters[0] == "WORKERS"):
						self.workers = int(parameters[1].split('\n')[0]);	

					if (parameters[0] == "BROKER"):
						self.broker = int(parameters[1].split('\n')[0]);
		
		self.siteurl = args.url;
		self.visited_url_set = set();			 					
		self.visited_url_set.add(self.siteurl);
		self.keep_alive_site_session = requests.Session()	
		self.not_visited_urls = [self.siteurl];		

	def url_encoder(self,url):
		url = url.decode("utf-8");

		if url[0] == '/':										
				url = self.siteurl + url 						# relative urls
		elif not (url[0:4] == 'http'):
				url = 'https://' + url;							# Making url append with http
		
		for filetype in self.permissible_files:							# Checking for permissible files
			if (len(url.split(filetype)) > 1):
				if url[-1] == "/":
					url = str(url[:-1]);

		for filetype in self.ignore_ext:							# Checking for ignore files
			if (len(url.split(filetype)) > 1):
				return -1;

		if (url.split("/")[2] == self.siteurl.split("/")[2]): 					# link of another domain
				pass; 
		else:
			return -1;

		# url = str(re.split('[#\?]',url)[0]);							# Removing Anchors and query based things
		
		url = str(re.split('/$',url)[0]);							# Removing Trailing '/' from the links
						
			
		return url;

	def run(self):
		if (self.broker == 0):
				broker_pool = multiprocessing.Pool(self.workers);
		else:
				broker_pool = ThreadPool(self.workers);
				
		if (self.DEBUG_MODE):
			start_time = time.time();
		
		XMLSitemap = "";
		while(len(self.not_visited_urls) != 0):
			
			results = broker_pool.map(self.process_each_url, self.not_visited_urls) 
			tmpQueue = [];
			for i in results:
				tmpQueue += i[0];
				XMLSitemap += i[1]

			self.not_visited_urls = []; 						# Only process distinct urls 
			for i in tmpQueue:
				if i in self.visited_url_set:
					continue;
				else: 
					self.visited_url_set.add(i);
					self.not_visited_urls.append(i)
		
		with open(self.dumpfile,'w') as f:							# Writing XML to the file
			f.write(SITEMAP_HEADER);
			f.write(XMLSitemap);
			f.write(SITEMAP_FOOTER);
		
		broker_pool.close()										# Close Parallel Resources 
		broker_pool.join()

		if (self.DEBUG_MODE):
			print("Total Time taken to generate Sitemap: %f" %(time.time()-start_time));

	def xml_per_url(self,soup,url):
		url_xml = URL_HEADER;									# Writing XML Entry for this url 
		url_xml += (URL_ENTRY % str(url));  
		
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
				url_xml += (IMAGE_ENTRY % mapattributes); 		
		url_xml += URL_FOOTER;
		return url_xml;		
	
	def process_each_url(self,url):
		pageObject = self.fetch_url(url);
		pageData = pageObject[0];

		if(pageObject[1] != ""):								# Change url if redirect happens 
			url = pageObject[1]
		
		url = self.url_encoder(url);		

		soup = BeautifulSoup(pageData);	 
		url_xml = self.xml_per_url(soup,url);							# Generates XML sting for this url 

		allLinks = [];
		for a in soup.find_all('a', href = True):
			link = a['href'];
			link = self.url_encoder(link);
			
			if (link == -1):
				continue;
			allLinks.append(link);

		return [allLinks,url_xml]		
	
	def fetch_url(self,url):
	    redirectLink = ""
	    try:
	    	req = self.keep_alive_site_session.get(url);
	    	
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
	init_sitemap.run();
    	
   		
    
