import requests, time, json, pickle, os, re
import urllib.request, urllib.error
from urllib.parse import urlparse
from pyquery import PyQuery as pq

extensions = {".jpg", ".png", ".gif"}

headers = { 
	"Origin"
	"Content-Type":"application/x-www-form-urlencoded",
	"Upgrade-Insecure-Requests":"1",
	"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
	"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3"
	}

payload = {
	"authenticity_token": "H5iRnH9pwj9RWUUKWigQzoHCN4AIzsPYa65xRqQcDnkwkIEhK9NIxn0i1upyWaxlMCkznXg9VHH3tuA2Xz7I/Q==",
	"commit":"",
	"user[email]":"",
	"user[password]":"",
	"utf8":"1"
}

urlLogin = "http://learn.ironhack.com/users/sign_in"
urlToken = "http://learn.ironhack.com/"
lessonsAllCourses = []

style = """
		<style type='text/css'>
		.container {
		    margin: 0 auto;
		    text-align: center;
		    width: 30%;
		}
		.lesson {
		    padding: 7px;
		    background: #88ceff;
		    border: 2px solid white;
		    border-radius: 10px;
		}
		a.shortcut {
		    color: white;
		    text-transform: uppercase;
		    font-weight: bold;
		    font-family: sans-serif;
		    text-decoration: none;
		}
		h2.header {
		    text-transform: uppercase;
		    width: 75%;
		    margin: 0 auto;
		    color: white;
		}
		</style>
		"""

#################### CREATE FOLDER FILES ##############
def initializeFolder(folderName):
	if not os.path.isdir(folderName):
		os.mkdir(folderName)
	# Initialize img folder
	print("Initialize img folder")
	if os.path.isdir(folderName+"\\"+"img"):
		print("Skip img folder")
		return
	else:
		print("Create folder img")
		os.mkdir(folderName+"\\"+"img")
		return

def getImagesAndReplaceContent(folderName,content):
	for url in re.findall('http\S+?/\S+?\.(?:jpg|jpeg|gif|png)',str(content)):
		# download IMG
		#print(url)
		fileName = re.findall('(?<=/)[\w\-\_]+\.(?:jpg|jpeg|gif|png)', url)[0]
		#print(fileName)
		try:
			urllib.request.urlretrieve(url, folderName + "\\"+fileName)
			# replace in content to local
			content=content.replace(url.encode('utf-8'), ("<img src='" + folderName + "/" + fileName + "'>").encode('utf-8'))
		except urllib.error.HTTPError as e:
			print(e.__dict__)
		except urllib.error.URLError as e:
			print(e.__dict__)
	return content

def initializeFile(folderName, namefile,content,header='N'):
	filename = str(namefile).replace("|","").replace("?","").replace("\\","").replace("/","").replace("#","").replace(":","")+".html"
	#filename = filename.encode('ascii',errors='ignore')
	if os.path.isfile(folderName+"\\"+filename):
		print("File already created, skipping create...")
		
	else:
		print("Indexing file...")
		## No header => Create file
		if header=='N':
			nameToShow = filename.replace(".html","")
			link = "<a class='shortcut' href='"+filename+"'>"+ str(nameToShow[nameToShow.find(")")+1: ]) +"</a>"
			print("Creating "+str(filename)+"...")
			## Extract images
			# content = getImagesAndReplaceContent(folderName+"\\"+"img",content)
			
			## Replace URL to local URL

			with open(folderName+"\\"+str(filename), 'wb') as f:
				f.write(content)
		else:
			link="<h2 class='header'>"+content+"</h2>"

		## Create index file if not exist or append
		if os.path.isfile(folderName+"\\"+"(0000) - Index - "+folderName+".html"):
			appendSomethingInFile(folderName+"\\"+"(0000) - Index - "+folderName+".html",link)

		else:
			with open(folderName+"\\"+"(0000) - Index - "+folderName+".html", 'w') as f:
				f.write(link)
		## END INDEX ##


	return
	
#################### END CREATE   #####################
#################### START LOGIN ######################

def loadPreviousCookie(session):
	with open('cookieIronhack', 'rb') as f:
		session.cookies.update(pickle.load(f))
	return session

def saveCookie(session):
	with open('cookieIronhack', 'wb') as f:
		pickle.dump(session.cookies, f)
	return session

def getToken(s):
	data = s.get(url=urlToken, headers=headers)
	token = pq(data.content)("meta[name=csrf-token]").attr("content")
	return token

def login(s):
	print("Logging in...")
	payload['authenticity_token'] = getToken(s)
	s.headers.update(headers)
	result = s.post(url=urlLogin, headers=headers, data=payload)
	saveCookie(s)
	return s

###################### END LOGIN ######################

# Return courses of student
def getCourse(s):
	courses = json.loads(s.get(url="http://learn.ironhack.com/api/course_editions", headers=headers).content)
	coursesArray = []

	for course in courses['course_editions']:
		coursesArray.append(course['edition_id'])
	return coursesArray

# Return ID of lessons
def getIDsLessonsCourse(s,course):
	course = json.loads(s.get(url="http://learn.ironhack.com/api/course_editions/"+str(course), headers=headers).content)
	return course

# Get iFrame URL
def getRealURLFromID(s,idLesson):
	realURL = json.loads(s.get(url="http://learn.ironhack.com/api/learning_units/"+str(idLesson), headers=headers).content)
	
	if len(realURL['resources']) > 0:
		url = realURL['resources'][0]['content']
	else:
		return ''

	if url!= '':
		UrlToReturn = str(realURL['resources'][0]['content'].replace("<iframe src='","")\
															.replace("'></iframe>","")\
															.replace('<iframe src="',"")\
															.replace('"></iframe>',""))
		return UrlToReturn
	else:
		return ''

def appendSomethingInFile(url,content):
	with open(url,'a') as f:
		f.write(content)
	return

def getLessonsDataFromIDs(s,lessonsAllCourses):
	dataWebIframe = {}
	# One element per course
	# COURSE[] => { LESSON['MODULES'] : { SUBLESSON }}
	for lessonId,lessonOneCourse in enumerate(lessonsAllCourses):
		
		dataWebIframe[lessonOneCourse['title']] = {}
		folderName = lessonOneCourse['title'].replace("\\","-").replace("/","-").replace("|","-")
		fileNameIndex = "(0000) - Index - "+folderName+".html"
		pathIndex = folderName+"\\"+fileNameIndex
		
		initializeFolder(folderName)
		appendSomethingInFile(pathIndex,style)
		appendSomethingInFile(pathIndex,"<div class='container'>")

		for idxModule, module in enumerate(lessonOneCourse['modules']):
			dataWebIframe[lessonOneCourse['title']][str(idxModule) + " - "+module['title']] = {}

			# All learning units inside module
			counterLessons = 0
			counterSubLessons = 1
			for idxUnit, learning_unit in enumerate(module['learning_units']):

				appendSomethingInFile(pathIndex,"<div class='lesson'>")
				if learning_unit['lab_url'] is None or learning_unit['lab_url']=='':
					realURLFromID = getRealURLFromID(s,learning_unit['id'],)
				else:
					realURLFromID = learning_unit['lab_url']

				# No RealURL -> Its header
				if realURLFromID != '':
					dataWebIframe[lessonOneCourse['title']][str(idxModule) + " - "+module['title']][str(idxUnit)+" - "+learning_unit['title']] = realURLFromID
					initializeFile(folderName, "("+str(learning_unit['id'])+") "+str(counterLessons)\
													    +"."+str(counterSubLessons)\
													    +" - "+learning_unit['title'],s.get(url=realURLFromID, headers=headers).content)
					counterSubLessons += 1
				else:
					dataWebIframe[lessonOneCourse['title']][str(idxModule) + " - "+module['title']][str(idxUnit)+" - "+learning_unit['title']] = 'header'
					initializeFile(folderName, "("+str(learning_unit['id'])+") "+str(counterLessons)+"."+str(counterSubLessons)+" - "+learning_unit['title'],learning_unit['title'],'Y')
					counterLessons += 1
					counterSubLessons = 1

				time.sleep(1)
				appendSomethingInFile(pathIndex,"</div>")

			appendSomethingInFile(pathIndex,"---------------------------------------------------------------------------")
				
		appendSomethingInFile(pathIndex,"</div>")
	print("End! - Open index file and learn. Thanks Ironhack!")			
	return

def main():
	s = requests.session()
	print("Logging in...")

	# if have cookie
	#s = loadPreviousCookie(s)
	# else and login with data input and save cookie
	s = login(s)
	print("Logged, starting...")

	#Get Courses of User and iterate
	for course in getCourse(s):
		# Get IDs of Lessons for scrap
		lessonsAllCourses.append(getIDsLessonsCourse(s,course))

	# Iterate and get URL's of each iframe
	getLessonsDataFromIDs(s,lessonsAllCourses)
	return

if __name__ == '__main__':
	print("Extractor ")
	payload["user[email]"] = input("Inserta tu email: \n")
	payload["user[password]"] = input("Inserta tu password: \n")
	main()