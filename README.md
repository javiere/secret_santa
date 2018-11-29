Secret Santa
==============

A program to create a simple Secret Santa application for families

When it is Christmas time and you want to decide which member of the family will buy the present for other member of the family and you want to make it secret so nobody else knows except for the person who has to buy the present to keep it a surprise until the big day. This program does that for you. 



## Requirements

In order to run the program, two files need to be provided:

1. A JSON file with the different people that will participate in the secret santa with the following format: 
```python
 [{"name":"X","not_allowed":["Y","Z"],"email":"x@y.com"},{...}]
```
2. A file that contains the message that will be sent to each participant. It can be either **TXT** or **HTML**.

## Usage

In orde to use the program, call the script using a Python interpreter:

```
python SecretSanta.py list message [-e] [-v]
```

Optionally, it can send the results to the person if the email is provided. (Currently configured to use *gmail*). Use the **-e** option if you want to send the emails to the participants.

At the end of the run, an output folder __'out'__ will be generated with the name of the different members and inside the text file who is assinged.
