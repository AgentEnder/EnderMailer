import smtplib
import re
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()


from pprint import pprint
from getpass import getpass
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Contact:
	def __init__(self, n, a):
		self.name = n #User name
		self.address = a #User email
		
	def __str__(self):
		return self.name
	

class Group:
	def __init__(self, n, i):
		self.name = n #Group Name
		self.include = i #Include group when user sends email to all
		self.members = []
	
	def __eq__(self, other):
		"""Overrides the default implementation"""
		if isinstance(self, other.__class__):
			return self.__dict__ == other.__dict__
		if isinstance(other, str): #This line is kind-of dangerous, could cause unintended behavior but works well for our use cases.
			return self.name == other
		return False
	
	def __str__(self):
		return self.name+", " + str(len(self.members))	 + " members" 
	
	def addPerson(self, person):
		self.members.append(person)

def remove_comments(string):
		pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|#[^\r\n]*$)"
		# first group captures quoted strings (double or single)
		# second group captures comments (//single-line or /* multi-line */)
		regex = re.compile(pattern, re.MULTILINE|re.DOTALL)
		def _replacer(match):
			# if the 2nd group (capturing comments) is not None,
			# it means we have captured a non-quoted (real) comment string.
			if match.group(2) is not None:
				return "" # so we will return empty to remove the comment
			else: # otherwise, we will return the 1st group
				return match.group(1) # captured quoted-string
		return regex.sub(_replacer, string)
		
def parse_comments(file):
	f = open(file, "r")
	fcontents = f.read()
	f.close()
	return remove_comments(fcontents)
	
def parse_config():
	config_options = {}
	fcontents = parse_comments("config.txt")
	flines = fcontents.split("\n")
	flags = list(filter(None, flines))
	config_options["email_host"] = flags[0]
	config_options["email_port"] = flags[1]
	config_options["contact_file"] = flags[2]
	config_options["msg_file"] = flags[3]
	config_options["email_username"] = flags[4]
	config_options["msg_groups"] = flags[5]
	print("Config Options:")
	print("------------------")
	pprint(config_options)
	print("\n\n")
	return config_options

def parse_contacts(file):
	fcontents = parse_comments(file)
	flines = fcontents.split("\n")
	flines = list(filter(None, flines))

	print("Users:")
	print("-------------")
	
	
	contacts = []
	groups = []
	currentGroup = Group("Default", True)
	print(currentGroup.name, ':')
	
	for line in flines:
		if line[:2] == "--":
			groups.append(currentGroup)
			if(line[2]=='!'):
				currentGroup = Group(line[3:], False)
			else:
				currentGroup = Group(line[2:], True)
			print(currentGroup.name, ':')
		else:
			clist = re.findall(r'"([^"]*)"', line)
			cname = clist[0]
			caddress = clist[1]
			newContact = Contact(cname,caddress)
			print('\t' + newContact.name + ":" + newContact.address)
			contacts.append(newContact)
			currentGroup.addPerson(newContact)
	groups.append(currentGroup)	
	print("\n\n")
	return groups, contacts

def read_message(file):
	return_subject = ""
	return_message = ""
	with open(file, 'r') as f:
		fcontent = remove_comments(f.read())
		flines = fcontent.split("\n")
		atMsgText = False
		for i, line in enumerate(flines):
			if(flines[i-1] == "--Subject"):
				return_subject = line
			elif(flines[i] == "--MessageText"):
				atMsgText = True
			elif(atMsgText):
				return_message += "\n"
				return_message += line
	return return_subject, return_message

config = parse_config() #Load Config Data

if(config["contact_file"] == "prompt"):
	config["contact_file"] = filedialog.askopenfilename(title = "Select Contacts File",filetypes = (("text files","*.txt"),("all files","*.*")))

if(config["msg_file"] == "prompt"):
	config["msg_file"] = filedialog.askopenfilename(title = "Select Message File",filetypes = (("text files","*.txt"),("all files","*.*")))


groups, contacts = parse_contacts(config["contact_file"])
for group in groups:
	print (group)

#Groups tos end message to
if(config['msg_groups'] == "prompt"):
	print("\nWhich groups would you like to message?")
	print("Press enter without typing a group name when you are finished.")
	config["msg_groups"] = []
	newGroup = ""
	while(True): #Do-while loop, break if condition is true at the end of the list.
		newGroup = input("Add group:")
		if (newGroup == "" or newGroup == "finished"):
			break;
		elif(newGroup == "all"):
			for g in groups:
				if g.include:
					config['msg_groups'].append(g.name)
			break
		elif(newGroup in groups):
			config["msg_groups"].append(newGroup)
		else:
			print("Please input a valid group.")
else:
	temp_groups = config['msg_groups'].split(",")
	config['msg_groups'] = []
	for groupName in temp_groups:
		if(groupName in groups):
			config["msg_groups"].append(newGroup)
		else:
			raise(ValueError(groupName + " does not exist in current contacts file"))

print(config["msg_groups"])

senderAddress = config["email_username"]
if(senderAddress == "prompt"): #No user email set
	senderAddress = input("Enter your email address: ")
senderPassword = getpass("Enter your Password: ")#Hide password input

s = smtplib.SMTP(host = config["email_host"], port = config["email_port"])
s.starttls()
s.login(senderAddress, senderPassword)



subject, message = read_message(config["msg_file"])	
for group in groups:
	if(group in config["msg_groups"]):
		for person in contacts:
			msg = MIMEMultipart()
			msg['Subject'] = subject
			
			msg['From'] = senderAddress
			msg['To'] = person.address
			msg.attach(MIMEText(message, "plain"))
			
			s.send_message(msg)
			
			del msg

input("Press Enter to Close")
