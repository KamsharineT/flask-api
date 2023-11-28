#Dockerfile, Dockerimage, Dockercontainer

FROM python:3.8.2

#name of the python file
#executes the 2nd python script first then the 1st script

#have to install eveyrhing , installed and used in the python dfile
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

 
COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]