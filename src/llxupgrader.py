#!/usr/bin/python3:
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
	os.makedirs(TMPDIR)
TARFILE=os.path.join(TMPDIR,"data.tar")
WRKDIR="/usr/share/llx-upgrade-release/"
REPODIR="/usr/share/llx-upgrade-release/repo"
LLXUP_PRESCRIPT="/usr/share/lliurex-up/preActions/850-remove-comited"
LLXUP_POSTSCRIPT="/usr/share/lliurex-up/postActions/900-touch"
LLXUP_TOKEN="/var/run/disableMetaProtection.token"

def i18n(raw):
	imsg=({
		"ABORT":_("Operation canceled"),
		"ACCEPT":_("Accept"),
		"ASK":_("Update?"),
		"AVAILABLE":_("There's a new LliureX release"),
		"BEGIN":_("Upgrading Lliurex..."),
		"CANCEL":_("Cancel"),
		"DEFAULT":_("Default repositores will be resetted to Lliurex defaults.") ,
		"DISABLE":_("All configured repositories will be disabled."),
		"DISABLEREPOS":_("Disabling repos.."),
		"DISCLAIMER":_("This operation may destroy your system (or not)"),
		"DISCLAIMERGUI":_("This operation may destroy the system, proceed anyway"),
		"DISMISS":_("If you don't know what are you doing abort now"),
		"DOWNGRADE":_("¡¡UPGRADE FAILED!!. Wait while trying to recovery..."),
		"END":_("System will go to upgrade mode. Don't poweroff the system."),
		"EXTRACT":_("Extracting upgrade files.."),
		"IMPORTANT":_("IMPORTANT"),
		"LASTCHANCE":_("This is the last chance for aborting. Don't poweroff the computer nor interrupt this process in any way."),
		"NOAVAILABLE":_("There're no upgrades available"),
		"PENDING":_("There're updates available. Install them before continue."),
		"PRAY":_("This is catastrophical.<br>Upgrader has tried to revert Lliurex-Up to original state"),
		"PRAY2":_("The upgraded failed.<br>Call a technical assistant and try to manually downgrade through Lliurex-Up"),
		"PRESS":_("Press a key for launching Lliurex-Up"),
		"READ":_("Read carefully all the info showed in the screen"),
		"REBOOT":_("All files are downloaded. Press ACCEPT to begin the upgrade."),
		"REBOOT1":_("Close all open applications for preventing data loss."),
		"REBOOT_KO":_("It seems that the upgrade failed"),
		"REBOOT_KO1":_("Check your network and retry."),
		"RECOM":_("As result of this aborted upgrade may appear some problems with package management. Run lliurex-up now."),
		"REPOS":_("All repositories configured in this system will be deleted."),
		"REVERT":_("Reverting repositories to previous state"),
		"ROOT":_("Must be root"),
		"SETTINGUP":_("Setting up things. Be patient..."),
		"UNDO":_("This operation could not be reversed"),
		"UPGRADEEND":_("System upgrade completed. Now the system will reboot"),
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
	#check state of current release
	clean()
	return(getPkgsToUpdate())
#def upgradeCurrentState

def getPkgsToUpdate():
	llxup=lliurexup.LliurexUpCore()
	update=llxup.getPackagesToUpdate()
	return(update)
#def getPkgsToUpdate():

def prepareFiles(metadata):
	tools=downloadFile(metadata["UpgradeTool"].replace("UpgradeTool: ",""))
	return(tools)
#def prepareFiles(metadata):

def _generateDemoteScript():
	if os.path.isfile("{}/demote.cfg".format(TMPDIR))==True:
		demote=[]
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
	meta=os.path.basename(url)
	meta=os.path.join(TMPDIR,meta)
	if os.path.isdir(TMPDIR)==False:
		os.makedirs(TMPDIR)
	if os.path.isfile(meta):
		os.unlink(meta)
	try:
		urlretrieve(url, meta)
	except Exception as e:
		print(url)
		print(e)
	return(meta)
#def downloadFile

def copySystemFiles():
	if os.path.isfile(TARFILE):
		return()	
	with tarfile.open(TARFILE,"w") as tarf:
		tarf.add("/etc/apt/sources.list")
		tarf.add("/etc/apt/sources.list.d/")
#def copySystemFiles

def _modifyAptConf():
	aptconf="/etc/apt/apt.conf"
	if os.path.isfile(aptconf)==True:
		shutil.copy(aptconf,TMPDIR)
	if os.path.isdir(REPODIR)==False:
		os.makedirs(REPODIR)
	with open(aptconf,"w") as f:
		f.write("Dir::Cache{{Archives {0}}}\nDir::Cache::Archives {0};".format(REPODIR))
#def _modifyAptConf

def setLocalRepo():
	sources="/etc/apt/sources.list"
	tmpsources=os.path.join(TMPDIR,".sources.list")
	with open(tmpsources,"w") as f:
		f.write("deb [trusted=yes] file:{} ./".format(REPODIR))
	shutil.copy(tmpsources,sources)
	#cmd=["mount",tmpsources,sources,"--bind"]
	#subprocess.run(cmd)
	_deleteAptLists()
#def setLocalRepo

def _deleteAptLists():
	wrkdir="/var/lib/apt/lists/"
	for f in os.listdir(wrkdir):
		dest=os.path.join(wrkdir,f)
		if os.path.isfile(dest) and f!="lock":
			os.unlink(dest)
#def _deleteAptLists

def downloadPackages():
	_modifyAptConf()
	clean()
	cmd=["apt-get","dist-upgrade","-d","-y"]
	subprocess.run(cmd)
#def downloadPackages

def generateLocalRepo():
	cmd=["dpkg-scanpackages",REPODIR,"/dev/null"]
	cmdOutput=subprocess.check_output(cmd,encoding="utf8").strip()
	line=""
	with open(os.path.join(REPODIR,"Packages"),"w") as f:
		for out in cmdOutput.split("\n"):
			if out.startswith("Filename:"):
				line=out.split(" ")
				out=" ".join([line[0],"./{}".format(os.path.basename(line[1]))])
			f.write("{}\n".format(out))
#def generateLocalRepo

def generateReleaseFile(release,version,releasedate):
	return
	#DEPRECATED
	releasedate="Wed, 27 Sep 2023 15:32:39 UTC"
	releasef=os.path.join(REPODIR,"Release")
	packages=os.path.join(REPODIR,"Packages")
	md5sum=hashlib.md5(open(packages,'rb').read()).hexdigest()
	sha1sum=hashlib.sha1(open(packages,'rb').read()).hexdigest()
	sha256sum=hashlib.sha256(open(packages,'rb').read()).hexdigest()
	size=os.path.getsize(packages)
#	packagesgz=os.path.join(REPODIR,"Packages.gz")
#	md5sumgz=hashlib.md5(open(packages,'rb').read()).hexdigest()
#	sha1sumgz=hashlib.sha1(open(packages,'rb').read()).hexdigest()
#	sha256sumgz=hashlib.sha256(open(packages,'rb').read()).hexdigest()
#	sizegz=os.path.getsize(packages)
#	rmd5sum=hashlib.md5(open(releasef,'rb').read()).hexdigest()
#	rsha1sum=hashlib.sha1(open(releasef,'rb').read()).hexdigest()
#	rsha256sum=hashlib.sha256(open(releasef,'rb').read()).hexdigest()
#	rsize=os.path.getsize(releasef)
#	inrelease=os.path.join(REPODIR,"InRelease")
#	imd5sum=hashlib.md5(open(inrelease,'rb').read()).hexdigest()
#	isha1sum=hashlib.sha1(open(inrelease,'rb').read()).hexdigest()
#	isha256sum=hashlib.sha256(open(inrelease,'rb').read()).hexdigest()
#	isize=os.path.getsize(inrelease)
	fcontent=[]
	fcontent.append("Origin: LliureX")
	fcontent.append("Label: LliureX")
	fcontent.append("codename: {}".format(release))
	fcontent.append("Version: {}".format(version))
	fcontent.append("Date: {}".format(releasedate))
	fcontent.append("Architecture: i386 amd64")
	fcontent.append("Components: main")
	fcontent.append("Description: Lliurex Release Packages")
	fcontent.append("MD5Sum:")
	fcontent.append("{0} {1} Packages".format(md5sum,size))
#	fcontent.append("{0} {1} Packages.gz".format(md5sumgz,sizegz))
#	fcontent.append("{0} {1} Release".format(rmd5sum,rsize))
#	fcontent.append("{0} {1} InRelease".format(imd5sum,isize))
	fcontent.append("SHA1:")
	fcontent.append("{0} {1} Packages".format(sha1sum,size))
#	fcontent.append("{0} {1} Packages".format(sha1sumgz,sizegz))
#	fcontent.append("{0} {1} Release".format(rsha1sum,rsize))
#	fcontent.append("{0} {1} InRelease".format(isha1sum,isize))
	fcontent.append("SHA256:")
	fcontent.append("{0} {1} Packages".format(sha256sum,size))
#	fcontent.append("{0} {1} Packages.gz".format(sha256sumgz,sizegz))
#	fcontent.append("{0} {1} Release".format(rsha256sum,rsize))
#	fcontent.append("{0} {1} InRelease".format(isha256sum,isize))
	with open(releasef,"w") as f:
		f.write("\n".join(fcontent))
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

