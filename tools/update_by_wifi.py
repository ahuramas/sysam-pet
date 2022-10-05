#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
import os

sourcdir = '../master/'
upload_dir = ['app', 'www']


def subDirScan(subDir):
	files = []
	for subfile in os.listdir(sourcdir + subDir):
		if subfile[0] == '_':
			continue
		if subfile.find('.') == -1:
			files.extend(subDirScan(subDir + '/' + subfile))
		else:
			files.append(subDir + '/' + subfile)
	return files


filelist =[]

for mdir in os.listdir(sourcdir):
	if upload_dir.count(mdir):
		filelist.extend(subDirScan(mdir))

print("Found %s files to send"%(len(filelist)))
ip = input('Input devace IP: ')

url = 'http://%s'%(ip)
print("Connecting to",url, end='\t- ')
url += '/api/info'
try:
	r = requests.get(url)
except:
	print('FAILED')
	exit()
print('OK')
url = 'http://%s/apt'%(ip)
for file_name in filelist:
	url_file = '%s/%s'%(url, file_name.replace('/', '+'))
	path_file = sourcdir + file_name
	print(path_file, '\t>>>\t', url_file, end='\t- ')
	with open(path_file, 'rb') as f:
		r = requests.post(url_file, data=f.read())
	print(r.text)
