import datetime
import os
import pwd
import humanize
from flask import Flask, redirect, render_template, send_from_directory, request
from python_ini.ini_file import IniFile

config = IniFile()

config_file_path = "backend/settings.ini"

config.parse(config_file_path)

if(config.errors):
    print('Configuration file has errors.')
    print(config.display_errors())

storage_path = config.get_section_values('application','storage_path')
page_title = config.get_section_values('page','page_title')
size_format = config.get_section_values('application','size_format')
attribute_backend = config.get_section_values('application','attribute_backend')
debug_status = str(config.get_section_values('application','debug'))


app = Flask(__name__)
app.debug = debug_status


@app.route('/files', defaults={'filter': None})
@app.route('/files/<filter>')
def files(filter=None):

	files = []
	for file in os.listdir(storage_path):
		if os.path.isfile(os.path.join(storage_path, file)):
			files.append(file)
   
	# if filters are present
	if filter != None:
		# split filter into an array
		filter = filter.split(',')
  
		# create empty array to store files that match the filter(s)
		filesModified = []
		for f in files:
			if all(elem in f for elem in filter):
				filesModified.append(f)
				files = filesModified
  
	
	response = files
	return render_template('filelist.html', page_title=page_title, response=response)


@app.route('/fileinfo/<filename>')
def getFileInfo(filename=None):
	if filename is None:
		response = "No filename provided"
		return render_template('error.html', page_title=page_title, response=response)
	else:
		if files().count(filename) == 0:
			response = 'Error: No file with name <kbd>"' + filename + '"</kbd> found'
			return render_template('error.html', page_title=page_title, response=response)
		else:
      
			# get full path of file
			filepath = storage_path + '/' + filename
			# get all xattr from file
   
			if(attribute_backend == 'xattr'):
				os.system("xattr -l " + filepath + " > xattr.txt")
				# open xattr.txt and read it
				xattr = open("xattr.txt", "r")
				# return the xattr
				fileInfo = xattr.read()
			elif (attribute_backend == 'sqlite'):
				db = DB()
				fileInfo = db.get_tags(filename)
			else:
				fileInfo = "Error: No attribute backend specified"
				return render_template('error.html', page_title=page_title, response=fileInfo)
   
			
		size = os.path.getsize(filepath)
		if size_format == 'human':
			size = humanize.naturalsize(size)
		elif size_format == 'bytes':
			size = size
		elif size_format == 'gnu':
			size = size
		else:
			size = humanize.naturalsize(size)
		
		mod_time = os.path.getmtime(filepath)
		mod_time = datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
		
		owner_uid = os.stat(filepath).st_uid
		owner_name = pwd.getpwuid(owner_uid).pw_name
		filepath = '<a href="/files" >' + storage_path + '</a>/' + filename
		
		response = fileInfo or "None"
		return render_template('fileinfo.html', page_title=page_title, filepath=filepath, size=size, last_modified=mod_time, owner_name=owner_name, response=response)


@app.route('/addtag/<filename>/<tagsArray>/<valueArray>')
def addtag(filename=None, tagsArray=None, valueArray=None):
    # check if all parameters are provided, and if not, return error
	response = []
	if filename is None:
		response.append("No filename provided")
	if tagsArray is None:
		response.append("No tags provided")
	if valueArray is None:
		response.append("No values provided")
  
    # add xattr to file
	if len(tagsArray) > 2:
		for i in range(tagsArray.count(',') + 1):
				# for each tag in tagsArray, add the corrosponding value from valueArray as an attribute to file
				if (attribute_backend == 'xattr'):
					os.system("xattr -w " + tagsArray.split(',')[i] + " " + valueArray.split(',')[i] + " " + filename)
				elif (attribute_backend == 'sqlite'):
					# add tag to sqlite database 
					DB.add_tag(filename, tagsArray.split(',')[i], valueArray.split(',')[i])
     
	elif len(tagsArray) < 2:
		if (attribute_backend == 'xattr'):
			# if only one tag is provided, add the first (only) value from valueArray as am attribute to file
			os.system("xattr -w " + tagsArray[0] + " " + valueArray[0] + " " + filename)
		elif (attribute_backend == 'sqlite'):
			DB.add_tag(filename, tagsArray[0], valueArray[0])
   
	return "Error: " + response


@app.route('/deltag/<filename>/<tagsArray>')
def deltag(filename=None, tagsArray=None):
    # add xattr to file
	if len(tagsArray) > 2:
		for i in range(tagsArray.count(',') + 1):
				# for each tag in tagsArray, delete the corrosponding xattr from the filename
				os.system("xattr -d " + tagsArray.split(',')[i] + " " + filename)
	elif len(tagsArray) < 2:
		os.system("xattr -w " + tagsArray[0] + " " + filename)


@app.route('/')
def index():
	# redirect to index.php
	return redirect("/files", code=302)


@app.route('/assets/<filename>')
def assets(filename):
	return send_from_directory(os.path.join(app.root_path, "templates/assets"), filename)

@app.route('/setup')
def setup():
	config_file_path = "settings.ini"
	# check if config.ini exists
	if os.path.isfile(os.path.join(app.root_path, "settings.ini")):
		config_exists = True
		config_file_contents = open(os.path.join(app.root_path, config_file_path), "r").read()
	else:
		config_exists = False
		
	config_file_path = os.path.join(app.root_path, config_file_path)
	return render_template('setup.html', page_title=page_title, config_file_contents=config_file_contents, config_file_path=config_file_path, config_exists=config_exists)

@app.route('/saveconfig', methods=['POST'])
def saveconfig():
	# get config from form
	config_file_contents = request.form['config_file_contents']
	config_file_path = request.form['config_file_path']
	
	# save config to file
	with open(config_file_path, "w") as f:
		f.write(config_file_contents)
	
 
	db = DB()
	db.create_table()

	# reload config
	config.read(config_file_path)
	
	return redirect("/files", code=302)



class DB():
	def __init__(self):
		import sqlite3

		sqlite_path = config.get_section_values('application','sqlite_path')
		try:
			self.conn = sqlite3.connect(sqlite_path)
			self.c = self.conn.cursor()
		except:
			print(f"""
                Error: Could not connect to sqlite database. Database file not found. 
                Please setup the application by going to http://{address}:{port}/setup
    			""")
			exit(1)
	
	def __enter__(self):
		return self
    
	def __del__(self):
		self.conn.close()
  
	def __str__(self):
		return f"Database connection: {self.conn}"
        
	def create_table(self):
		# Create table with the following columns: id, name, distributor, desktop_environment, architecture, release, filename, tags
		self.c.execute(
      	'''CREATE TABLE files (id INTEGER PRIMARY KEY, name TEXT, distributor TEXT, desktop_environment TEXT, architecture TEXT, release TEXT, filename TEXT, tags TEXT)'''
		)
		self.conn.commit()

	def add(self, name, distributor, desktop_environment, architecture, release, filename, tags):
		self.c.execute(
		'''INSERT INTO files (name, distributor, desktop_environment, architecture, release, filename, tags) VALUES (?, ?, ?, ?, ?, ?, ?)'''
		, (name, distributor, desktop_environment, architecture, release, filename, tags)
		)
		self.conn.commit()

	def count(self, filename):
		self.c.execute("SELECT * FROM files WHERE filename=?", (filename,))
		return len(self.c.fetchall())

	def get(self, filename):
		self.c.execute("SELECT * FROM files WHERE filename=?", (filename,))
		return self.c.fetchall()

	def get_all(self):
		self.c.execute("SELECT * FROM files")
		return self.c.fetchall()

	def get_tags(self, filename):
		self.c.execute("SELECT tags FROM files WHERE filename=?", (filename,))
		return self.c.fetchall()

	def delete(self, filename):
		self.c.execute("DELETE FROM files WHERE filename=?", (filename,))
		self.conn.commit()
  
	def update(self, name, distributor, desktop_environment, architecture, release, filename, tags):
		self.c.execute("UPDATE files SET name=?, distributor=?, desktop_environment=?, architecture=?, release=?, filename=?, tags=? WHERE filename=?", (name, distributor, desktop_environment, architecture, release, filename, tags, filename))
		self.conn.commit()
  
	def close(self):
		self.conn.close()
	
	def __exit__(self):
		self.close()
		return True

	def exportSQL(self, sqlite_path):
		# export database to sql file
		os.system("sqlite3 " + sqlite_path + " .dump > " + sqlite_path + ".sql")


try: 
	if debug_status == "True" or debug_status == True:
		print("Starting application with debug values... {debug_status}")
		address = config.get_section_values('development','address')
		port = config.get_section_values('development','port')
		app.run(host=address, port=port, debug="True")
	else:
		address = config.get_section_values('application','address')
		port = config.get_section_values('application','port')
		app.run(host=address, port=port, debug="True")
except:
	print("Error: Could not start application with specified values. Please check your configuration file.")
	print("Starting application with safe values...")
	app.run(host='0.0.0.0', port=8080)
