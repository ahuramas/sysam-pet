import micropython
from app.restapi import Rest
from app.worker import Worker
import machine

# розмір памяті
micropython.mem_info()

####### Global var #########
status = {
	'nextfeed': {},		#наступні годування
	'cametime': {},		#активність біля тарілки
	'remnant': '',		#залишок корму в тарілці
	'supply': '',		#запас корму в бункері
	'def_lang': 'en',
	'pet': {},			#інформація про улюбленця
	'cmd': '',			#команда
	'conn': {}			#інформація по зєднанням
}

# ініціалізація основного функціоналу
work = Worker(status)

main_timer = machine.Timer(0)
main_timer.init(period=100, mode=machine.Timer.PERIODIC, callback = work.slotProces)


# ініціалізація WEB-сервера
restAPI = Rest(status)
restAPI.start()