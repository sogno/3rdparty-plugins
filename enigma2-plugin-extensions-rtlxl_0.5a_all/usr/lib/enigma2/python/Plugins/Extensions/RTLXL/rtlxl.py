from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.Label import Label
from Components.ActionMap import NumberActionMap, ActionMap
from twisted.internet import reactor, defer
from twisted.web import client
from twisted.web.client import HTTPClientFactory, getPage, downloadPage
from Screens.MessageBox import MessageBox
import xml.etree.cElementTree
import string
import os
from urllib import quote

from Components.ServiceEventTracker import ServiceEventTracker
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarNotifications, InfoBarCueSheetSupport
from enigma import eTPM, eTimer, ePoint, ePicLoad, eServiceReference, iPlayableService



class RTLXLMENU(Screen):
	skin = """
		<screen position="center,center" size="360,380" title="RTL XL" >
			<widget name="list" position="10,0" size="340,280" scrollbarMode="showOnDemand" />
			<widget name="Text" position="center,280" size="360,100" halign="center" font="Regular;22" />
                </screen>"""
		
	def __init__(self, session, args = 0):
		self.session = session
		Screen.__init__(self, session)
		
		self["list"] = MenuList([])		
		self["Text"] = Label("=--RTL XL App {NETTV}--=\nMade by DEG 2012~!")
		self["myActionMap"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.cancel}, -1)
		self.onLayoutFinish.append(self.flist)

	def cancel(self):
		self.close(None)
		
	def okClicked(self):
		iday = self["list"].getSelectionIndex()
		url = self.urlt[iday]
		self.session.open(secondmenu, url)
		
	def flist(self):
		self.rtldays = []
		self.urlt = []
		
		self.rtldays.append("Maandag")
		self.rtldays.append("Dinsdag")
		self.rtldays.append("Woensdag")
		self.rtldays.append("Donderdag")
		self.rtldays.append("Vrijdag")
		self.rtldays.append("Zaterdag")
		self.rtldays.append("Zondag")
		
		self.urlt.append("http://www.rtl.nl/service/gemist/device/philips/index.xml?day=1&grid=0")
		self.urlt.append("http://www.rtl.nl/service/gemist/device/philips/index.xml?day=2&grid=0")
		self.urlt.append("http://www.rtl.nl/service/gemist/device/philips/index.xml?day=3&grid=0")
		self.urlt.append("http://www.rtl.nl/service/gemist/device/philips/index.xml?day=4&grid=0")
		self.urlt.append("http://www.rtl.nl/service/gemist/device/philips/index.xml?day=5&grid=0")
		self.urlt.append("http://www.rtl.nl/service/gemist/device/philips/index.xml?day=6&grid=0")
		self.urlt.append("http://www.rtl.nl/service/gemist/device/philips/index.xml?day=7&grid=0")
		self["list"].setList(self.rtldays)
	
###

class myHTTPClientFactory(HTTPClientFactory):
	def __init__(self, url, method='GET', postdata=None, headers=None, agent="Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.102011-10-16 20:23:10", timeout=0, cookies=None, followRedirect=1, lastModified=None, etag=None):
		HTTPClientFactory.__init__(self, url, method=method, postdata=postdata,	headers=headers, agent=agent, timeout=timeout, cookies=cookies, followRedirect=followRedirect)

	def clientConnectionLost(self, connector, reason):
		lostreason=("Connection was closed cleanly" in vars(reason))
		if lostreason==None:
			print"[SHOUTcast] Lost connection, reason: %s ,trying to reconnect!" %reason
			connector.connect()

	def clientConnectionFailed(self, connector, reason):
		print"[SHOUTcast] connection failed, reason: %s,trying to reconnect!" %reason
		connector.connect()

def sendUrlCommand(url, contextFactory=None, timeout=60, *args, **kwargs):
	scheme, host, port, path = client._parse(url)
	factory = myHTTPClientFactory(url, *args, **kwargs)
	# print "scheme=%s host=%s port=%s path=%s\n" % (scheme, host, port, path)
	reactor.connectTCP(host, port, factory, timeout=timeout)
	return factory.deferred
	
####
		
class secondmenu(Screen):
	
	
	skin = """
		<screen position="center,center" size="570,480" title="RTL XL" >
			<widget name="list" position="10,0" size="550,370" scrollbarMode="showOnDemand" />
			<widget name="Text" position="center,400" size="570,80" halign="center" font="Regular;22" />
		</screen>"""
	
	def __init__(self, session, url):
		self.skin = secondmenu.skin
		Screen.__init__(self, session)
		
		self["list"] = MenuList([])
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.cancel}, -1)
		self.options = []
		self.url = url
		self.srefOld = None
		#self.path = "/tmp/DEG.bak"
		self["Text"] = Label("=--RTL XL App {NETTV}--=\nMade by DEG 2012~!")
		self.hrefpage = ' '
		try:
			self.onLayoutFinish.append(self.downloadList)
		except:
			self["Text"].setText(_("Error fill list") )
		
	def cancel(self):
		#if self.srefOld is not None:
		#	self.session.nav.playService(self.srefOld)
		self.close(None)
		                                
	def downloadList(self):
		#url = "http://rtl.nl/service/gemist/dataset_xml.xml"
		#url = "http://api.shoutcast.com/legacy/stationsearch?k=fa1jo93O_raeF0v9&f&search=hardcore"
		#url = "http://api.shoutcast.com/genre/secondary?parentid=0&k=fa1jo93O_raeF0v9&f=xml"
		self.hreflist = []
		self.namelist = []
		self.hrefpage = ' '
		try:
			sendUrlCommand(self.url, None,10).addCallback(self.callbackGenreList).addErrback(self.callbackGenreListError)
		except:
			self["Text"].setText(_("Error download list") )
		
                #getPage(self.url).addCallback(self.downloadListCallback).addErrback(self.downloadListError)
        
	def callbackGenreListError(self, error = None):
		if error is not None:
			try:
				self["Text"].setText(_("Error getting list\n%s") % str(error.getErrorMessage()) )
			except:
				pass
		
	def callbackGenreList(self, xmlstring):
		root = xml.etree.cElementTree.fromstring(xmlstring)
		
		
		print('xml loaded' )
		self.hrefpage = ' '
		

		for froot in root.findall('{http://www.w3.org/1999/xhtml}body'):
			for childs in froot.findall('{http://www.w3.org/1999/xhtml}div'):
				for childs2 in childs.findall('{http://www.w3.org/1999/xhtml}div'):
					childs21 = str(childs2.get('class'))
					if childs21 == 'content':
						for childs3 in childs2.findall('{http://www.w3.org/1999/xhtml}div'):
							childs6 = str(childs3.get('class'))
							if childs6 == 'nblr':
								for nextpage in childs3.findall('{http://www.w3.org/1999/xhtml}a'):
									childs7 = str(nextpage.get('class'))
									if childs7 == 'bn':
										self.hrefpage = str(nextpage.get('href'))
							elif childs6 == 'gridholder':
								for childs4 in childs3.findall('{http://www.w3.org/1999/xhtml}div'):
									for childs5 in childs4.findall('{http://www.w3.org/1999/xhtml}a'):
										hrefraw = str(childs5.get('href'))
										f1 = hrefraw.find('video=',0)
										f2 = hrefraw.find('.mp4', (f1+6))
										f3 = hrefraw.find('&t=', 0)
										href = hrefraw[(f1+6):(f2+4)]
										title = hrefraw[(f3+3):]
										title = title.replace('%20',' ')
										title = title.replace('%28','(')
										title = title.replace('%29',')')
										title = title.replace('%2F','/')
										title = title.replace('%3A',':')
										title = title.replace('%2C',',')
										title = title.replace('%26','&')
										title = title.replace('%3F','?')
										title = title.replace('%21','!')
										title = title.replace('%27',"'")
										self.hreflist.append(href)
										self.namelist.append(title)
										print('title: %s; ' % (title))						
		
		if self.hrefpage == ' ':
			print('Generate list')
			self["list"].setList(self.namelist)
		else:
			urlpage = ('http://www.rtl.nl/service/gemist/device/philips/index.xml' + self.hrefpage)
			self.hrefpage = ' '
			sendUrlCommand(urlpage, None,10).addCallback(self.callbackGenreList).addErrback(self.callbackGenreListError)
		

			
			
	def okClicked(self):
		ioptie = self["list"].getSelectionIndex()
		title = self.namelist[ioptie]
		hrefurl = self.hreflist[ioptie]
		ipadurl = "http://us.rtl.nl/rtlxl/network/ipad/progressive"
		a3turl = "http://us.rtl.nl/rtlxl/network/a3t/progressive"
		nettv = "http://iptv.rtl.nl/nettv/"
		self.mp4url = (nettv + hrefurl)
		#self.mp4url[j] = (part1 + part2 + "/" + uuid + ".ssm/" + uuid + ".mp4")
		#http://us.rtl.nl/rtlxl/network/ipad/progressive/components/sport/vioranje/278870/692ee485-45a4-3399-ae33-5341f7784866.ssm/692ee485-45a4-3399-ae33-5341f7784866.mp4
		#uuid 692ee485-45a4-3399-ae33-5341f7784866
		#component uri /components/sport/vioranje/miMedia/278870/278882.s4m.56202856.De_Zomer_Van_4_Vi_Oranje_s2_a12.xml
		#http://us.rtl.nl/rtlxl/network/ipad/progressive
		#http://us.rtl.nl/rtlxl/network/a3t/progressive
		#http://iptv.rtl.nl/ipadxlapp/
		self.title = title
		#self.mp4url = (ipadurl + partcompo + seasonkey + "/" + uuid + ".ssm/" + uuid +".mp4")
		#print('mp4 url: %s; ' % (self.mp4url))
		self.old()
		
	def old(self):
		self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
		print("srefOLD = %s" %(self.srefOld))
		self.session.nav.stopService()
		print("srefOLD STOPPED!!" )
		#self.play()
		nowplay = self.mp4url
		#nowplay = "http://odi.omroep.nl/video/hbbtv/h264_std/bb0901faf348a99f363bea21d3f50b8c/4fe06043/AVRO_1520871/1?type=http"
		#nowplay = "http://iptv.rtl.nl/nettv/20120522063943_b3e45143996133b1af5d7e9336975b02.mp4"
		if nowplay is not None:
			mysref = eServiceReference(4097,0,nowplay)
			mysref.setName(self.title)
			#print("/n myref = %s" %(mysref))
			#self.session.nav.playService(mysref)
			self.session.open(RtlPlayer, mysref, self.srefOld)
		else:
			self.session.open(MessageBox, _("Sorry, video is not available!"), MessageBox.TYPE_INFO)
		
	
                
                
class RtlPlayer(Screen, InfoBarNotifications, InfoBarCueSheetSupport, InfoBarSeek):
	STATE_IDLE = 0
	STATE_PLAYING = 1
	STATE_PAUSED = 2
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True
	
	skin = """<screen name="RTLXL-Player" position="0,45" size="1280,100" backgroundColor="transparent" title="RTLXL-Player" flags="wfNoBorder">
    <widget source="session.CurrentService" render="Label" position="224,4" size="832,52" backgroundColor="transparent" zPosition="1" foregroundColor="foreground" borderWidth="2" font="Regular;24" borderColor="black" valign="center" halign="center">
      <convert type="ServiceName">Name</convert>
    </widget>
    <eLabel backgroundColor="infobarBG" position="120,56" size="1040,14" zPosition="0"/>
    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/RTLXL/scale1024.png" position="128,61" size="1024,4" zPosition="1" />
    <widget source="session.CurrentService" render="PositionGauge" position="128,57" size="1024,12" transparent="1" zPosition="4" pointer="/usr/lib/enigma2/python/Plugins/Extensions/RTLXL/position_pointer1024.png:1012,0">
      <convert type="ServicePosition">Gauge</convert>
    </widget>
    <widget source="session.CurrentService" render="Label" position="128,31" size="90,25" backgroundColor="transparent" zPosition="4" foregroundColor="foreground" borderWidth="2" font="Regular;22" borderColor="black" valign="center" halign="left">
      <convert type="ServicePosition">Position,ShowHours</convert>
    </widget>
    <widget source="session.CurrentService" render="Label" position="1035,31" size="117,25" backgroundColor="transparent" zPosition="4" foregroundColor="foreground" borderWidth="2" font="Regular;22" borderColor="black" valign="center" halign="right">
      <convert type="ServicePosition">Remaining,Negate,ShowHours</convert>
    </widget>
    <widget source="global.CurrentTime" render="Label" borderWidth="2" position="1052,3" size="100,25" backgroundColor="transparent" noWrap="1" zPosition="1" foregroundColor="foreground" font="Regular;22" valign="center" halign="right">
      <convert type="ClockToText">Format:%-H:%M</convert>
    </widget>
  </screen>"""
		
	def __init__(self, session, service, oldsref):
		self.skin = RtlPlayer.skin
		Screen.__init__(self, session)
		InfoBarNotifications.__init__(self)
		InfoBarCueSheetSupport.__init__(self, actionmap = "MediaPlayerCueSheetActions")

		
		self.session = session
		self.service = service
		self.oldservice = oldsref
		self.screen_timeout = 5000
		self.nextservice = None
		
		print "evEOF=%d" % iPlayableService.evEOF
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
			{
				iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged,
				iPlayableService.evStart: self.__serviceStarted,
				iPlayableService.evEOF: self.__evEOF,
			})
		
		self["actions"] = ActionMap(["OkCancelActions", "InfobarSeekActions", "MediaPlayerActions", "MovieSelectionActions"],
		{
				"ok": self.ok,
				"cancel": self.leavePlayer,
				"stop": self.leavePlayer,
				"playpauseService": self.playpauseService,
				"play": self.playpauseService,
				"pause": self.playpauseService,
			}, -2)
		
		InfoBarSeek.__init__(self, actionmap = "MediaPlayerSeekActions")
		self.hidetimer = eTimer()
		self.hidetimer.timeout.get().append(self.ok)
		self.returning = False
		
		self.state = self.STATE_PLAYING
		self.lastseekstate = self.STATE_PLAYING
		
		self.onPlayStateChanged = [ ]
		self.__seekableStatusChanged()
		
		self.play()
		self.onClose.append(self.__onClose)
		
	def __onClose(self):
		self.session.nav.stopService()
		if self.oldservice is not None:
			#self.session.nav.stopService()
			self.session.nav.playService(self.oldservice)
		
	def __evEOF(self):
		print "evEOF=%d" % iPlayableService.evEOF
		print "Event EOF"
		self.handleLeave()
		
	def __setHideTimer(self):
		self.hidetimer.start(self.screen_timeout)
		
	def showInfobar(self):
		self.show()
		if self.state == self.STATE_PLAYING:
			self.__setHideTimer()
		else:
			pass
		
	def hideInfobar(self):
		self.hide()
		self.hidetimer.stop()
	
	def ok(self):
		if self.shown:
			self.hideInfobar()
		else:
			self.showInfobar()
		
	def playService(self, newservice):
		if self.state != self.STATE_IDLE:
			self.stopCurrent()
		self.service = newservice
		self.play()
		
	def play(self):
		if self.state == self.STATE_PAUSED:
			if self.shown:
				self.__setHideTimer()	
		self.state = self.STATE_PLAYING
		self.session.nav.playService(self.service)
		if self.shown:
			self.__setHideTimer()
			
	def stopCurrent(self):
		print "stopCurrent"
		self.session.nav.stopService()
		#if self.oldservice is not None:
			#self.session.nav.stopService()
		#self.session.nav.playService(self.oldservice)
		self.state = self.STATE_IDLE
		
	def playpauseService(self):
		print "playpauseService"
		if self.state == self.STATE_PLAYING:
			self.pauseService()
		elif self.state == self.STATE_PAUSED:
			self.unPauseService()
			
	def pauseService(self):
		print "pauseService"
		if self.state == self.STATE_PLAYING:
			self.setSeekState(self.STATE_PAUSED)
		
	def unPauseService(self):
		print "unPauseService"
		if self.state == self.STATE_PAUSED:
			self.setSeekState(self.STATE_PLAYING)
			
	def getSeek(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None

		seek = service.seek()

		if seek is None or not seek.isCurrentlySeekable():
			return None

		return seek
		
	def isSeekable(self):
		if self.getSeek() is None:
			return False
		return True
		
	def __seekableStatusChanged(self):
		print "seekable status changed!"
		if not self.isSeekable():
			self.setSeekState(self.STATE_PLAYING)
		else:
			print "seekable"

	def __serviceStarted(self):
		self.state = self.STATE_PLAYING
		self.__seekableStatusChanged()
		
	def setSeekState(self, wantstate):
		print "setSeekState"
		if wantstate == self.STATE_PAUSED:
			print "trying to switch to Pause- state:",self.STATE_PAUSED
		elif wantstate == self.STATE_PLAYING:
			print "trying to switch to playing- state:",self.STATE_PLAYING
		service = self.session.nav.getCurrentService()
		if service is None:
			print "No Service found"
			return False
		pauseable = service.pause()
		if pauseable is None:
			print "not pauseable."
			self.state = self.STATE_PLAYING

		if pauseable is not None:
			print "service is pausable"
			if wantstate == self.STATE_PAUSED:
				print "WANT TO PAUSE"
				pauseable.pause()
				self.state = self.STATE_PAUSED
				if not self.shown:
					self.hidetimer.stop()
					self.show()
			elif wantstate == self.STATE_PLAYING:
				print "WANT TO PLAY"
				pauseable.unpause()
				self.state = self.STATE_PLAYING
				if self.shown:
					self.__setHideTimer()

		for c in self.onPlayStateChanged:
			c(self.state)
		
		return True
		
	def handleLeave(self, error = False):
		self.is_closing = True
		#if self.oldservice is not None:
		#self.session.nav.stopService()
		#self.session.nav.playService(self.oldservice)
		self.close()
	
	def leavePlayer(self):
		self.handleLeave()
		
	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing :
			return
		self.handleLeave(config.usage.on_movie_eof.value)
