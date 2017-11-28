#
# Author: Javier Espigares Martin
# Python script to perform the draw for a Secret Santa.
#
# Call the script with a reference to a JSON file with the different
# people that will participate in the secret santa with the following
# format:
#
#  [{"name":"X","not_allowed":["Y","Z"],"email":"x@y.com"},{...}]
#
# At the end of the run, an output folder 'out' will be generated with the
# name of the different members and inside the text file who is assinged
# 
# Optionally, it can send the results to the person if the email is provided
#
import logging 
import json
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from random import choice

class Person(object) :
	"""
	Defines each individual and the lucky person who will receive the present.
	"""
	def __init__(self, name, not_allowed, email=""):
		self._logger = logging.getLogger("Person")
		self._name = name # String
		self._not_allowed = not_allowed # List
		self._email = email #String
		self._receiver = None # String
		
		self._logger.debug('Person name: %s. Not allowed:%s',self._name,self._not_allowed)
	def __str__(self):
		return self.message()
	def __eq__(self,person) :
		return self.name is person.name
	def __repr__(self):
		return self.name
	def clone(self):
		"""
		Returns a copy of the person (without receiver)
		"""
		return Person(self.name,self.notAllowed)
	@property
	def receiver(self) :
		return self._receiver
	@receiver.setter 
	def receiver(self,value) :
		self._receiver = value
	@property
	def name(self):
		return self._name
	@property
	def email(self):
		return self._email
	@property
	def notAllowed(self):
		return self._not_allowed
	def message(self) :
		"""
		Returns a string with the basic information of the person
		"""
		return  "Name: " + self.name + \
				"\nReceiver: " + self.receiver.name + \
				"\nEmail: " + self.email
	def validateReceiver(self,receiver):
		"""
		Checks if the receiver is valid, if valid it will be 
		assigned to this person
		
		receiver is a Person object
		"""
		if receiver == self :
			return False
		if receiver.name in self.notAllowed :
			return False
		self.receiver = receiver
		self._logger.debug("%s will buy something for %s", self.name, self.receiver.name)
		return True
		
	def writeFile(self, path) : 
		"""
		Writes a file with the object's message into the path given by
		parameter. The file name will be the object's name.
		"""
		filename = path + self.name + ".txt"
		with open(filename,'w') as f:
			self._logger.debug("Writting file: %s",filename)
			f.write( self.message() )
		
	def sendEmail(self, letter) :
		"""
		Sends email with the person that should get the present, the
		letter message is passed via parameter. The characther ^ in the
		text will be replaced by the object's name and the characther
		* will be replaced by the receiver's name
		
		By default uses a connection to gmail, change it to other
		address if needed
		"""
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login("EMAIL", "PASSWORD")
		
		msg = MIMEMultipart('alternative')
		msg['Subject'] = "Invisible Santa for {}".format(self.name)
		msg['From'] = "SANTAS-EMAIL"
		msg['To'] = self.email
		
		# Adjust message
		letter = letter.replace("^",self.name)
		part1 = MIMEText(letter.replace("*",self.receiver.name), 'html')
		msg.attach(part1)
		
		self._logger.info("Sending email to %s", self.email)
		server.sendmail("SANTAS-EMAIL", self.email, msg.as_string())
		server.quit()

class Bucket(object) :
	"""
	Defines class that holds the people who can receive a gift and
	also does the draw for an specific person
	"""
	def __init__(self, list) :
		"""
		Creates bucket with the list of people. A copy of the list
		is created internally 
		"""
		self._logger = logging.getLogger("Bucket")
		# self._list = map(lambda x: x.clone(), list) # Can we just make a new list without cloning?
		self._list = map(lambda x: x, list)
		self._len = len(self._list)
		
		# Debug
		self._logger.debug("Initial People in bucket: %s",self._list)
	def draw(self, giver) :
		"""
		Performs the draw for the giver given by parameter. Giver is 
		Person object.
		"""
		# Debug
		self._logger.debug("Finding receiver for %s",giver.name)
		
		pick = False
		count = 0
		while not pick :
			ch = choice(self._list) 
			pick = giver.validateReceiver(ch)
			if pick :
				self._list.remove(ch)
			count = count + 1
			# It can happen that we find ourselves in a deadlock, it that
			# case the program will crash and fail
			if count > self._len+1 :
				raise Exception("Bad combinantion, repeat program")
				
		# Debug
		self._logger.debug("People in bucket: %s",self._list)
	def peopleLeft(self) :
		return len(self._list)
		
class Lottery(object) :
	"""
	Class to do the draw. Requires a list of People objects.
	
	Will write out a file with the name of the people in the list
	that contains the person who they will need to buy a present 
	for.
	"""
	def __init__(self, listOfPeople, letter_file, send_email, name=None) :
		"""
		Creates the lottery, initiates the draw and sends results
		
		Needs list of people and path to file where the letter 
		to be emailed resides
		"""
		self._logger = logging.getLogger("Lottery")
		self.letter_file = letter_file
		
		self._name = ""
		if name is not None :
			self._name = name
			
		# Load message file and store it
		with open(letter_file,'r') as f :
			self.msg = f.read()

		self._logger.debug("Message: \n%s",self.msg)
			
		# Create list of people and bucket with candidates
		self._listOfPeople = listOfPeople 
		self._bucket = Bucket(listOfPeople)
		
		# Proceed to the draw
		for person in self._listOfPeople :
			self._bucket.draw(person)
			
		# Writes out files for people
		for person in self._listOfPeople :
			if send_email :
				person.sendEmail(self.msg)
			person.writeFile("out/" + self._name)

def main() :
	parser = argparse.ArgumentParser(prog="Secret Santa", 
									 description="A Secret Santa that emails recepients")
	parser.add_argument("list",help='File that contains list of people.')
	parser.add_argument("message",help='File that contains message to be sent.')
	parser.add_argument("-e","--email",help="Sends email", action='store_true')
	parser.add_argument("-v","--verbosity",help='Shows debug info', action='count')
	
	args = parser.parse_args()
	
	if args.verbosity is not None :
		logging.basicConfig(level=logging.DEBUG)
	else :
		logging.basicConfig(level=logging.INFO)
		
	with open(args.list,'r') as f:
		peopleList = json.load(f)
	
	list_of_people = map(lambda x: Person(x['name'],x['not_allowed'],x['email']), peopleList)
	Lottery(list_of_people, args.message, args.email)
				
if __name__ == "__main__" :
	main()

