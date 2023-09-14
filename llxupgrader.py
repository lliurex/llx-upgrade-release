#!/usr/bin/python3
import os,sys, tempfile, shutil
import tarfile
import subprocess
from repomanager import RepoManager as repos
from urllib.request import urlretrieve
from lliurex import lliurexup
import gettext
_ = gettext.gettext

def i18n(raw):
	imsg={"IMPORTANT":_("IMPORTANT"),
		"ACCEPT":_("Accept"),
		"AVAILABLE":_("There's a new LliureX release"),
		"ASK":_("Update?"),
		"CANCEL":_("Cancel"),
		"DISCLAIMER":_("This operation may destroy your system (or not)"),
		"DISCLAIMERGUI":_("This operation may destroy the system, proceed anyway"),
		"ABORT":_("Operation canceled"),
		"READ":_("Read carefully all the info showed in the screen"),
		"REPOS":_("All repositories configured in this system will be deleted."),
		"UPGRADE":_("Setting info for lliurex-up"),
		"EXTRACT":_("Extracting upgrade files.."),
		"DISABLEREPOS":_("Disabling repos.."),
		"PENDING":_("There're updates available. Install them before continue."),
		"DISABLE":_("All configured repositories will be disabled."),
		"DEFAULT":_("Default repositores will be resetted to Lliurex defaults.") ,
		"UNDO":_("This operation could not be reversed"),
		"DISMISS":_("If you don't know what are you doing abort now"),
		"BEGIN":_("Upgrading Lliurex...")}
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

def disclaimerAgree():
	print(" ===== {} =====".format(i18n("IMPORTANT")))
	print(" ===== {} =====".format(i18n("IMPORTANT")))
	print()
	print(" {}".format(i18n("DISCLAIMER")))
	print()
	print("****************")
	print(" * {} *".format(i18n("READ")))
	print("****************")
	print()
	print(" * {} *".format(i18n("REPOS")))
	print()
	print("{}".format(i18n("DISMISS")))
	print()
	abort=input("[y]/n: ")
	if abort=="n":
		return(True)
	return(False)
#def disclaimerAgree

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
			print("... {}".format(line))
			cmd=["repoman-cli","-y","-d",repoId]
			subprocess.run(cmd)
#def disableRepos

def downloadFile(url):
	meta=os.path.basename(url)
	try:
		urlretrieve(url, meta)
	except Exception as e:
		print(url)
		print(e)
		sys.exit(1)
	return(meta)
#def downloadFile

def copySystemFiles():
	tarf=tarfile.open("/tmp/data.tar","w")
	tarf.addfile(tarfile.TarInfo("/etc/apt/sources.list"))
	tarf.addfile(tarfile.TarInfo("/etc/apt/sources.list.d/"))
	for f in os.listdir("/etc/apt/sources.list.d"):
		tarf.addfile(tarfile.TarInfo("/etc/apt/sources.list.d/{}".format(f)))
	tarf.close()
#def copySystemFiles

def chkUpgradeResult():
	pass
	
#def chkUpgradeResult

