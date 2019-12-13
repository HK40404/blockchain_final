import re
import json
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.template import loader
from django.http import HttpResponseRedirect

from Chain import ChainManager

def test(request):
	print(ChainManager().queryReceipt("asd"))
	return HttpResponse('Hello, django')

def menu(request):
	if not request.session.get('Username'):
		return HttpResponseRedirect('login')
	else:
		return render(request, 'menu.html')

def login(request):
	context = {}
	if request.method == 'POST':
		username = request.POST['Username']
		password = request.POST['Password']
		ret = ChainManager().login(username, password)
		if ret:
			context['error_message'] = "用户名或密码错误"
		else:
			context['error_message'] = "登录成功"
			request.session['Username'] = username
			request.session['Password'] = password
			return HttpResponseRedirect('menu')
	return render(request, 'login.html', context)

def register(request):
	context = {}
	if request.method == 'POST':
		username = request.POST['Username']
		password = request.POST['Password']

		# 用户名：1~12位的字母/数字
		# 密码：6~18位的字母/数字
		pattern_name = re.compile(r"^\w{1,12}$")
		pattern_pass = re.compile(r"^\w{6,18}$")
		if not pattern_name.match(username):
			context['error_message'] = "用户名必须为1~12位的字母/数字"
		elif not pattern_pass.match(password):
			context['error_message'] = "密码必须为6~12位的字母/数字"
		else:
			ret = ChainManager().register(username, password)
			if ret == -1:
				context['error_message'] = "用户已经存在"
			elif ret == -2:
				context['error_message'] = "出现了未知错误，请重试！"
			else:
				return HttpResponseRedirect('login')
	return render(request, 'register.html', context)

def signature(request):
	# 该函数仅供开发测试
	context = {}
	if request.method == 'POST':
		info = request.POST['info']
		v,r,s = ChainManager().sign('bank', 'bank', info)
		context['v'] = v
		context['r'] = r
		context['s'] = s
	return render(request, 'signature.html', context)

def registerCom(request):
	context = {}
	if request.method == 'POST':
		if not request.session.get('Username'):
			context['error_message'] = "请先登录"
		else:
			username = request.session.get('Username')
			password = request.session.get('Password')
			cm = ChainManager()
			if cm.login(username, password) == -1:
				context['error_message'] = "用户信息错误，请重新登录"
			else:
				name = request.POST['name']
				addr = request.POST['address']
				credit = request.POST['credit']
				comtype = request.POST['type']
				v = int(request.POST['v'])
				r = int(request.POST['r'])
				s = int(request.POST['s'])
				ret = cm.registerCom(username, name, addr, credit, comtype, (v,r,s))
				del cm
				if ret == 0:
					context['error_message'] = "注册成功"
				elif ret == -4:
					context['error_message'] = "vrs错误，请重新核对"
				elif ret == -1:
					context['error_message'] = "公司已存在"
				else:
					context['error_message'] = "未知错误"
	return render(request, 'registerCompany.html', context)

def queryCom(request):
	context = {}
	if request.method == 'POST':
		name = request.POST['name']
		ret = ChainManager().queryCom(name)
		if ret == -1:
			context['error_message'] = "公司不存在"
			return render(request, 'queryCompany.html', context)
		else:
			context['name'] = ret[0]
			context['owner'] = ret[1]
			context['addr'] = ret[2]
			context['credit'] = ret[3]
			context['type'] = ret[4]
			return render(request, 'company.html', context)

	return render(request, 'queryCompany.html', context)

def eraseCom(request):
	context = {}
	if request.method == 'POST':
		if not request.session.get('Username'):
			context['error_message'] = "请先登录"
		else:
			username = request.session.get('Username')
			password = request.session.get('Password')
			cm = ChainManager()
			if cm.login(username, password) == -1:
				context['error_message'] = "用户信息错误"
			else:
				name = request.POST['name']
				ret = cm.eraseCom(name)
				del cm
				if ret == 0:
					context['error_message'] = "注销成功"
				elif ret == -1:
					context['error_message'] = "公司不存在"
				elif ret == -2:
					context['error_message'] = "无权限注销"
				else:
					context['error_message'] = "未知错误"
	return render(request, 'eraseCompany.html', context)

def createReceipt(request):
	context = {}
	if request.method == 'POST':
		if not request.session.get('Username'):
			context['error_message'] = "请先登录"
		else:
			username = request.session.get('Username')
			password = request.session.get('Password')
			cm = ChainManager()
			if cm.login(username, password) == -1:
				context['error_message'] = "用户信息错误，请重新登录"
			else:
				title = request.POST['title']
				fromc = request.POST['from']
				to = request.POST['to']
				amount = int(request.POST['amount'])
				lasttime = int(request.POST['lasttime'])
				comment = request.POST['comment']
				vrs = None
				if request.POST['v']:
					v = int(request.POST['v'])
					r = int(request.POST['r'])
					s = int(request.POST['s'])
					vrs = (v,r,s)

				ret = cm.createReceipt(title, fromc, to, amount, lasttime, comment, vrs=vrs)
				del cm
				if ret == 0:
					context['error_message'] = "账款创建成功"
				elif ret == -1:
					context['error_message'] = "账款名已使用"
				elif ret == -2:
					context['error_message'] = "欠款公司和收款公司不能为同一公司"
				elif ret == -3:
					context['error_message'] = "欠款公司或收款公司未在链上注册"
				elif ret == -5:
					context['error_message'] = "账款必须由欠款公司所有者创建"
				else:
					context['error_message'] = "未知错误"
	return render(request, 'createReceipt.html', context)

def queryReceipt(request):
	context = {}
	if request.method == 'POST':
		title = request.POST['title']
		ret = ChainManager().queryReceipt(title)
		if ret == -1:
			context['error_message'] = "账款不存在"
			return render(request, 'queryReceipt.html', context)
		else:
			context['title'] = ret[0]
			context['from'] = ret[1]
			context['to'] = ret[2]
			context['amount'] = ret[3]
			context['createtime'] = ret[4]
			context['lasttime'] = ret[5]
			if ret[6]:
				context['confirm'] = "是"
			else:
				context['confirm'] = "否"
			context['comment'] = ret[7]
			return render(request, 'receipt.html', context)

	return render(request, 'queryReceipt.html', context)

def queryReceiptOfCom(request):
	context = {}
	if request.method == 'POST':
		name = request.POST['name']
		isfrom = True if request.POST['from'] == "1" else False
		ret = ChainManager().queryReceiptOfCom(name, isfrom)
		context['receipts'] = ret
		return render(request, 'companyReceipt.html', context)
	return render(request, 'queryReceiptOfCompany.html', context)


def transferReceipt(request):
	context = {}
	if request.method == 'POST':
		if not request.session.get('Username'):
			context['error_message'] = "请先登录"
		else:
			username = request.session.get('Username')
			password = request.session.get('Password')
			cm = ChainManager()
			if cm.login(username, password) == -1:
				context['error_message'] = "用户信息错误"
			else:
				title = request.POST['title']
				newamount = int(request.POST['amount'])
				newtitle = request.POST['newtitle']
				ret = cm.queryReceipt(title)

				if ret == -1:
					context['error_message'] = "账款不存在"
				else:
					fromc = ret[1]
					middle = ret[2]
					amount = int(ret[3])
					to = request.POST['to']
					if newamount > amount:
						context['error_message'] = "账款余额不足"
					ret = cm.transferReceipt(title, fromc, middle, to, newamount, newtitle)
					del cm
					if ret == 0:
						context['error_message'] = "转让成功"
					elif ret == -1:
						context['error_message'] = "待转让公司不存在"
					elif ret == -3:
						context['error_message'] = "转让人非公司所有者"
					elif ret == -5:
						context['error_message'] = "转让公司与被转让公司相同"
					else:
						context['error_message'] = "未知错误"
	return render(request, 'transferReceipt.html', context)

def deleteReceipt(request):
	context = {}
	if request.method == 'POST':
		if not request.session.get('Username'):
			context['error_message'] = "请先登录"
		else:
			username = request.session.get('Username')
			password = request.session.get('Password')
			cm = ChainManager()
			if cm.login(username, password) == -1:
				context['error_message'] = "用户信息错误"
			else:
				title = request.POST['title']
				ret = cm.deleteReceipt(title)
				if ret == 1:
					context['error_message'] = "账款注销成功"
				elif ret == -1:
					context['error_message'] = "账款不存在"
				elif ret == -2:
					context['error_message'] = "非账款收款方，无法注销"
				else:
					context['error_message'] = "未知错误"
	return render(request, 'deleteReceipt.html', context)

