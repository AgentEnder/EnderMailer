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
	def __init__(self, n, a, g):
		self.name = n #User name
		self.address = a #User email
		self.group = g #Group user belongs to
	

class Group:
	def __init__(self, n, i):
		self.name = n #Group Name
		self.include = i #Include group when user sends email to all
	
	def __eq__(self, other):
		"""Overrides the default implementation"""
		if isinstance(self, other.__class__):
			return self.__dict__ == other.__dict__
		return False

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
	groups.append(currentGroup)
	print(currentGroup.name, ':')
	
	for line in flines:
		if line[:2] == "--":
			if(line[2]=='!'):
				currentGroup = Group(line[3:], False)
			else:
				currentGroup = Group(line[2:], True)
			groups.append(currentGroup)
			print(currentGroup.name, ':')
		else:
			clist = re.findall(r'"([^"]*)"', line)
			cname = clist[0]
			caddress = clist[1]
			cgroup = currentGroup
			newContact = Contact(cname,caddress,cgroup)
			print('\t' + newContact.name + ":" + newContact.address)
			contacts.append(newContact)
	
	print("\n\n")
	
	return groups, contacts
	

config = parse_config() #Load Config Data

if(config["contact_file"] == "prompt"):
	config["contact_file"] = filedialog.askopenfilename(title = "Select Contacts File",filetypes = (("text files","*.txt"),("all files","*.*")))


groups, contacts = parse_contacts(config["contact_file"])

senderAddress = config["email_username"]
if(senderAddress == "prompt"): #No user email set
	senderAddress = input("Enter your email address: ")
senderPassword = getpass("Enter your Password: ")#Hide password input

s = smtplib.SMTP(host = config["email_host"], port = config["email_port"])
s.starttls()
s.login(senderAddress, senderPassword)

if(config["msg_file"] == "prompt"):
	config["msg_file"] = filedialog.askopenfilename(title = "Select Message File",filetypes = (("text files","*.txt"),("all files","*.*")))


for person in contacts:
	msg = MIMEMultipart()
	text = ""
	with open(config["msg_file"], 'r') as f:
		fcontent = remove_comments(f.read())
		flines = fcontent.split("\n")
		pprint(flines)
		atMsgText = False
		for i, line in enumerate(flines):
			if(flines[i-1] == "--Subject"):
				msg['Subject'] = line
			elif(flines[i] == "--MessageText"):
				atMsgText = True
			elif(atMsgText):
				text += "\n"
				text += line
	msg['From'] = senderAddress
	msg['To'] = person.address
	msg.attach(MIMEText(text, "plain"))
	
	s.send_message(msg)
	
	del msg

input("Press Enter to Close")
