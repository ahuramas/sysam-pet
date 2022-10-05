#!/usr/bin/python3
# -*- coding: utf-8 -*-

from app.restapi import Rest
import json, time

# створення розкладу задач на добу
def taskCreate():
	# синхронізація часу
	# con.ntpSynch(settings['ntp'])

	time_now = time.time()
	print('time: ', time_now)

	# читаємо розклад годувань
	try:
		f = open('conf/schedule.json', 'r')
		tasksDict = json.load(f)
		f.close()
	except:
		# створюємо файл розкладу
		f = open('conf/schedule.json', 'w')
		f.write(json.dumps({}))
		f.close()
		return {'title':'cron', 'time': time_now+600}

	tm = time.localtime()

	# for uPython
	# midnight = time.mktime((tm[0], tm[1], tm[2], 0, 0, 0, tm[6], tm[7]))
	# wdtask = tm[6]
	
	# for cPython
	temp = time.strftime("%Y-%m-%d", tm)
	midnight = time.mktime(time.strptime(temp, "%Y-%m-%d"))
	wdtask = tm.tm_wday

	#пошук наступного годування
	next_task = {}
	for key in tasksDict:
		task = tasksDict[key]
		if task['on'] == 0:
			continue

		hh, mm = task['ftime'].split(':')
		time_task = int(midnight) + (60*int(hh) + int(mm))*60
		
		print(task['title'], time_task)

		if time_task < time_now:
			time_task += 86400
			wdtask += 1
			if wdtask > 6:
				wdtask = 0

		if not task['wd'][str(wdtask)]:
			continue

		if next_task.get('time') == None or time_task < next_task.get('time'):
			next_task = {
				'title': task['title'],
				'time': time_task,
			'portion': int(task['portion'])
			}
	
	if not next_task:
		return {'title':'cron', 'time': time_now+600}
	return next_task

# профіль улюбленця
def proPet():
	prodata = {}
	# розклад годування на наступну добу
	# read schedule
	try:
		f = open('conf/profile.json', 'r')
		prodata = json.load(f)
		f.close()
	except:
		f = open('conf/profile.json', 'w')
		f.write(json.dumps({}))
		f.close()
	prodata.pop('breed');
	prodata.pop('birthday');
	return prodata

glob_var = {
	'weight': 5650,
	'portion': -1,
	'plate_lock': 0,
}

# read unit settings
try:
	with open('conf/settings.json', 'r') as f:
		settings = json.load(f)
except:
	print('no unit settings')

status = {
	'cametame': {'time': 122146},
	'remnant': '',					#залишок корму в тарілці
	'nextfeed': taskCreate(),		#наступні годування
	'supply': '',					#запас корму в бункері
	'def_lang': settings['feedset']['language'],
	'pet': proPet(),
	'cmd': ''
}

print(status['nextfeed'])

##########################
restAPI = Rest(status)
restAPI.start()