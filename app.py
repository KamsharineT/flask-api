##########################################################################################################
##Developer : Kamsharine Thayananthan                                                                   ##
##Purpose   : writing API using python & flask to fetch the data as per user's preference    			##
##Date      : 2022/10/20                                                                                ##
# updated on : 2023/01/12                                                                               ##  
# updated on : 2023/01/19 - modified to fetch the data from postgresql     								##
# updated on : 2023/01/27 - modified to fix the structure issue and from date issue                     ##                                        
##########################################################################################################

# flask imports
from flask_sqlalchemy import SQLAlchemy
from flask import Flask,request,jsonify,make_response
import uuid # for public id
from werkzeug.security import generate_password_hash, check_password_hash
# imports for PyJWT authentication
import jwt
import os
from pytz import utc
import pytz
import requests
import json
from datetime import datetime, timedelta
from functools import wraps
from tinydb import TinyDB,Query
import psycopg2

# creates Flask object
app = Flask(__name__)
# configuration
# NEVER HARDCODE YOUR CONFIGURATION IN YOUR CODE
# INSTEAD CREATE A .env FILE AND STORE IN IT
app.config['SECRET_KEY'] = 'your secret key'
# database name
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['JSON_SORT_KEYS'] = False
# creates SQLALCHEMY object
db = SQLAlchemy(app)

# Database ORMs
class User(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	public_id = db.Column(db.String(50), unique = True)
	name = db.Column(db.String(100))
	email = db.Column(db.String(70), unique = True)
	password = db.Column(db.String(80))
	
with app.app_context():
	db.create_all()
	
# decorator for verifying the JWT
def token_required(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		token = None
		# jwt is passed in the request header
		if 'bearer-token' in request.headers:
			token = request.headers['bearer-token']
		# return 401 if token is not passed
		if not token:
			return jsonify({'message' : 'Token is missing !!'}), 401

		try:
			# decoding the payload to fetch the stored details
			data = jwt.decode(token, app.config['SECRET_KEY'])
			current_user = User.query\
				.filter_by(public_id = data['public_id'])\
				.first()
            
		except:
			return jsonify({
				'message' : 'Token is invalid !!'
			}), 401
		# returns the current logged in users contex to the routes
		return f(current_user, *args, **kwargs)

	return decorated



# email = "admin@gmail.com"
# password = "123123"
# Headers = {'Authorization': 'jwt ' + 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ImFkbWluQGdtYWlsLmNvbSIsImV4cCI6MTY2NDg1MjE4OSwib3JpZ0lhdCI6MTY2NDg1MTg4OX0.w0V6WhEiM9ydro-fxU9txxs3vfXNo4DZ6X0gxJkuRis'}
# fetchapi = "https://wqprofiling.flotech.io/graphql/"

@app.route('/flotechapi/validate', methods =['GET','POST'])
@token_required
def validate(self):
	
	sName = request.args.get('sName')
	fromdate = request.args.get('fromdate')

	if sName is None and fromdate is None:
		return "Enter the parameters"
	elif sName is None:
		return " Enter the station name"

	
	# if sName not in ("SE541","SE512","SE510"): # temporarily hardcoded for testing purposes
	# 	return "Wrong Station Name"

    # get the from date
	query = """query{
	devices(deviceNameId: \"""" +sName+ """") {
		edges {
		node {
			lastTransmissionDataTime
			deviceType
		}
		}
	}
	}

    """
	# data = requests.get(fetchapi,json={'query':query},headers=Headers)

	# datatext = data.text
	# jsondata =  json.loads(datatext)

    # print(datatext)
	conn = psycopg2.connect(
		host="",
		database="",
		port="",
		user="",
		password="")

	cur = conn.cursor()
    
	cur.execute("select status from devices_device where tag = '"+sName+"'")
	status = cur.fetchall()

	print("status ",status)
	if status == []:
		return "Invalid station Name!, Station is not existing"
	
	cur.close()
    # st = "SE541"
    # cur.execute("Select max(record_time) from device_data where device_tag = '"+st+"'")
    # # time = "2023-01-19 04:05:17"
    # time = cur.fetchall()
    # time = time[0][0]
    # time = datetime.strftime(time,'%Y-%m-%d %H:%M:%S')
    # cur.execute("Select * from device_data where device_tag = '"+st+"' and record_time >= '"+time+"'")
    # res = cur.fetchall()

	#to check and convert the from date
	if fromdate is not None:
		fromdate = fromdate
		print(fromdate,'from date is not none')

		try:
			fromdateconv = datetime.strptime(fromdate,'%d:%m:%Y %H:%M:%S')
			fromdateconv = fromdateconv+timedelta(hours=(-8)) #to convert the time to utc format
			
			print(fromdateconv)
			datedif = fromdateconv + timedelta(days=+3)
			datedif = datetime.strftime(datedif,'%d:%m:%Y')
			today = datetime.strftime(datetime.now(utc),'%d:%m:%Y')
			
			if(datedif<today):
				print("Can retreive the historical data upto 3 days only!")
				return "Can retreive the historical data upto 3 days only!"
			
		except:
			return "Date Format is Wrong, Enter in DD:MM:YYYY HH:MM:SS format"
        

        
	else: #if the from date is null system should get last transmission time as from date
        
		cur = conn.cursor()
		# st = "SE541"
		cur.execute("Select max(record_time) from device_data where device_tag = '"+sName+"' and parameter_tag = ('Temperature')")
		# time = "2023-01-19 04:05:17"
		lastTransmissionDataTime = cur.fetchall()
		print(lastTransmissionDataTime)
		lastTransmissionDataTime = lastTransmissionDataTime[0][0]
		lastTransmissionDataTime = datetime.strftime(lastTransmissionDataTime,'%Y-%m-%d %H:%M:%S')
		# try:
			
		#     lastTransmissionDataTime = datetime.strptime(lastTransmissionDataTime,'%Y-%m-%dT%H:%M:%S.%f+00:00')+timedelta(minutes=(-5))#decucting 5 minutes to avoid getting device data recorded time instead sensor data record time
		# except:
		#     lastTransmissionDataTime = datetime.strptime(lastTransmissionDataTime,'%Y-%m-%dT%H:%M:%S+00:00')+timedelta(minutes=(-5))
		fromdateconv = lastTransmissionDataTime	
		fromdateconv = datetime.strptime(fromdateconv,'%Y-%m-%d %H:%M:%S')
		
	# fromdateconv = datetime.strftime(fromdateconv,'%Y-%m-%dT%H:%M:%SZ')
		cur.close()
	# rec_time = datetime.strptime(fromdateconv,'%Y-%m-%d %H:%M:%S')
	rec_time = fromdateconv+timedelta(minutes=(-1))
	rec_time = datetime.strftime(rec_time,'%Y-%m-%d %H:%M:%S')

	print('rectime',rec_time)
	listval = []

#     #the output contains depth, the sensor values in the depths & weather details 
#     #if we get the length of infolist it will be considering weatherdetails too
#     #therefore deducting 1 to avoid weather details
	print(sName)
	cur = conn.cursor()
	cur.execute("select device_type,number_of_depth from devices_device where tag = '"+sName+"'")
	device_Data = cur.fetchall()

	no_of_depths = device_Data[0][1]   
	print('no_of_depths',no_of_depths)
#     #weatherlist = infolist[no_of_depths] # add the weather list once weather is added

#     #hard coding weather details for testing purpose

	

	# weatherlist = {}
#     #print(infolist[no_of_depths])

#     # get the device type
#     device_type = (jsondata.get('data').get('devices').get('edges'))
#     device_type = device_type[0].get('node').get('deviceType')

    # fromdateconv = datetime.strptime(fromdateconv,'%Y-%m-%d %H:%M:%S')
    # fromdateconv = fromdateconv+timedelta(minutes=(-20))
    # fromdateconv = datetime.strftime(fromdateconv,'%Y-%m-%dT%H:%M:%SZ')

	print(fromdateconv)
	device_type = device_Data[0][0]
	print(device_type)
	try:
		print('rectime',rec_time)
		cur.execute("Select record_time from device_data where device_tag = '"+sName+"' and record_time >= To_timestamp('"+rec_time+"','yyyy-mm-dd hh24:mi') and parameter_tag = ('Temperature') group by record_time order by record_time ")
		# cur.close()
		#print(("Select record_time from device_data where device_tag = '"+sName+"' and record_time >= To_timestamp('"+rec_time+"','yyyy-mm-dd hh:mi') and parameter_tag in ('Temperature') group by record_time order by record_time "))
		no_record = cur.fetchall()
		# print(no_record)
		# print(('no_record',no_record)[0][0])
	except:
		print("Error")
		return ("Error Occured!")


	#     info = []
	#     #info= [{"depth_id":n+1,"temperature":"","pH":"","conductivity":"","chl-a":"","do_conc":"","do_sat":"","tds":"","salinity":"","turbidity":"","depth":""}]
	print('len(no_record)',len(no_record))
	for i in range(len(no_record)):
		#print(datatext)
		try:
			record_time= no_record[i][0]
		except:
			print("no values")
			return "no values retreived for the period! check the parameters and try again!"	
		# count = 1
		listd = []

	#         #######****************  PONTOON********************################

		
		if (device_type == "pontoon"):
			print("no_of_depths",int(no_of_depths))
			# weatherlist = {"atm_temp": 35.1,"wind_speed": 2.5,"wind_direction": 128.5,"relative_humidity": 95,"net_solar": 155.21}
			# print("pontoon")
			cur.execute("select depth from depths_depth where id in(select depth_id from devices_device_depth where device_id = (select id from devices_device where tag = '"+sName+"')) order by depth;")
			depthlist = cur.fetchall()
			print(depthlist)
			print('len',len(depthlist))
			for k in range(len(depthlist)):
				depth = depthlist[k][0]
				print('depth',depth)
				#info= [{"depth_id":" ","temperature":"","pH":"","conductivity":"","chl-a":"","do_conc":"","do_sat":"","tds":"","salinity":"","turbidity":"","depth":""}]
				# for n in range(int(no_of_depths)):
				# print(rec_time)
				cur.execute("Select value_float from device_data where device_tag = '"+sName+ "' and record_time >= '"+rec_time+"' and depth = "+str(depth)+" and parameter_tag in ('Temperature','pH', 'DO_Concentration', 'DO_Saturation', 'Conductivity', 'Turbidity','Chlorophyll-a','TDS','Salinity') order by parameter_tag ")
				# print("Select value_float from device_data where device_tag = '"+sName+ "' and record_time >= '"+rec_time+"' and depth = "+str(depth)+" and parameter_tag in ('Temperature','pH', 'DO_Concentration', 'DO_Saturation', 'Conductivity', 'Turbidity','Chlorophyll-a','TDS','Salinity') order by record_time ")
				res = cur.fetchall()
				# print(res)

				listf = []

				#if there are multiple list the infolist will contain the dteila of all lists
				#have to fetch the sensor values for each lists
				innerlist = res
			
				for j in range(len(innerlist)):
						try:
							# print(innerlist[j][1][i][0])
							listf.append(innerlist[j][0])
							# listf.append(innerlist[j][1][i])
						except:
							listf.append('0.0')
				#print(listf)
				for l in range(len(listf)):
					if(l==0):
						try:
							chl_a = listf[l]
						except:
							chl_a = 0.0
					elif(l==1):
						try:
							conductivity = listf[l]
							
						except:
							conductivity = 0.0
					elif(l==2):
						try:
							do_conc = listf[l]
						except:
							do_conc = 0.0
					elif(l==3):
						try:
							do_sat = listf[l]
						except:
							do_sat = 0.0
					elif(l==4):
						try:
							ph = listf[l]
						except:
							ph = 0.0
					elif(l==5):
						try:
							salinity = listf[l]
						except:
							salinity = 0.0
					elif(l==6):
						try:
							tds= listf[l]
						except:
							tds = 0.0
					elif(l==7):
						try:
							temp = listf[l]
						except:
							temp = 0.0
					elif(l==8):
						try:
							turbidity = listf[l]
						except:
							turbidity = 0.0
					else:#brmoide should come here
						pass
				
				# print('depthid',l+1)
				info= {"depth_id":k+1,"depth":depth,"temperature":temp,"pH":ph,"conductivity":conductivity,"chl-a":chl_a,"do_conc":do_conc,"do_sat":do_sat,"tds":tds,"salinity":salinity,"turbidity":turbidity}
				# count = count+1
				# print((info))
				listd.append(info)
				# print('k',k)
				# print('listd',listd)



                #################**********WATERWAY***********#################
		else:
				cur.execute("Select value_float from device_data where device_tag = '"+sName+ "' and record_time >= '"+rec_time+"' and parameter_tag in ('Temperature','pH', 'DO_Concentration', 'DO_Saturation', 'Conductivity', 'Turbidity','Chlorophyll-a','TDS','Salinity') order by parameter_tag ")
				res = cur.fetchall()
				# print(res)
				# print(len(res))
				listf = []
				innerlist = res
				# print(innerlist)
				for j in range(len(innerlist)):
					try:
						# print(innerlist[j][1][i][0])
						listf.append(innerlist[j][0])
						#print(innerlist[j][1][i])
						# listf.append(innerlist[j][1][i])
					except:
						listf.append('0.0')
				print('listf',listf)
				for l in range(len(listf)):
					if(l==0):
						try:
							chl_aw = listf[l]
						except:
							chl_aw = 0.0
					elif(l==1):
						try:
							conductivityw = listf[l]
						except:
							conductivityw = 0.0
					elif(l==2):
						try:
							do_concw = listf[l]
						except:
							do_concw = 0.0
					elif(l==3):
						try:
							do_satw = listf[l]
						except:
							do_satw = 0.0
					elif(l==4):
						try:
							phw = listf[l]
						except:
							phw = 0.0
					elif(l==5):
						try:
							salinityw = listf[l]
						except:
							salinityw = 0.0
					elif(l==6):						
						try:
							tdsw = listf[l]
						except:
							tdsw = 0.0
					elif(l==7):
						try:
							tempw = listf[l]
						except:
							tempw = 0.0
					elif(l==8):
						try:
							turbidityw = listf[l]
						except:
							turbidityw = 0.0
					else:#brmoide should come here
						pass
					
				print(listf)
				print(tempw)
				print(phw)
				print(do_concw)
				print(do_satw)
				print(conductivityw)
				print(turbidityw)
				print(chl_aw)
				print(tdsw)
				print(salinityw)

				
				info = {"depth_id":"1","depth":"0.5m","temperature":tempw,"pH":phw,"conductivity":conductivityw,"chl-a":chl_aw,"do_conc":do_concw,"do_sat":do_satw,"tds":tdsw,"salinity":salinityw,"turbidity":turbidityw}
				#info= [{"temperature":tempw,"pH":phw,"conductivity":conductivityw,"chl-a":chl_aw,"do_conc":do_concw,"do_sat":do_satw,"tds":tdsw,"salinity":salinityw,"turbidity":turbidityw}]
				# print((info))
				listd.append(info)

		#converting UTC time to SG time 
		# record_time = record_time+timedelta(hours=(+8))
		try:
			record_time = datetime.strftime(record_time,'%Y-%m-%dT%H:%M:%S.%fZ')#datetime.strftime(datetime.strptime(record_time,'%Y-%m-%dT%H:%M:%S.%fZ'),'%Y-%m-%dT%H:%M:%S.%fZ
		except:
			record_time = datetime.strftime(record_time,'%Y-%m-%dT%H:%M:%SZ')

		UTC = pytz.utc
		IST = pytz.timezone('Asia/Singapore')
		# print(type())
		record_time = datetime.strptime(record_time,'%Y-%m-%dT%H:%M:%S.%fZ')
		record_time = record_time+timedelta(hours=(+8))

		#nutc =
		#print(nutc)
		#record_timelcl = (UTC.localize(record_time,is_dst=None)).astimezone(IST)
		try:
			record_timelcl = datetime.strftime(record_time,'%Y-%m-%dT %H:%M:%S.%fZ')
		except:
			record_timelcl = datetime.strftime(record_time,'%Y-%m-%dT %H:%M:%SZ')
			
		# print(listd)
		if(device_type == "pontoon"):
			cur.execute("select count(*) from devices_device where tag = '"+sName+"' and is_weather in ('true')")
			wthrcnt = cur.fetchall()
			print('wthrcnt',wthrcnt)
			if wthrcnt[0][0] == 1:
				cur.execute("Select value_float from device_data where device_tag = '"+sName+"' and parameter_tag in ('Wind_Direction','Wind_Speed','Atmospheric_Temperature','Relative_Humidity','Net_Solar_Radiation') and record_time >= '"+rec_time+"' order by parameter_tag desc")
				weather = cur.fetchall()
				weatherlist = {"atm_temp": weather[4][0],"wind_speed": weather[0][0],"wind_direction": weather[1][0],"relative_humidity": weather[2][0],"net_solar": weather[3][0]}
					#WEATHER DETAILS
			else:
				weatherlist = {}	
			listl = {"station_info":{"station_id":sName,"datetime":record_timelcl,"depths":no_of_depths},
					"water quality units":{"temperature":"degree celcius","pH":"pH","conductivity":"uS/cm","chl-a":"ug/l","do_conc":"mg/l","do_sat":"%","salinity":"PSU","tds":"mg/l","turbidity":"NTU","depth":"m"},
					"weather units":{"atm_temp": "degree celcius","wind_speed": "m/s","wind_direction": "degrees","relative_humidity": "%","net_solar": "W/m2"},
					"wq_data":listd,
					"weather_data":weatherlist}
		else:
			print('listd',listd[0])
			listl = {"station_info":{"station_id":sName,"datetime":record_timelcl,"depths":1},
					"water quality units":{"temperature":"degree celcius","pH":"pH","conductivity":"uS/cm","chl-a":"ug/l","do_conc":"mg/l","do_sat":"%","salinity":"PSU","tds":"mg/l","turbidity":"NTU","depth":"m"},
					"weather units":{"atm_temp": "degree celcius","wind_speed": "m/s","wind_direction": "degrees","relative_humidity": "%","net_solar": "W/m2"},
					"wq_data":listd[0]}
		print('listl',listl)
		
		# listl = list(listl)

		
		listval.append(listl)

		print('listval',listval)

	#--? to validate if there are any data for the passed parameters --- ? #
	#******************#
	cur.close()
	if(no_record == 0):
		return "no values retreived! check the parameters and try again!"
	else:
		
		# if fromdate is None:
		# 	listval = listval[0]

		listdict = {"recordings":listval}
		#print(type(listdict))
		cur.close()
		return listdict	

# route for logging user in
@app.route('/flotechapi/login', methods =['POST'])
def login():
	# creates dictionary of form data
	auth = request.form

	if not auth or not auth.get('name') or not auth.get('password'):
		print(auth.get('name'))
		print("first")
		# returns 401 if any email or / and password is missing
		return make_response(
			'Could not verify',
			401,
			{'WWW-Authenticate' : 'Basic realm ="Login required !!"'}
		)

	user = User.query\
		.filter_by(name = auth.get('name'))\
		.first()
	print(user)
	if not user:
		print("if")
		# returns 401 if user does not exist
		return make_response(
			'Could not verify',
			401,
			{'WWW-Authenticate' : 'Basic realm ="User does not exist !!"'}
		)

	if check_password_hash(user.password, auth.get('password')):
		# generates the JWT Token
		token = jwt.encode({
			'public_id': user.public_id
		}, app.config['SECRET_KEY'])

		print(type(token))

		
		return make_response(jsonify({'token' : token.decode('UTF-8')}), 201)# commented for testing on local
	# returns 403 if password is wrong
	return make_response(
		'Could not verify',
		403,
		{'WWW-Authenticate' : 'Basic realm ="Wrong Password !!"'}
	)

# signup route
@app.route('/flotechapi/signup', methods =['POST'])
def signup():
	# creates a dictionary of the form data
	data = request.form

	# gets name, email and password
	name, email = data.get('name'), data.get('email')
	password = data.get('password')

	
	# checking for existing user
	user = User.query\
		.filter_by(email = email)\
		.first()
	if not user:
		# database ORM object
		user = User(
			public_id = str(uuid.uuid4()),
			name = name,
			email = email,
			password = generate_password_hash(password)
		)
		# insert user
		db.session.add(user)
		db.session.commit()

		return make_response('Successfully registered.', 201)
	else:
		# returns 202 if user already exists
		return make_response('User already exists. Please Log in.', 202)

def checkdate():

    # handling the data using tiny db
    Todo = Query()
    datadb = TinyDB('user.json') # tiny db refreshes data once server refreshed ???????????
    user = os.getlogin() # get the current system user

    cdate = datetime.now()

    #formatting date
    date = datetime.strftime(cdate,'%d:%m:%Y')
    date_time = datetime.strftime(cdate,'%d:%m:%Y %H:%M:%S.%f')
    
    #get the count of existing data for the same user and date
    dcount = datadb.count((Todo.date == date ) & (Todo.user==user))
    #print(dcount)

    #get the existing date and time for the same user
    olddate = [i["date and time"] for i in datadb.search(Todo.user==user and Todo.date==date)]

    #formattingtime
    time = datetime.strftime(cdate,'%H:%M:%S')

    #remove data if the date is not today(to delete old data from the table)
    datadb.remove(Todo.date != date )

    #if there is already a a record of the user for the same user, 
    #api would fetch the latest data and update the time against the same user
    if(dcount == 0):
      datadb.insert({'user':user,'date':date,'date and time':date_time})
    else:
      datadb.update({'date':date,'date and time':date_time},Todo.user==user)

    if(olddate)== [] :
    
      return None
    else:
      return (olddate)

## geeks for geeks source
# Python code to merge dict using update() method
def Merge(dict1, dict2):
    return(dict2.update(dict1))

if __name__ == "__main__":
	app.run(host="0.0.0.0",debug = True)
    
