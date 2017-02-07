#!/usr/bin/env python
# 
# Sitemap Generator http://tomblomfield.com
# 

import requests;
import os,sys,time;
from bs4 import BeautifulSoup;
import multiprocessing,copy_reg,types;
from multiprocessing.dummy import Pool as ThreadPool 
workers=multiprocessing.cpu_count();
def _pickle_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)

copy_reg.pickle(types.MethodType, _pickle_method)

class siteCrawler:
	siteUrl=""
	session = ""
	XMLSitemap='''<?xml version="1.0" encoding="UTF-8"?>
<urlset
  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:xhtml="http://www.w3.org/1999/xhtml"
  xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"
  xmlns:video="http://www.google.com/schemas/sitemap-video/1.1"
  xsi:schemaLocation="
        http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
	'''

	''' Intializes settings per site'''
	def init(self,url):
		self.siteUrl=url
		self.session = requests.Session()
		processQueue=[url];
		processSet=set();
		if(url[0]!="/"):
			url=url+"/"
		processSet.add(url)
		# split work in  processes 
		pool=multiprocessing.Pool(workers);
		# split in work in threads, faster 
		#pool=ThreadPool(workers);
		while(len(processQueue)!=0):
			# returns a list of [undiscoverd urls,xmlString]
			#print  processQueue, "\n" 
			results = pool.map(self.xmlPerURL, processQueue)
			tmpQueue=[];
			for i in results:
				tmpQueue+=i[0];
				self.XMLSitemap+=i[1]

			# time to process only distinct urls
			processQueue=[];
			for i in tmpQueue:
				if i in processSet:
					continue;
				else: 
					processSet.add(i);
					processQueue.append(i)
					#print i;

		# Writing XMLsitemap
		self.XMLSitemap+="\n</urlset>"
		f=open("sitemap.xml","w");
		f.write(self.XMLSitemap);
		f.close();
		#print self.XMLSitemap

		#close the pool and wait for the work to finish 
		pool.close() 
		pool.join()
		#results=self.xmlPerURL(url);
		#print results;
		return 0; 
	
	''' Returns perURL XML string and undiscovered urls list '''
	def xmlPerURL(self,url):
		pageObject=self.fetchPage(url);
		pageData=pageObject[0];
		if(pageObject[1]!=""):
			url=pageObject[1] 
		tmpXML=""	
		# Writing url data
		tmpXML=tmpXML+'''\n<url>\n\t<loc> '''+url+''' </loc>'''  
		
		soup=BeautifulSoup(pageData);

		# add image sources if exist
		imgSources=soup.find_all('img');
		if(len(imgSources)>0):
			for a in soup.find_all('img'):
				src=str(a['src']);
				src=src.split("?")[0]
				tmpXML=tmpXML+'''\n\t  <image:image>'''
				try:
					alt= a['alt'];
					tmpXML=tmpXML+'''\n\t\t<image:caption>'''+str(alt)+'</image:caption>'
				except:
					pass;
				tmpXML=tmpXML+'''\n\t\t<image:loc> '''+str(src)+''' </image:loc>\n\t </image:image>'''		
		tmpXML=tmpXML+'''\n</url>'''

		# add distinct urls encountered to the queue
		allLinks=[];
		for a in soup.find_all('a', href=True):
			link=a['href']

			# patch up relative links if exists 
			if (link[0]=='/'):
				link=self.siteUrl+link
			elif(len(link.split("http"))==1):
				link=self.siteUrl+"/"+link;
				
			# ignore redirect links, some redirect links will have multiple http in it. 
			if (len(link.split("http"))>2):
				continue;
			
			# if base url belongs to differnt domain 
			try:
				if (link.split("/")[2]!=self.siteUrl.split("/")[2]):
					continue; 
			except:
				print "Error in processing ", link
				continue;

			# Removing Anchors
			link=link.split('#')[0];

			# Removing Query on pages "?"
			link=link.split('?')[0];

			# checking file types links and adding '/' in the end for html links
			if(len(link.split('pdf'))>1 or len(link.split('ppt'))>1):
				a='Do nothing'		
			elif(link[-1]!="/"):
				link=link+"/"

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
	    redirectLink=""
	    try:
	    	req=self.session.get(url);
	    	if req.history:
	    		redirectLink=req.url.split("#_=_")[0]
	    		#print url," redirct link",redirectLink

	    except:
	    	print url," cannot be fetched, check link again";
	    	return [-1,redirectLink];
		
	    return [req.text,redirectLink];    
	    
if __name__ == '__main__':
    
    if(len(sys.argv)<2):
    	print '''Usage:\n\t python sitemap.py <link>: Generates sitemap.xml in current directory\n\t python sitemap.py test: Generate sitemaps of other sites''' 
    	sys.exit(-1);
    
    # Checking for url	
    if (len(sys.argv[1].split("http"))>1):
    	itStartsHere = siteCrawler();
    	s_time=time.time();
    	itStartsHere.init(sys.argv[1]);
    	print "Total Time taken:",time.time()-s_time;
    	sys.exit();
    elif (sys.argv[1]=="test"):
    	urls=["https://jvns.ca"];
    	for u in urls:
    		print "Testing for ", u;
    		while(workers!=32):
    			s_time=time.time();
    			testSitemap=siteCrawler();
    			testSitemap.init(u);
    			print workers," ",time.time()-s_time
    			workers*=2;
    		workers=multiprocessing.cpu_count();	 
    else:
    	sys.exit(-2);		
    
