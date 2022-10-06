import time
import network, machine
import ntptime
import onewire, ds18x20
from ubinascii import hexlify
from micropython import const


class Net():
	def __init__(self):
		self.led = machine.Pin(2, machine.Pin.OUT)
		# create access-point interface
		self.ap = network.WLAN(network.AP_IF)
		# create client interface
		self.wlan = network.WLAN(network.STA_IF)
		self.MAC = str(hexlify(self.wlan.config('mac')), 'utf8')
		self.CLIENT_ID = bytes('sysampet_'+ self.MAC, 'utf8')

	def wifiAP(self, conf):
		ifconf = {}
		if conf['on']:
			self.ap.active(True)
			ifconf['ip'] = self.ap.ifconfig()[0]
		else:
			self.ap.active(False)
		ifconf['is'] = self.ap.isconnected()
		ifconf['mac'] = str(hexlify(self.ap.config('mac')), 'utf8')
		return ifconf

	def wifiCon(self, conf):
		ifconf = {}
		if conf['on']:
			if not self.wlan.isconnected():
				# self.led.on()
				try:
					self.wlan.config(dhcp_hostname=str('sysampet_'+ self.MAC))
				except:
					print("Host name set FAILED")
				self.wlan.active(True)
				print("Connecting to WiFi ... ")
				self.wlan.connect(conf['ssid'], conf['passwd'])
				self.led.value(not self.led.value)
			ifconf['ip'] = self.wlan.ifconfig()[0]
			print('WiFi connacted (ip %s)'% ifconf['ip'])
		else:
			self.wlan.active(False)
		ifconf['is'] = self.wlan.isconnected()
		ifconf['mac'] = self.MAC
		return ifconf

	def ntpSynch(self, conf):
		ntptime.host = conf['url']
		dtc = 3600*int(conf['dst']['on'])
		# utc = conf['timezone']
		# hh, mm = utc[4:].split(":")
		# if utc[3] == '+':
		# 	dtc += (int(hh)*60 + int(mm))*60
		# else:
		# 	dtc -= (int(hh)*60 + int(mm))*60
		try:
			ntptime.settime()
			# print("UTC time: ", str(time.localtime()))
		except:
			return {'is': False}
		rtc = time.time() + dtc
		tm = time.gmtime(rtc)
		machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
		return {'is': True, 'synctime': time.time()}


class Mqtt():
	def __init__(self, config):
		from app.umqtt import MQTTClient
		self.mqtt = MQTTClient(Net().CLIENT_ID, config['MQTT']['broker'])

	def mqttCon(self, subfan):
		self.led.on()
		self.mqtt.set_callback(subfan)
		self.mqtt.connect()
		print('Connected to MQTT broker')
		self.led.off()

	def mqttPub(self, root_topic, data):
		self.led.on()
		subsqr_ignor = []
		main_topic = root_topic.replace('<MAC>', self.MAC)
		if type(data) == type({"a":"b"}):
			for key in data.keys():
				topic = main_topic +'/'+ key
				subsqr_ignor.append(topic)
				topic = str(topic).encode()
				msg = str(data[key]).encode()
				self.mqtt.publish(topic, msg)
		elif type(data) == type("abc"):
			topic = str(main_topic).encode()
			msg = str(data).encode()
			self.mqtt.publish(topic, msg)
		self.led.off()
		return subsqr_ignor


class Actuators():
	def __init__(self, servopins):
		self.pwm_duty = [60, 155, 250, 155]
		base_freq = 100
		# self.pwm = {}
		self.freq = {}
		self.pin = {}
		for key in servopins.keys():
			# self.pwm[key] = machine.PWM(machine.Pin(servopins[key][2]), freq=base_freq, duty=self.pwm_duty[0])
			self.freq[key] = base_freq
			self.pin[key] = servopins[key][2]
			base_freq += 1

	# фун-я керування сервоприводом
	def servoControl(self, name, cmd):
		dt = self.pwm_duty[cmd]
		fr = self.freq[name]
		p = self.pin[name]
		pwm = machine.PWM(machine.Pin(p), freq=fr, duty=dt)
		if cmd == -1:
			pwm.deinit()
			machine.Pin(p, machine.Pin.OUT).off()
			# print(key, ' pwm off')
		else:
			pwm.init()
			# print(pwm)
			return [cmd, time.time(), p]


class Meteo:
	def __init__(self, dthpin):
		import dht
		dth_pin = machine.Pin(dthpin)
		self.sensor = dht.DHT11(dth_pin)

	def getMeteo(self):
		try:
			met = [self.sensor.temperature(), self.sensor.humidity()]
			self.sensor.measure()
			return met
		except:
			print("Sensor NOT CONNACTED")
			return None


class HX711(object):
	CHANNEL_A_128 = const(1)
	CHANNEL_A_64 = const(3)
	CHANNEL_B_32 = const(2)

	DATA_BITS = const(24)
	MAX_VALUE = const(0x7fffff)
	MIN_VALUE = const(0x800000)
	READY_TIMEOUT_SEC = const(1)
	SLEEP_DELAY_USEC = const(80)

	def __init__(self, d_out: int, pd_sck: int, channel: int = CHANNEL_A_128):
		self.d_out_pin = machine.Pin(d_out, machine.Pin.IN)
		self.pd_sck_pin = machine.Pin(pd_sck, machine.Pin.OUT, value=0)
		self.channel = channel

	def __repr__(self):
		return "HX711 on channel %s, gain=%s" % self.channel

	def _convert_from_twos_complement(self, value: int) -> int:
		if value & (1 << (self.DATA_BITS - 1)):
			value -= 1 << self.DATA_BITS
		return value

	def _set_channel(self):
		for i in range(self._channel):
			self.pd_sck_pin.value(1)
			self.pd_sck_pin.value(0)

	def _wait(self):
		t0 = time.time()
		while not self.is_ready():
			if time.time() - t0 > self.READY_TIMEOUT_SEC:
				raise Exception("HX711 connect timeout")

	@property
	def channel(self) -> tuple:
		if self._channel == self.CHANNEL_A_128:
			return 'A', 128
		if self._channel == self.CHANNEL_A_64:
			return 'A', 64
		if self._channel == self.CHANNEL_B_32:
			return 'B', 32

	@channel.setter
	def channel(self, value):
		if value not in (self.CHANNEL_A_128, self.CHANNEL_A_64, self.CHANNEL_B_32):
			raise Exception("Invalid mode")
		else:
			self._channel = value

		if not self.is_ready():
			self._wait()

		for i in range(self.DATA_BITS):
			self.pd_sck_pin.value(1)
			self.pd_sck_pin.value(0)

		self._set_channel()

	def is_ready(self) -> bool:
		return self.d_out_pin.value() == 0

	def power_off(self):
		self.pd_sck_pin.value(0)
		self.pd_sck_pin.value(1)
		time.sleep_us(self.SLEEP_DELAY_USEC)

	def power_on(self):
		self.pd_sck_pin.value(0)
		self.channel = self._channel

	def read(self, raw=False):
		if not self.is_ready():
			self._wait()

		raw_data = 0
		for i in range(self.DATA_BITS):
			self.pd_sck_pin.value(1)
			self.pd_sck_pin.value(0)
			raw_data = raw_data << 1 | self.d_out_pin.value()
		self._set_channel()

		if raw:
			return raw_data
		else:
			return self._convert_from_twos_complement(raw_data)


# end