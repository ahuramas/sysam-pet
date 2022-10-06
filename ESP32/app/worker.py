import machine, gc
import time, json
import app.drivers as drv


def readSettings():
	# read unit settings
	try:
		with open('conf/settings.json', 'r') as f:
			return json.load(f)
	except:
		print('no unit settings')

# створення розкладу задач на добу
def taskCreate():

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
	midnight = time.mktime((tm[0], tm[1], tm[2], 0, 0, 0, tm[6], tm[7]))
	wdtask = tm[6]
	
	# for cPython
	# temp = time.strftime("%Y-%m-%d", tm)
	# midnight = time.mktime(time.strptime(temp, "%Y-%m-%d"))
	# wdtask = tm.tm_wday

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

class Worker():
	def __init__(self, status):
		# GPIO
		self.led = machine.Pin(2, machine.Pin.OUT)		# system debug

		self.in_pin = {	# [status, changtime, gpio]
			'menu_sw': [0, 0, machine.Pin(4, machine.Pin.IN)],
			'pir_sen': [0, 0, machine.Pin(13, machine.Pin.IN)]
			}

		self.servo = { # [status, changtime, gpio]
			# 'plate': [0, 0, 32],
			'feed': [0, 0, 27]
			}

		self.glob_var = {
			'portion': -1,
			'plate_lock': 0
			}

		self.tact = 0

		# масив ігнорованих топіків для MQTT Subscr-колбеку
		self.topic_ignor = []

		# підключення модуля ваги
		self.weight = drv.HX711(d_out=16, pd_sck=17)
		self.weight.power_off()

		# підключення модуля температури/вологості
		self.dth = drv.Meteo(23)
		self.dth.getMeteo()

		# підключення модуля сервоприводів
		self.mg = drv.Actuators(self.servo)

		# підключення мережевих модулів
		self.con = drv.Net()

		self.settings = readSettings()

		self.status = status
		self.status['pet'] = proPet()
		self.status['def_lang'] = self.settings['feedset']['language']
	

	def slotProces(self, t):
		# global tact
		
		if gc.mem_free() < 102000:
			gc.collect()
		
		if self.tact >= 100: self.tact = 0
		else: self.tact +=1
		# print(self.tact)

		time_now = time.time()
		# обробка зміни сенсорів/кнопок
		for skey in self.in_pin.keys():
			if self.in_pin[skey][0] == self.in_pin[skey][2].value():
				continue
			
			# якщо зафіксовано рух біля кормушки
			if skey=='pir_sen':
				self.status['motion'] = self.in_pin['pir_sen'][0]
				self.status['cametime'] = {'time': time_now}
			
			# якщо була натиснута кнопка менше 3с - насипату додаткову прцію 
			elif skey=='menu_sw':
				if self.in_pin[skey][2].value() == 1 and self.in_pin[skey][1] > time_now - 5:
					self.status['cmd'] = 'feed'

			self.in_pin[skey][0] = self.in_pin[skey][2].value()
			self.in_pin[skey][1] = time.time()

		# обробка команд
		if self.status['cmd'] == 'reboot':
			machine.reset()
		elif self.status['cmd'] == 'feed':
			self.glob_var['portion'] = int(self.settings['feedset']['manual_servings'])
		self.status['cmd'] = ''

		# перевірка мережевих підключень
		if self.tact==0:
			# підключення до WiFi
			self.status['conn']['WiFi'] = self.con.wifiCon(self.settings['WiFi'])
			# режим точки доступу
			self.status['conn']['AP'] = self.con.wifiAP(self.settings['AP'])


		# обробка розкладу
		if self.tact%10==1:
			if not self.status['nextfeed'].get('time'):
				self.status['conn']['ntp'] = self.con.ntpSynch(self.settings['ntp'])
				self.status['nextfeed'] = taskCreate()
			if self.status['nextfeed']['time'] > time.time():
				return
			if self.status['nextfeed']['title'] != 'cron':
				self.glob_var['portion'] = self.status['nextfeed'].get('portion')
			# синхронізація часу
			self.status['conn']['ntp'] = self.con.ntpSynch(self.settings['ntp'])
			# створення наступної задачі
			self.status['nextfeed'] = taskCreate()

		# обробка порцій
		if self.tact%10==2:
			if self.glob_var['portion'] <= 0:
				return
			new_val = self.servo['feed'][0] + 1
			if new_val >= 4:
				new_val = 0
			self.servo['feed'] = self.mg.servoControl('feed', new_val)
			self.glob_var['portion'] -= 1
			# print(glob_var['portion'], new_val)

		# перевірка таймерів
		if self.tact%10==3:
			# вимкнути pwm через 5с від останьої активності сервоприводу
			for key in self.servo.keys():
				if self.servo[key][1] == time_now-5:
					self.mg.servoControl(key, -1)
			
			# якщо натиснута кнопка більше 3с - змінюємо режим AP
			if self.in_pin['menu_sw'][0]==0 and self.in_pin['menu_sw'][1] < time_now-5:
				self.settings['AP']['on'] = not self.settings['AP']['on']
				self.in_pin['menu_sw'][1] = time_now


		# вимір вагу
			#  and in_pin['pir_sen'][0]==0 and in_pin['pir_sen'][1]+10 <= time.time():
		if self.tact==14:
			self.weight.power_on()
		if self.tact==24:
			self.status['weight'] = int(self.weight.read())
		if self.tact==34:
			self.weight.power_off()
			self.status['remnant'] = str(self.status['weight'])
		
		# вимір температуру та вологість
		if self.tact==5:
			temp = self.dth.getMeteo()
			if temp != None:
				self.status['temperature'] = str(temp[0])
				self.status['humidity'] = str(temp[1])
			else:
				self.status['temperature'] = '---'
				self.status['humidity'] = '---'