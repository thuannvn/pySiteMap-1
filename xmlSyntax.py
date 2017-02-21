#!/usr/bin/env python

# XML Formats 
SITEMAP_HEADER   = \
'<?xml version = "1.0" encoding = "UTF-8"?>\n' \
'<urlset \n' \
'  xmlns = "http://www.sitemaps.org/schemas/sitemap/0.9"\n' \
'  xmlns:xsi = "http://www.w3.org/2001/XMLSchema-instance"\n' \
'  xmlns:xhtml = "http://www.w3.org/1999/xhtml"\n' \
'  xmlns:image = "http://www.google.com/schemas/sitemap-image/1.1"\n' \
'  xmlns:video = "http://www.google.com/schemas/sitemap-video/1.1"\n' \
'  xsi:schemaLocation = "\n' \
'        http://www.sitemaps.org/schemas/sitemap/0.9\n' \
'        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">\n' \

SITEMAP_FOOTER = '</urlset>\n';
URL_HEADER = ' <url>\n';
URL_FOOTER = ' </url>\n';
URL_ENTRY = '  <loc> %s </loc>\n';
IMAGE_ENTRY = \
'    <image:image>\n' \
'      <image:caption> %(caption)s </image:caption>\n' \
'      <image:loc> %(imageurl)s </image:loc>\n' \
'   </image:image>\n' \
