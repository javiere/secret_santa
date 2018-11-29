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
import os.path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from random import choice


class SecretSanta(object):
  """
  Class to run the Secret Santa draw. Uses the parser to get the options and
  the file references.

  The parser needs to provide:
      - List of people that participate (in JSON format)
      - Message that will be distributed
  """

  def __init__(self):
    self._args = None
    self._logger = logging.getLogger("Secret Santa")
    if not len(self._logger.handlers):
      # Normal handler
      normal_format = logging.Formatter("%(message)s")
      normal_handler = logging.StreamHandler()
      normal_handler.setFormatter(normal_format)
      normal_handler.setLevel(logging.NOTSET)
      # Console logger for importat things
      debug_format = logging.Formatter(
          "%(levelname)-8s = [%(filename)s, line:%(lineno)-5d] %(module)s->%(funcName)s")
      debug_handler = logging.StreamHandler()
      debug_handler.setFormatter(debug_format)
      debug_handler.setLevel(logging.WARNING)
      # File logger to output anything that happens
      file_format = logging.Formatter(
          "%(asctime)s - [%(filename)s, line:%(lineno)-5d] = %(levelname)-8s = %(message)s")
      file_handler = logging.FileHandler("secret_santa.log")
      file_handler.setFormatter(file_format)
      file_handler.setLevel(logging.DEBUG)
      # Adding handlers
      self._logger.addHandler(debug_handler)
      self._logger.addHandler(normal_handler)
      self._logger.addHandler(file_handler)

  def main(self):
    self.parseArgs()

    # Determine verbosity for logger
    verbosity = logging.WARNING
    if self._args.verbosity >= 2:
      verbosity = logging.DEBUG
    elif self._args.verbosity >= 1:
      verbosity = logging.INFO

    # Setting log level as verbosity
    self._logger.setLevel(verbosity)
    self._logger.info("Starting Secret Santa")

    # Start the lottery process
    Lottery(self._args.list, self._args.message,
            self._args.email, self._logger)

  def parseArgs(self):
    parser = argparse.ArgumentParser(prog="Secret Santa",
                                     description="A Secret Santa that emails recepients")
    parser.add_argument("list", help='File that contains list of people.')
    parser.add_argument(
        "message", help='File that contains message to be sent.')
    parser.add_argument("-e", "--email", help="Sends email",
                        action='store_true', default=False)
    parser.add_argument("-v", "--verbosity",
                        help='Shows debug info', action='count')

    args = parser.parse_args()

    # Check if the files do exist before running the program
    if not os.path.isfile(args.list):
      self._logger.error("File {} not found".format(args.list))
      raise IOError
    if not os.path.isfile(args.message):
      self._logger.error("File {} not found".format(args.message))
      raise IOError

    self._args = args

    return args


class Person(object):
  """
  Defines each individual and the lucky person who will receive the present.
  """

  def __init__(self, name, not_allowed, email, logger):
    self._logger = logger
    self._name = name  # String
    self._not_allowed = not_allowed  # List
    self._email = email #String
    self._receiver = None  # String

    self._logger.debug('Person name: %s. Not allowed:%s',
                       self._name, self._not_allowed)

  def __str__(self):
    return self.message()

  def __eq__(self, person):
    return self.name is person.name

  def __repr__(self):
    return self.name

  def clone(self):
    """
    Returns a copy of the person (without receiver)
    """
    return Person(self.name, self.notAllowed)

  @property
  def receiver(self):
    return self._receiver

  @receiver.setter
  def receiver(self, value):
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

  def message(self):
    """
    Returns a string with the basic information of the person
    """
    return "Name: " + self.name + \
        "\nReceiver: " + self.receiver.name + \
        "\nEmail: " + self.email

  def isReceiverOK(self, receiver):
    """
    Returns whether the proposed receiver is OK for this person
    """
    if receiver == self:
      self._logger.debug("%s cannot buy something for him/herself", self.name)
      return False
    elif receiver.name in self.notAllowed:
      self._logger.debug("%s cannot buy something for %s",
                         self.name, receiver.name)
      return False
    else:
      self._logger.debug("%s CAN buy something for %s",
                         self.name, receiver.name)
      return True

  def assignReceiver(self, receiver):
    self.receiver = receiver
    self._logger.debug("%s will buy something for %s",
                       self.name, self.receiver.name)

  def validateReceiver(self, receiver):
    """
    Checks if the receiver is valid

    receiver is a Person object
    """
    if self.isReceiverOK(receiver):
      self.assignReceiver(receiver)

  def writeFile(self, path):
    """
    Writes a file with the object's message into the path given by
    parameter. The file name will be the object's name.
    """
    filename = path + self.name + ".txt"
    with open(filename, 'w') as f:
      self._logger.info("Writting file: %s", filename)
      f.write(self.message())

  def sendEmail(self, letter):
    """
    Sends email with the person that should get the present, the
    letter message is passed via parameter. The characther ^ in the
    text will be replaced by the object's name and the characther
    * will be replaced by the receiver's name

    By default uses a connection to gmail, change it to other
    address if needed
    """
    self._logger.info("Configuring email for %s", self.name)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
		server.login("EMAIL", "PASSWORD")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Invisible Santa for {}".format(self.name)
		msg['From'] = "SANTAS-EMAIL"
    msg['To'] = self.email

    # Adjust message
    letter = letter.replace("^", self.name)
    part1 = MIMEText(letter.replace("*", self.receiver.name), 'html')
    msg.attach(part1)

    self._logger.info("Sending email to %s", self.email)
		server.sendmail("SANTAS-EMAIL", self.email, msg.as_string())
    server.quit()


class Bucket(object):
  """
  Defines class that holds the people who can receive a gift and
  also does the draw for an specific person
  """

  def __init__(self, list, logger):
    """
    Creates bucket with the list of people. A copy of the list
    is created internally
    """
    self._logger = logger
    self._original_list = list

    self._len = len(self._original_list)

    # Perform the draw
    valid_draw = False
    while not valid_draw:
      valid_draw = self.draw()

  def draw(self):
    # Creates a copy of the original list
    list = map(lambda x: x, self._original_list)

    for person in self._original_list:
      list = self.pick(person, list)

    result = len(list) == 0
    self._logger.debug("Result from draw is: %s", result)

    return result

  def pick(self, giver, list):
    """
    Performs the draw for the giver given by parameter. Giver is
    Person object.
    """
    # Debug
    self._logger.debug("Finding receiver for %s", giver.name)

    pick = False
    count = 0
    while not pick:
      ch = choice(list)
      pick = giver.isReceiverOK(ch)
      if pick:
        giver.assignReceiver(ch)
        list.remove(ch)
      count = count + 1
      # It can happen that we find ourselves in a deadlock, it that
      # case the program will crash and fail
      if count > self._len + 1:
        # raise Exception("Bad combinantion, repeat program")
        self._logger.debug("Invalid draw. Repeat.")
        return list

    # Debug
    self._logger.debug("People in bucket: %s", list)
    return list

  def peopleLeft(self):
    return len(self._list)


class Lottery(object):
  """
  Class to do the draw. Requires a list of People objects.

  Will write out a file with the name of the people in the list
  that contains the person who they will need to buy a present
  for.
  """

  def __init__(self, people_file, letter_file, send_email, logger, output_file=None):
    """
    Creates the lottery, initiates the draw and sends results

    Needs list of people and path to file where the letter
    to be emailed resides
    """
    self._logger = logger
    self.letter_file = letter_file

    self._output_file = ""
    if output_file is not None:
      self._output_file = output_file

    # Load message file and store it
    with open(letter_file, 'r') as f:
      self.msg = f.read()

    self._logger.debug("Message: \n%s", self.msg)

    # Open the list of people from the json file
    with open(people_file, 'r') as f:
      peopleList = json.load(f)

    # Create list of people and bucket with candidates. Once the Bucket
    # is created, the draw will begin
    self._listOfPeople = map(lambda x: Person(
        x['name'], x['not_allowed'], x['email'], self._logger), peopleList)
    self._bucket = Bucket(self._listOfPeople, logger)

    # Writes out files for people
    for person in self._listOfPeople:
      if send_email:
        person.sendEmail(self.msg)
      person.writeFile("out/" + self._output_file)


if __name__ == "__main__":
  SecretSanta().main()
