import os
import configparser


def __init__():
	print("listContainer imported")
	# Start parsers
	config = configparser.ConfigParser()
 
	# Check if settings.ini exists, if not, create it
	if (os.path.isfile('settings.ini') == True):
		config.read('settings.ini')
		checkSettingsFile(config)
     	
	else:
		print("settings.ini not found, creating new one")

		newSettingsFile = open("settings.ini", "w")

		# write default settings to file
		checkSettingsFile(config)

		newSettingsFile.close()

		
def checkSettingsFile(config):
	# get sections from config file and check if section 'window' exists
	configSections = []
	configSections = config.sections()

	print(configSections)

	# if section 'window' exists, load it, if not, create it
	if 'window' in configSections:

		config.read('settings.ini')
		print("Section 'window' found and loaded")
  
	else:
		print("Section 'window' not found, creating new section")
  
		# create section 'window' and save it
		config['window'] = {'width': '700', 'height': '500'}
  
		# save config file
		with open('settings.ini', 'w') as configfile:
			config.write(configfile)
   
		print("Section 'window' created and saved")

	


__init__()
