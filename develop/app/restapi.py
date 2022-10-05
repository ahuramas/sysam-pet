import json
import time
from app.microdot import Microdot

class Rest():
	def __init__(self, status) -> None:
		self.status = status
		self.info = {
				'mac':'sd:fs:df:a1:sa:76',
				'ip': '0.0.0.0'
			}
		pass

	def start(self):
		app = Microdot()

		@app.route('/')
		def index(request):
			with open('www/index.html', 'rb') as f:
				return f.read(), 200, {'Content-Type': 'text/html'}

		@app.route('/<filename>')
		def static(request, filename):
			name, ext = filename.split('.')
			if ext == 'css':
				mime_type = 'text/css'
			elif ext == 'js':
				mime_type = 'text/javascript'
			elif ext == 'json':
				mime_type = 'application/json'
			elif ext == 'svg':
				mime_type = 'image/svg+xml'
				filename = 'icons/'+ str(filename)
			else:
				mime_type = 'text/plain'
			filepath = 'www/'+ str(filename)
			with open(filepath, 'rb') as f:
				return f.read(), 200, {'Content-Type': mime_type}
		
		@app.get('/api/languag')
		@app.get('/api/languag/<leng>')
		def sendLanguag(request, leng = None):
			if leng == None:
				filepath = "www/languag/%s.json"%(self.status['def_lang'])
			else:
				filepath = "www/languag/%s.json"%(leng)
			# print(filepath)
			try:
				with open(filepath, 'rb') as f:
					return f.read(), 200, {'Content-Type': 'application/json'}
			except:
				return '', 400

		@app.get('/api/info')
		def sendTime(request):
			return json.dumps(self.info), 200, {'Content-Type': 'application/json'}
		
		@app.get('/api/cmd/<newcmd>')
		def getCMD(request, newcmd = None):
			if newcmd != None:
				self.status['cmd'] = newcmd
			return '', 200
  
		@app.get('/api/status')
		def sendStatus(request):
			status_now = self.status.copy()
			status_now['datatime'] = {'time': round(time.time())}
			return json.dumps(status_now), 200, {'Content-Type': 'application/json'}

		@app.get('/conf/<filename>')
		def sendConfig(request, filename):
			filepath = 'conf/%s.json'%(filename)
			# read config fiel
			try:
				with open(filepath, 'rb') as f:
					return f.read(), 200, {'Content-Type': 'application/json'}
			except:
				return '', 400

		@app.post('/conf/<filename>/save')
		def saveConfig(request, filename):
			filepath = 'conf/%s.json'%(filename)
			# write config file
			try:
				with open(filepath, 'wb') as f:
					f.write(request.body)
				return '', 200
			except:
				return '', 400
# ------------------------------------------------
		@app.get('/cat/<filen>')
		def saveFile(request, filen):
			filepath = filen.replace('+', '/')
			# filepath = filepath.replace('-', '.')
			print(filepath)
			try:
				with open(filepath, 'rb') as f:
					return f.read(), 200, {'Content-Type': 'text/plain'}
			except:
				return '', 400

		@app.post('/apt/<filein>')
		def saveFile(request, filein):
			filepath = filein.replace('+', '/')
			# filepath = filepath.replace('-', '.')
			try:
				with open(filepath, 'wb') as f:
					f.write(request.body)
				return 'Done', 200
			except:
				return '', 400

		app.run(debug=True)
		pass

# end