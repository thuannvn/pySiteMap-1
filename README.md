pySiteMap
===
**A Simple python sitemap generator** 

## Introduction 
Generates a sitemap.xml file for a website based on [sitemap protocol](https://sitemap.org).  

## Usage ##

```
	python sitemap.py <link> : Creates sitemap.xml for the link 
	python sitemap.py test : Tests sitemap.xml generation for bunch of other websites 
```

* Requirements 
	+ requests, bs4, multiprocessing

## Benchmark Results ##
Here is the table for sitemap generation for site [Tom Blomfield](http://tomblomfield.com). These tests were run on 64-bit 2 Core Intel Architecture.  

| # of Contexts | Threading Time(s) | Multiprocessing Time (s) |
|:---:|:---:|:---:|
|1 |39.99 | 39.599|
|2 |22.012| 25.11 |
|4 |12.46| 14.655|
|8 | 8.38 | 8.66 |
|16 |6.969| 6.34|

Benchmarking results for [Julia Evans Blog](https://jvns.ca)

| # of Contexts | Threading Time(s) | Multiprocessing Time (s) |
|:---:|:---:|:---:|
|1 |2340 | 2340|
|2 |332| 217.65 |
|4 |377| 247.15|
|8 |363 | 259.13 |
|16 |370| 265.26|

## Optimizations ##
- Used keep alive connections
- Made code more readable via setting options at config.yml files  
- Used multiprocessing in place of threading, for the reason  
	- Python has a **GIL**, a global interpreter lock, which is used to serialize events for threads. Problem with GIL is that it restricts only one active thread running on cpu, and it does not takes care of multi-core architecture. And that might be the one reason to explain above results.
- can use edge triggering for handlelling downloads per process  	 


