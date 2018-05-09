import csv
import sys
import requests
import tesserocr
from PIL import Image
from bs4 import BeautifulSoup

baseURL = 'https://www.ccxp.nthu.edu.tw/ccxp/INQUIRE/JH/6/6.2/6.2.9/JH629001.php'
resultURL = 'https://www.ccxp.nthu.edu.tw/ccxp/INQUIRE/JH/6/6.2/6.2.9/JH629002.php'

# Crawl the name and abbr of the dept from baseURL

deptNameTW = []    # chinese department name
deptNameEN = []    # english department name
deptNameAbbr = []  # department abbreviation

response = requests.get(baseURL)
response.encoding = 'big5' # baseURL is encoded by 'big-5'
soup = BeautifulSoup(response.text, 'html.parser')
dept = soup.find('select', attrs={"name": "dept"})
optionTags = dept.findChildren()

init = False

# DEPT. Crawler

for optionTag in optionTags:
	# Skip the first option tag
	if init is False:
		init = True
		continue
	temp = optionTag.text.split()
	deptNameAbbr.append(temp[0])
	deptNameTW.append(temp[1])
	k = 2;
	str = ''

	while k < len(temp):
		str = str + temp[k] + ' '
		k = k+1

	deptNameEN.append(str)

# Course Crawler

## Access URL

isAccessed = False

### php Attrbs

payload = {
	'ACIXSTORE': 'l2stqej6nluuahonkvdlc5kac5',
	'YS': '106|10',
	'cond': 'a',
	'cou_code': 'ANTH',
	'auth_num': '',
	'chks':''
}

def Binarize(img, threshold):
	img = img.convert("L")
	pixdata = img.load()
	w, h = img.size
	for y in range(h):
		for x in range(w):
			if pixdata[x, y] < threshold:
				pixdata[x, y] = 0
			else:
				pixdata[x, y] = 255
	return img

while isAccessed is False:

	img = soup.findAll('img')
	imgSRC = img[0].attrs['src']

	imgSRC = 'https://www.ccxp.nthu.edu.tw/ccxp/INQUIRE/JH/' + imgSRC[9:]

	img = requests.get(imgSRC)

	with open('auth.png', 'wb') as f:
		f.write(img.content)
		f.close()


	authPIC = Image.open('auth.png')

	authPIC = Binarize(authPIC, 150)

	# authPIC.show()

	auth_num = tesserocr.image_to_text(authPIC)

	ACIXSTORE = soup.findAll('input')[0].attrs['value']

	payload['ACIXSTORE'] = ACIXSTORE
	payload['auth_num'] = auth_num[0:3]

	res = requests.post(resultURL, data = payload)
	res.encoding = 'big5'
	soup = BeautifulSoup(res.text, 'html.parser')
	try:
		req = soup.findAll('title')[0].text
		isAccessed = True
		print('Access the URL')
	except:
		print('Can\'t Access the URL')
		response = requests.get(baseURL)
		response.encoding = 'big5'
		soup = BeautifulSoup(response.text, 'html.parser')


# CRAWL Courses and write to csv file

with open('course_10610.csv', 'w', newline='') as csvfile:

	writer = csv.writer(csvfile)
	rowID = -1
	for dept in deptNameAbbr:
		rowID = rowID + 1
		payload['cou_code'] = dept
		res = requests.post(resultURL, data = payload)
		res.encoding = 'big5'
		soup = BeautifulSoup(res.text, 'html.parser')
		req = soup.findAll('title')[0].text
		tb = soup.find('table')
		# print (tb)
		tr = tb.findAll('tr')
		i = 0
		for td in tr[4:]:
			isWrited = 0
			colSTR = td.text
			courseID = td.text.split('\n')
			if courseID[1] is not '':
				print (courseID[1])
				isWrited = isWrited + 1
			courseName = courseID[3][12:]
			checkNum = 0
			for word in courseName:
				if word.lower() <= 'z' and word.lower() >= 'a':
					break
				checkNum = checkNum + 1
			courseNameTW = courseName[0:checkNum]
			courseNameEN = courseName[checkNum:]
			if courseNameTW is not '':
				print (courseNameTW)
				isWrited = isWrited + 1
			if courseNameEN is not '':
				print (courseNameEN)
				isWrited = isWrited + 1
			try:
				# print (courseID[9])
				professorName = courseID[9]
				checkNum = 0
				for word in professorName:
					if (ord(word) <= 255):
						break
					checkNum = checkNum + 1
				professorNameTW = professorName[0:checkNum]
				professorNameEN = professorName[checkNum:]
				if professorNameTW is not '':
					print (professorNameTW)
					isWrited = isWrited + 1
				if professorNameEN is not '':
					print (professorNameEN)
					isWrited = isWrited + 1
				if isWrited is 5:
					writer.writerow([dept, deptNameTW[rowID], deptNameEN[rowID], courseID[1], courseNameTW, courseNameEN, professorNameTW, professorNameEN])
			except:
				temp = ''
