#!/usr/bin/python3
import os,sys, tempfile, shutil
import tarfile
import subprocess
from repomanager import RepoManager as repos
from urllib.request import urlretrieve
from lliurex import lliurexup
import gettext
_ = gettext.gettext

WRKDIR="/tmp/llx-release-updater"

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
		"EXTRACT":_("Extracting upgrade files.."),
		"IMPORTANT":_("IMPORTANT"),
		"LASTCHANCE":_("If you continue the system will be upgraded to the new release of LliureX"),
		"PENDING":_("There're updates available. Install them before continue."),
		"PRESS":_("Press a key for launching Lliurex-Up"),
		"READ":_("Read carefully all the info showed in the screen"),
		"RECOM":_("As result of this aborted upgrade may appear some problems with package management. Run lliurex-up now."),
		"REPOS":_("All repositories configured in this system will be deleted."),
		"REVERT":_("Reverting repositories to previous state"),
		"UNDO":_("This operation could not be reversed"),
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
	upgradeTo={}
	for release,releasedata in metadata.items():
		version=releasedata.get("Version","").split(":")[1].strip()
		if (str(version) > str(cmdOutput)):
			upgradeTo=releasedata
			break
	return(upgradeTo)
#def chkReleaseAvailable

def upgradeCurrentState():
	#check state of current release
	llxup=lliurexup.LliurexUpCore()
	update=llxup.getLliurexVersionLliurexNet()
	if update["installed"]<update["candidate"]:
		return True
	return False
#def upgradeCurrentState

def prepareFiles(metadata):
	tools=downloadFile(metadata["UpgradeTool"].replace("UpgradeTool: ",""))
	return(tools)
#def prepareFiles(metadata):

def enableUpgradeRepos(tools):
	try:
		a=tarfile.open(tools)
		a.extractall()
	except Exception as e:
		print(e)
	shutil.copy("sources.list","/etc/apt/sources.list")
#def enableUpgradeRepos

def restoreRepos():
	ftar="/tmp/data.tar"
	if os.path.isfile(ftar)==False:
		return
	try:
		with tarfile.open(ftar) as tar:
			tar.extractall(path=WRKDIR,filter='data')
	except Exception as e:
		print("Untar: {}".format(e))
	wrkdir=os.path.join(WRKDIR,"etc/apt")
	shutil.copy("{}/sources.list".format(wrkdir),"/etc/apt/sources.list")
	if os.path.isdir("{}/sources.list.d".format(wrkdir)):
		for f in os.listdir("{}/sources.list.d".format(wrkdir)):
			if f.endswith(".list"):
				shutil.copy("{0}/sources.list.d/{1}".format(wrkdir,f),"/etc/apt/sources.list.d/{}".format(f))
#def restoreRepos

def launchLliurexUp():
	llxup=lliurexup.LliurexUpCore()
	llxup.defaultUrltoCheck="http://lliurex.net/jammy"
	llxup.defaultMirror="llx23"
	llxup.defaultVersion="jammy"
	llxup.installLliurexUp()
	a=open("/var/run/disableMetaProtection.token","w")
	a.close()
	os.execv("/usr/sbin/lliurex-up",["-u"])
#def launchLliurexUp

def launchLliurexUpgrade():
	llxup=lliurexup.LliurexUpCore()
	llxup.defaultUrltoCheck="http://lliurex.net/jammy"
	llxup.defaultMirror="llx23"
	llxup.defaultVersion="jammy"
	llxup.installLliurexUp()
	a=open("/var/run/disableMetaProtection.token","w")
	a.close()
	os.execv("/usr/sbin/lliurex-upgrade",["-u"])
#def launchLliurexUpgrade
		
def disableRepos():
	copySystemFiles()
	cmd=["repoman-cli","-l"]
	repos=subprocess.check_output(cmd,encoding="utf8").split("\n")
	for line in repos:
		if len(line)>0:
			repoId=line.split(")")[0]
			cmd=["repoman-cli","-y","-d",repoId]
			subprocess.run(cmd)
#def disableRepos

def downloadFile(url):
	meta=os.path.basename(url)
	meta=os.path.join(WRKDIR,meta)
	if os.path.isdir(WRKDIR)==False:
		os.makedirs(WRKDIR)

	try:
		urlretrieve(url, meta)
	except Exception as e:
		print(url)
		print(e)
		sys.exit(1)
	return(meta)
#def downloadFile

def copySystemFiles():
	with tarfile.open("/tmp/data.tar","w") as tarf:
		tarf.add("/etc/apt/sources.list")
		tarf.add("/etc/apt/sources.list.d/")
#def copySystemFiles

def chkUpgradeResult():
	pass
	
#def chkUpgradeResult

