#!/usr/bin/python3
import os,sys, tempfile, shutil
import tarfile
import hashlib
import time
import subprocess
from repomanager import RepoManager as repoman
from urllib.request import urlretrieve
from lliurex import lliurexup
import gettext
_ = gettext.gettext

TMPDIR="/usr/share/llx-upgrade-release/tmp"
if os.path.isdir(TMPDIR)==False:
	if os.path.exists(TMPDIR)==True:
		os.unlink(TMPDIR)
	os.makedirs(TMPDIR)
TARFILE=os.path.join(TMPDIR,"data.tar")
WRKDIR="/usr/share/llx-upgrade-release/"
DATADIR="/usr/share/llx-upgrade-release/files"
REPODIR="/usr/share/llx-upgrade-release/repo"
LLXUP_PRESCRIPT="/usr/share/lliurex-up/preActions/850-remove-comited"
LLXUP_POSTSCRIPT="/usr/share/lliurex-up/postActions/900-touch"
LLXUP_TOKEN="/var/run/disableMetaProtection.token"
META_RDEPENDS=os.path.join(TMPDIR,"pkgs.list")

def i18n(raw):
	imsg=({
		"ABORT":_("Operation canceled"),
		"ACCEPT":_("Accept"),
		"ASK":_("Update?"),
		"AVAILABLE":_("There's a new LliureX release"),
		"BEGIN":_("Upgrading Lliurex..."),
		"CANCEL":_("Cancel"),
		"CHKRESULTS":_("Checking upgrade results..."),
		"DEFAULT":_("Default repositores will be resetted to Lliurex defaults.") ,
		"DISABLE":_("All configured repositories will be disabled."),
		"DISABLEREPOS":_("Disabling repos.."),
		"DISCLAIMER":_("This operation may destroy your system (or not)"),
		"DISCLAIMERGUI":_("This operation may destroy the system, proceed anyway"),
		"DISMISS":_("If you don't know what are you doing abort now"),
		"DOWNGRADE":_("¡¡UPGRADE FAILED!!. Wait while trying to recovery..."),
		"DOWNLOADED":_("All packages has been downloaded"),
		"END":_("System will go to upgrade mode. Don't poweroff the system."),
		"EXTRACT":_("Extracting upgrade files.."),
		"IMPORTANT":_("IMPORTANT"),
		"LASTCHANCE":_("This is the last chance for aborting.<br>Don't poweroff the computer nor interrupt the upgrade in any way."),
		"NOAVAILABLE":_("There're no upgrades available"),
		"PENDING":_("There're updates available. Install them before continue."),
		"PRAY":_("This is catastrophical.<br>Upgrader has tried to revert Lliurex-Up to original state"),
		"PRAY2":_("The upgraded failed.<br>Call a technical assistant and try to manually downgrade through Lliurex-Up"),
		"PRESS":_("Press a key for launching Lliurex-Up"),
		"PRESSREBOOT":_("Press to reboot"),
		"READ":_("Read carefully all the info showed in the screen"),
		"REBOOT":_("All files are downloaded. Press ACCEPT to begin the upgrade."),
		"REBOOT1":_("Close all open applications for preventing data loss."),
		"REBOOT_KO":_("It seems that the upgrade failed"),
		"REBOOT_KO1":_("Check your network and retry."),
		"RECOM":_("As result of this aborted upgrade may appear some problems with package management. Run lliurex-up now."),
		"REPONOTFOUND":_("No repo available at given path."),
		"REPOS":_("All repositories configured in this system will be deleted."),
		"REVERT":_("Reverting repositories to previous state"),
		"ROOT":_("Must be root"),
		"SETTINGUP":_("Setting up things. Be patient..."),
		"UNDO":_("This operation could not be reversed"),
		"UPGRADEEND":_("System upgrade completed. Now the system will reboot"),
		"UPGRADEOK":_("System upgrade completed."),
		"UPGRADE":_("Setting info for lliurex-up")})
	return(imsg.get(raw,raw))

def processMetaRelease(meta):
	content={}
	dist={}
	for line in meta:
		if "UpgradeToolSignature" in line:
			dist["UpgradeToolSignature"]=line.strip()
		elif "UpgradeTool" in line:
			dist["UpgradeTool"]=line.strip()
		elif "ReleaseNotesHtml" in line:
			dist["ReleaseNotesHtml"]=line.strip()
		elif "ReleaseNotes" in line:
			dist["ReleaseNotes"]=line.strip()
		elif "Release-File" in line:
			dist["Release-File"]=line.strip()
		elif "Description" in line:
			dist["Description"]=line.strip()
		elif "Supported" in line:
			dist["Supported"]=line.strip()
		elif "Date" in line:
			dist["Date"]=line.strip()
		elif "Version" in line:
			dist["Version"]=line.strip()
		elif "Name" in line:
			dist["Name"]=line.strip()
		elif "Dist" in line:
			if len(dist.get("Dist",""))>0:
				content[dist["Dist"]]=dist
				dist={}
			dist["Dist"]=line.strip()
	content[dist["Dist"]]=dist
	return(content)
#def processMetaRelease

def chkReleaseAvailable(metadata):
	cmd=["lliurex-version","-n"]
	cmdOutput=subprocess.check_output(cmd,encoding="utf8").strip()
	majorCurrent=cmdOutput.split(".")[0]
	upgradeTo={}
	for release,releasedata in metadata.items():
		version=releasedata.get("Version","").split(":")[1].strip()
		majorNext=version.split(".")[0]
		if (str(majorNext) > str(majorCurrent)):
			upgradeTo=releasedata
			break
	return(upgradeTo)
#def chkReleaseAvailable

def upgradeCurrentState():
	clean()
	return(getPkgsToUpdate())
#def upgradeCurrentState

def getPkgsToUpdate():
	llxup=lliurexup.LliurexUpCore()
	update=llxup.getPackagesToUpdate()
	return(update)
#def getPkgsToUpdate():

def getAllPackages():
	llxupPkgs=getPkgsToUpdate()
	tmp=[]
	for pkg,data in llxupPkgs.items():
		tmp.append(pkg)
	tmp.extend(getDependPkgs())
	pkgset=set(tmp)
	pkgs=[]
	for pkg in pkgset:
		if len(pkg.strip().replace("\n",""))>0:
			pkgs.append(pkg.strip().replace("\n",""))
	return(pkgs)
#def getAllPackages

def getDependPkgs():
	tmp=[]
	tmp.extend(_getMetaDepends())
	if os.path.isfile(META_RDEPENDS):
		with open(META_RDEPENDS,"r") as f:
			tmp.extend(f.read().split("\n"))
	tmp.extend(_getInstalledPkgs())
	pkgset=set(tmp)
	pkgs=[]
	for pkg in pkgset:
		if len(pkg.strip().replace("\n",""))>0:
			pkgs.append(pkg.strip().replace("\n",""))
	return(pkgs)
#def getDependPkgs

def prepareFiles(metadata):
	tools=downloadFile(metadata["UpgradeTool"].replace("UpgradeTool: ",""))
	return(tools)
#def prepareFiles(metadata):

def _generateDemoteScript():
	if os.path.isfile("{}/demote.cfg".format(TMPDIR))==True:
		demote=[]
		fcontent=[]
		with open("{}/demote.cfg".format(TMPDIR),"r") as f:
			for line in f.readlines():
				if len(line.strip())>0:
					demote.append(line.strip())
		if len(demote)>0:
			fcontent="#!/bin/bash\n"
			fcontent+="ACTION=\"$1\"\n"
			fcontent+="case \"$ACTION\" in\n" 
			fcontent+="preActions)\n"
			fcontent+="dpkg --force-all --purge {} || true\n".format(" ".join(demote))
			fcontent+="apt-get install -f -y\n"
			fcontent+="rm $0\n"
			fcontent+="\n;;\nesac"

		if len(fcontent)>0:
			with open(LLXUP_PRESCRIPT,"w") as f:
				f.write(fcontent)
			os.chmod(LLXUP_PRESCRIPT,0o755)
#def _generateDemoteScript

def _generatePostInstallScript():
		#DEPRECATED
		return
		fcontent="#!/bin/bash\n"
		fcontent+="ACTION=\"$1\"\n"
		fcontent+="case \"$ACTION\" in\n" 
		fcontent+="postActions)\n"
		fcontent+="touch /tmp/.endUpdate\n"
		fcontent+="rm {} 2>/dev/null || true\n".format(LLXUP_TOKEN)
		fcontent+="rm $0\n"
		fcontent+="\n;;\nesac"
		with open(LLXUP_POSTSCRIPT,"w") as f:
			f.write(fcontent)
		os.chmod(LLXUP_POSTSCRIPT,0o755)
#def _generatePostInstallScript

def enableUpgradeRepos(tools):
	try:
		with tarfile.open(tools) as tar:
			tar.extractall(path=TMPDIR)
	except Exception as e:
		print(e)
	shutil.copy("{}/sources.list".format(TMPDIR),"/etc/apt/sources.list")
	_generateDemoteScript()
	_generatePostInstallScript()
	return()
#def enableUpgradeRepos

def clean():
	cmd=["apt-get","clean"]
	subprocess.run(cmd)
#def clean

def restoreRepos():
	ftar=TARFILE
	if os.path.isfile(ftar)==False:
		return
	try:
		with tarfile.open(ftar) as tar:
			tar.extractall(path=TMPDIR)
	except Exception as e:
		print("Untar: {}".format(e))
	wrkdir=os.path.join(TMPDIR,"etc/apt")
	shutil.copy("{}/sources.list".format(wrkdir),"/etc/apt/sources.list")
	if os.path.isdir("{}/sources.list.d".format(wrkdir)):
		for f in os.listdir("{}/sources.list.d".format(wrkdir)):
			if f.endswith(".list"):
				shutil.copy("{0}/sources.list.d/{1}".format(wrkdir,f),"/etc/apt/sources.list.d/{}".format(f))
	cleanLlxUpActions()
#def restoreRepos

def cleanLlxUpActions():
	if os.path.isfile(LLXUP_PRESCRIPT):
		os.unlink(LLXUP_PRESCRIPT)
	if os.path.isfile(LLXUP_POSTSCRIPT):
		os.unlink(LLXUP_POSTSCRIPT)
	if os.path.isfile(LLXUP_TOKEN):
		os.unlink(LLXUP_TOKEN)
#def cleanLLxUpActions

def downgrade():
	#Update info
	cmd=["apt-get","update"]
	subprocess.run(cmd)
	#Get old version
	cmd=["apt-cache","policy","lliurex-up"]
	cmdOutput=subprocess.check_output(cmd,encoding="utf8").strip()
	line=""
	for out in cmdOutput.split("\n"):
		if "://" in out:
			break
		line=out
	uprelease=line.strip().split()[0]
	cmd=["apt-get","install","-y","--allow-downgrades","--reinstall","lliurex-up={}".format(uprelease), "lliurex-up-core={}".format(uprelease), "lliurex-up-cli={}".format(uprelease), "lliurex-up-indicator={}".format(uprelease),"python3-lliurexup={}".format(uprelease)]
	subprocess.run(cmd)
#def downgrade()

def _getValuesForLliurexUp(metadata):
	data={"url":"http:/","mirror":"","version":""}
	releaseurl=metadata.get("Release-File","").split()[-1]
	for component in releaseurl.split("/")[1:]:
		if component=="dists":
			break
		data["url"]="{}/{}".format(data["url"],component)
	data["version"]=os.path.basename(data["url"])
		
	return(data)
#def _getValuesForLliurexUp

def disableRepos():
	copySystemFiles()
	manager=repoman.manager()
	for repo,data in manager.list_sources().items():
		repos={}
		repos[repo]=data
		repos[repo]['enabled']='false'
		manager.write_repo_json(repos)
		manager.write_repo(repos)
#def disableRepos

def downloadFile(url):
	f=os.path.basename(url)
	f=os.path.join(TMPDIR,f)
	if os.path.isdir(TMPDIR)==False:
		os.makedirs(TMPDIR)
	if os.path.isfile(f):
		os.unlink(f)
	try:
		urlretrieve(url, f)
	except Exception as e:
		print(url)
		print(e)
	return(f)
#def downloadFile

def copySystemFiles():
	if os.path.isfile(TARFILE):
		return()	
	with tarfile.open(TARFILE,"w") as tarf:
		tarf.add("/etc/apt/sources.list")
		tarf.add("/etc/apt/sources.list.d/")
#def copySystemFiles

def _modifyAptConf(repodir=""):
	if repodir=="" or os.path.exists(repodir)==False:
		repodir=REPODIR
	aptconf="/etc/apt/apt.conf"
	if os.path.isfile(aptconf)==True:
		shutil.copy(aptconf,TMPDIR)
	if os.path.isdir(repodir)==False:
		os.makedirs(repodir)
	with open(aptconf,"w") as f:
		f.write("Dir::Cache{{Archives {0}}}\nDir::Cache::Archives {0};".format(repodir))
#def _modifyAptConf

def setLocalRepo(release="jammy",repodir=""):
	if repodir=="" and os.path.exists(repodir)==False:
		repodir=REPODIR
	sources="/etc/apt/sources.list"
	tmpsources=os.path.join(TMPDIR,".sources.list")
	dists=[release,"{}-updates".format(release),"{}-security".format(release)]
	with open(tmpsources,"w") as f:
		for dist in dists:
			repo="{}{}".format(repodir,dist.replace(release,""))
			f.write("deb [trusted=yes] file:{} ./\n".format(repo))
	shutil.copy(tmpsources,sources)
	_deleteAptLists()
#def setLocalRepo

def _deleteAptLists():
	wrkdir="/var/lib/apt/lists/"
	for f in os.listdir(wrkdir):
		dest=os.path.join(wrkdir,f)
		if os.path.isfile(dest) and f!="lock":
			os.unlink(dest)
#def _deleteAptLists

def downloadPackages(pkgs):
	_modifyAptConf()
	clean()
	#_getMetaDepends()
	#pkgs=llxup.getPackagesToUpdate()
	cmd=["apt-get","dist-upgrade","-y","-d"]
	subprocess.run(cmd)
	repoerr="/usr/share/llx-upgrade-release/err"
	f=open(repoerr,"w")
	f.close()
	for pkg in pkgs:
		cmd=["apt-get","install","-y","-d","--reinstall",pkg]
		prc=subprocess.run(cmd,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
		print("Get: {}".format(pkg))
		if prc.returncode!=0:
			olddir=os.getcwd()
			os.chdir(REPODIR)
			print("Download: {})".format(pkg))
			#pkglist=_getDepends(pkg)
			#cmd=["apt-get","download","{}".format(" ".join(pkglist))]
			cmd=["apt-get","download","{}".format(pkg)]
			prc=subprocess.run(cmd)
			os.chdir(olddir)
		#	try:
		#		new=1
		#		old=0
		#		if os.path.isfile(repoerr):
		#			with open(repoerr,"r") as f:
		#				old=f.read().strip()
		#				if old.isdigit()==True:
		#					new=int(old)+1
		#		with open(repoerr,"w") as f:
		#			f.write(str(new))
		#	except Exception as e:
		#		print(e)
#def downloadPackages

def _getMetaDepends():
	cmd=["lliurex-version","--history"]
	cmdOutput=subprocess.check_output(cmd,encoding="utf8").strip()
	metas=[]
	depends=[]
	first=""
	for out in cmdOutput.split("\n"):
		line=out.replace("\t","").split(" ")
		if len(line[0])==0:
			line.pop(0)
		pkg=line[1]
		if "live" in pkg:
			continue
		cmd=["dpkg","-l",pkg]
		state=subprocess.run(cmd)
		if state.returncode==0:
			metas.append(pkg)
		if first=="":
			first=pkg
	if len(metas)==0:
		metas.append(pkg)
	#cmd=["apt-get","update"]
	#subprocess.run(cmd)
	metaDepends=[]
	for meta in metas:
		metaDepends.extend(_getDepends(meta))
	if len(metaDepends)>0:
		setDepends=set(metaDepends)
		for depen in setDepends:
			depends.append(depen)
	return(depends)
#def _getMetaDepends

def _getDepends(pkg):
	depends=[]
	cmd=["apt-cache","depends","--recurse","--no-suggests",pkg]
	cmdOutput=subprocess.check_output(cmd,encoding="utf8").strip()
	for line in cmdOutput.split("\n"):
		if line[0].isalpha():
			depends.append(line)
	return(depends)
#def _getDepends(pkg)

def _getInstalledPkgs():
	pkgs=[]
	cmd=["dpkg","--get-selections"]
	cmdOutput=subprocess.check_output(cmd,encoding="utf8").strip()
	for line in cmdOutput.split("\n"):
		data=line.split()
		pkgs.append(data[0])
	return(pkgs)
#def _getInstalledPkgs

def generateLocalRepo(release="jammy",repodir=""):
	if repodir=="" or os.path.exists(repodir)==False:
		repodir=REPODIR
		
	dists=[release,"{}-updates".format(release),"{}-security".format(release)]
	components=["main","universe","multiverse"]
	for dist in dists:
		repo="{}{}".format(repodir,dist.replace(release,""))
		if os.path.isdir(repo)==False:
			os.makedirs(repo)
		f=open(os.path.join(repo,"Packages"),"w")
		f.close()
		for component in components:
			packagesf=downloadFile("http://lliurex.net/{0}/dists/{1}/{2}/binary-amd64/Packages".format(release,dist,component))
			with open(packagesf,"r") as f:
				fcontent=f.read()
			if repo!=repodir:
				path="../repo/"
			else:
				path="./"
			if os.path.isdir(repo)==False:
				os.makedirs(repo)
			line=[]
			with open(os.path.join(repo,"Packages"),"a") as f:
				for fline in fcontent.split("\n"):
					if fline.startswith("Filename:"):
						line=fline.split(" ")
						fline=" ".join([line[0],"{0}{1}".format(path,os.path.basename(line[1]))])
					f.write("{}\n".format(fline))
#def generateLocalRepo

def generateReleaseFile(release="jammy",version="23.06",releasedate="Mon, 18 Sep 2023 10:02:58 UTC"):
	releasef=downloadFile("http://lliurex.net/{0}/dists/{0}/main/binary-amd64/Release".format(release))
	releasePath=os.path.join(DATADIR,"Release")
	if os.path.isfile(releasePath):
		os.unlink(releasePath)
	shutil.copy(releasef,releasePath)
	return
#def _generateReleaseFile

def upgradeLlxUp(metadata):
	data=_getValuesForLliurexUp(metadata)
	a=open(LLXUP_TOKEN,"w")
	a.close()
	llxup=lliurexup.LliurexUpCore()
	llxup.defaultUrltoCheck=data.get("url")
	llxup.defaultVersion=data.get("version")
	llxup.installLliurexUp()
#def upgradeLlxUp():

def setSystemdUpgradeTarget():
	systemdpath="/usr/lib/systemd/system"
	target=os.path.join(systemdpath,"llx-upgrade.target")
	service=os.path.join(systemdpath,"llx-upgrade.service")
	targetContent=["[Unit]","Description=Upgrade Mode","Documentation=man:systemd.special(7)","Requires=llx-upgrade.service","After=llx-upgrade.service","AllowIsolate=yes"]
	with open (target,"w") as f:
		f.write("\n".join(targetContent))
	unitContent=["[Unit]","Description=Upgrade environment","Documentation=man:sulogin(8)","DefaultDependencies=no","Conflicts=network-manager.service","Conflicts=shutdown.target","Conflicts=llx-upgrade.service","Before=shutdown.target","Before=llx-upgrade.service"]
	serviceContent=["[Service]","Environment=HOME=/root","WorkingDirectory=-/root","ExecStart=-/usr/share/llx-upgrade-release/upgrader.py","Type=idle","#StandardInput=tty-force","StandardOutput=inherit","StandardError=inherit","KillMode=process","IgnoreSIGPIPE=no","SendSIGHUP=yes"]
	with open (service,"w") as f:
		f.write("\n".join(unitContent))
		f.write("\n")
		f.write("\n".join(serviceContent))
#def setSyemdUpgradeTarget

def unsetSystemdUpgradeTarget():
	systemdpath="/usr/lib/systemd/system"
	target=os.path.join(systemdpath,"llx-upgrade.target")
	service=os.path.join(systemdpath,"llx-upgrade.service")
	if os.path.isfile(target):
		os.unlink(target)
	if os.path.isfile(service):
		os.unlink(service)
#def unsetSyemdUpgradeTarget

def chkUpgradeResult():
	pass
	
#def chkUpgradeResult

def fixAptSources(repodir=""):
	if repodir=="" or os.path.exists(repodir)==False:
		repodir=REPODIR
	llxup_sources="/etc/apt/lliurexup_sources.list"
	tmpllxup_sources=os.path.join(TMPDIR,"lliurexup_sources.list")
	sources="/etc/apt/sources.list"
	if os.path.isfile(llxup_sources):
		os.unlink(llxup_sources)
	fcontent=[]
	fcontent.append("deb [trusted=yes] file:{}/ ./\n".format(repodir))
	fcontent.append("deb [trusted=yes] file:{}-updates/ ./\n".format(repodir))
	fcontent.append("deb [trusted=yes] file:{}-security/ ./\n".format(repodir))
	#with open(sources,"r") as f:
	#	for line in f.readlines():
	#		if "file:" in line:
	#			continue
	#		fcontent.append(line)
	fcontent.append("")
	tmpsources=os.path.join(TMPDIR,"sources.list")
	with open (tmpsources,"w") as f:
		f.writelines(fcontent)
	shutil.copy(tmpsources,sources)
	shutil.copy(tmpsources,llxup_sources)
#def fixAptsources


def _enableIpRedirect():
	##DEPRECATED##
	cmd=["nslookup","lliurex.net"]
	local127=False
	try:
		output=subprocess.check_output(cmd,encoding="utf8",universal_newlines=True)
	except Exception as e:
		output=""
	for line in output.split("\n"):
		if line.startswith("Address:"):
			ip=line.split()[-1]
			if ip.startswith("127"):
				if not ip.endswith(".1"):
					continue
				local127=True
			cmd=["iptables","-t","nat","-A","OUTPUT","-d",ip,"-p","tcp","--dport","80","-j","DNAT","--to-destination","127.0.0.2"]
			try:
				subprocess.run(cmd)
			except Exception as e:
				print("iptables: {}".format(e))
	return(len(output))
#def _enableIpRedirect

def _modHosts():
	fcontent=[]
	tmphosts=os.path.join(TMPDIR,"hosts")
	hosts="/etc/hosts"
	with open(hosts,"r") as f:
		for line in f.readlines():
			if "localhost" in line and "lliurex.net" not in line:
				line=line.replace("localhost","localhost lliurex.net",1)
			fcontent.append(line)

	with open(hosts,"w") as f:
		f.writelines(fcontent)
		f.write("\n")
	#cmd=["mount",tmphosts,"/etc/hosts","--bind"]
	#subprocess.run(cmd)
#def _modHosts

def _modHttpd():
	files=["/etc/apache2/ports.conf","/etc/apache2/sites-available/000-default.conf"]
	swFound=False
	for filen in files:
		if os.path.isfile(filen)==False:
			continue
		swFound=True
		fcontent=[]
		with open(filen,"r") as f:
			for line in f.readlines():
				if "Listen 80" in line or "<VirtualHost *:80>" in line:
					line=line.replace("80","10880")
				fcontent.append(line)
			tmpfilen=os.path.join(TMPDIR,os.path.basename(filen))
			with open(tmpfilen,"w") as f:
				f.writelines(fcontent)
				f.write("\n")
			cmd=["mount",tmpfilen,filen,"--bind"]
			print("CMD: {}".format(" ".join(cmd)))
			try:
				subprocess.run(cmd)
			except Exception as e:
				print (e)
	if swFound==True:
		cmd=["service","apache2","restart"]
		try:
			subprocess.run(cmd)
		except:
			pass
	return()
#def _modHttpd()

def _disableMirror():
	mirrorDir="/etc/lliurex-mirror/conf"
	srvPath="/srv"
	if os.path.isdir(mirrorDir):
		cmd=["mount",srvPath,mirrorDir,"--bind"]
		subprocess.run(cmd)
	return()
#def _disableMirror

def _disableIpRedirect():
	cmd=["iptables","-t","nat","-F"]
	subprocess.run(cmd)
	return()
#def _disableIpRedirect

def disableSystemdServices():
	for i in ["network-manager","systemd-networkd"]:
		cmd=["service",i,"stop"]
		subprocess.run(cmd)
	cmd=["systemctl","stop","network.target"]
	subprocess.run(cmd)
	return()
#def disableSystemdServices

def undoHostsMod():
	hosts="/etc/hosts"
	fcontent=[]
	with open(hosts,"r") as f:
		for line in f.readlines():
			if "localhost" in line and " lliurex.net" in line:
				line=line.replace(" lliurex.net","")
			fcontent.append(line)
	with open(hosts,"w") as f:
		f.writelines(fcontent)
		f.write("\n")
	return()
#def undoHostsMod

def unfixAptSources():
	sources="/etc/apt/sources.list"
	llxup_sources="/etc/apt/lliurexup_sources.list"
	f=open(sources,"w")
	f.close()
	cmd=["repoman-cli","-e","0","-y"]
	subprocess.run(cmd)
	if os.path.isfile(llxup_sources):
		os.unlink(llxup_sources)
	shutil.copy(sources,llxup_sources)
	return()
#def unfixAptsources

def removeAptConf():
	aptconf="/etc/apt/apt.conf"
	tmpaptconf=os.path.join(TMPDIR,os.path.basename(aptconf))
	if os.path.isfile(aptconf):
		os.unlink(aptconf)
	if os.path.isfile(tmpaptconf):
		shutil.copy(tmpaptconf,aptconf)
	return()
#def removeAptConf

def enableSystemdServices():
	for i in ["network-manager","systemd-networkd"]:
		cmd=["service",i,"start"]
		subprocess.run(cmd)
	return()
#def enableSystemdServices
