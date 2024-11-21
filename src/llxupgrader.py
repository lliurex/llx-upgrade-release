#!/usr/bin/python3
import os,sys, tempfile, shutil
import filecmp
import tarfile,gzip
import subprocess
from repoman import repomanager as repoman
from urllib.request import urlretrieve
from lliurex import lliurexup

DBG=True

TMPDIR="/usr/share/llx-upgrade-release/tmp"
if os.path.isdir(TMPDIR)==False and os.geteuid()==0:
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
SOURCESF="/etc/apt/sources.list"

def _debug(msg):
	if DBG==True:
		print("DBG: {}".format(msg))
#def _debug

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

def chkReleaseAvailable(url=""):
	upgradeTo={}
	if len(url)==0:
		url="https://raw.githubusercontent.com/lliurex/llx-upgrade-release/master/src/files/meta-release"
	meta=downloadFile(url)
	if os.path.isfile(meta):
		with open(meta,"r") as f:
			metadata=processMetaRelease(f.readlines())
	cmd=["lliurex-version","-n"]
	cmdOutput=subprocess.check_output(cmd,encoding="utf8").strip()
	majorCurrent=cmdOutput.split(".")[0]
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
			fcontent+="dpkg --get-selections > {0}\n".format(os.path.join(TMPDIR,"dselect"))
			fcontent+="rm $0\n"
			fcontent+="\n;;\nesac"

		if len(fcontent)>0:
			with open(LLXUP_PRESCRIPT,"w") as f:
				f.write(fcontent)
			os.chmod(LLXUP_PRESCRIPT,0o755)
#def _generateDemoteScript

def _disablePinning():
	pinf="/etc/apt/preferences.d/lliurex-pinning"
	if os.path.isfile(pinf)==True:
		with open(pinf,"r") as f:
			lines=f.readlines()
		disabled=[]
		for line in lines:
			disabled.append("#${}".format(line.strip()))
		with open(pinf,"w") as f:
			f.write("\n".join(disabled))
	return()
#def _disablePinning

def _generatePostInstallScript():
		#DISABLED
		return
		fcontent="#!/bin/bash\n"
		fcontent+="ACTION=\"$1\"\n"
		fcontent+="case \"$ACTION\" in\n" 
		fcontent+="postActions)\n"
		fcontent+="dpkg --set-selections < {0}\n".format(os.path.join(TMPDIR,"dselect"))
		fcontent+="apt-get dselect-upgrade -y || true\n"
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
	_disablePinning()
	return()
#def enableUpgradeRepos

def clean():
	cmd=["apt-get","clean"]
	subprocess.run(cmd)
#def clean

def _enablePinning():
	pinf="/etc/apt/preferences.d/lliurex-pinning"
	if os.path.isfile(pinf)==True:
		with open(pinf,"r") as f:
			lines=f.readlines()
		enabled=[]
		for line in lines:
			enabled.append("{}".format(line.replace("#$","",1).strip()))
		with open(pinf,"w") as f:
			f.write("\n".join(enabled))
	return()
#def _enablePinning

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
	shutil.copy(os.path.join(wrkdir,os.path.basename(SOURCESF)),SOURCESF)
	wrksourcesd="{}.d".format(os.path.join(wrkdir,os.path.basename(SOURCESF)))
	sourcesd="{}.d".format(os.path.join(SOURCESF))
	if os.path.isdir(wrksourcesd):
		for f in os.listdir(wrksourcesd):
			if f.endswith(".list"):
				shutil.copy(os.path.join(wrksourcesd,f),os.path.join(sourcesd,f))
	removeAptConf()
	_enablePinning()
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
	aptFlags=["install","-y","--allow-downgrades","--reinstall"]
	pkgList="lliurex-up={0} lliurex-up-core={0} lliurex-up-cli={0} lliurex-up-indicator={0} python3-lliurexup={0}".format(uprelease)
	cmd=["apt-get"]
	cmd.extend(aptFlags)
	cmd.extend(pkgList.split())
	print(cmd)
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
		tarf.add("{}".format(SOURCESF))
		tarf.add("{}.d/".format(SOURCESF))
#def copySystemFiles

def _modifyAptConf(repodir=""):
	if repodir=="" or os.path.exists(repodir)==False:
		repodir=REPODIR
	aptconf="/etc/apt/apt.conf"
	_debug("APT cache: {}".format(repodir))
	if os.path.isfile(aptconf)==True:
		shutil.copy(aptconf,TMPDIR)
	elif os.path.exists(os.path.join(TMPDIR,os.path.basename(aptconf))):
		os.unlink(os.path.join(TMPDIR,os.path.basename(aptconf)))
	if os.path.isdir(repodir)==False:
		os.makedirs(repodir)
	with open(aptconf,"w") as f:
		f.write("Dir::Cache{{Archives {0}}}\nDir::Cache::Archives {0};".format(repodir))
#def _modifyAptConf

def setLocalRepo(release="jammy",repodir=""):
	if repodir=="" or os.path.exists(repodir)==False:
		repodir=REPODIR
	tmpsources=os.path.join(TMPDIR,".{}".format(os.path.basename(SOURCESF)))
	dists=[release,"{}-updates".format(release),"{}-security".format(release)]
	with open(tmpsources,"w") as f:
		for dist in dists:
			repo=os.path.join(repodir,dist)
			f.write("deb [trusted=yes] file:{} ./\n".format(repo))
			_debug("LocalRepo deb [trusted=yes] file:{} ./".format(repo))
	shutil.copy(tmpsources,SOURCESF)
	_deleteAptLists()
	_modifyAptConf(repodir)
#def setLocalRepo

def _deleteAptLists():
	wrkdir="/var/lib/apt/lists/"
	for f in os.listdir(wrkdir):
		dest=os.path.join(wrkdir,f)
		if os.path.isfile(dest) and f!="lock":
			os.unlink(dest)
#def _deleteAptLists

def downloadPackages(pkgs,repodir=""):
	if repodir=="" or os.path.exists(repodir)==False:
		repodir=REPODIR
	clean()
	cmd=["apt-get","dist-upgrade","-y","-d","-o","Dir::Cache::Archives={0}".format(repodir)]
	subprocess.run(cmd)
	repoerr="/usr/share/llx-upgrade-release/err"
	f=open(repoerr,"w")
	f.close()
	for pkg in pkgs:
		cmd=["apt-get","install","-y","-d","--reinstall",pkg,"-o","Dir::Cache::Archives={0}".format(repodir)]
		prc=subprocess.run(cmd,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
		_debug("Get: {}".format(pkg))
		if prc.returncode!=0:
			olddir=os.getcwd()
			os.chdir(repodir)
			_debug("Download: {})".format(pkg))
			cmd=["apt-get","download","{}".format(pkg)]
			prc=subprocess.run(cmd,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
			os.chdir(olddir)
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
		
	repos=_readLocalRepo(repodir)
	_cleanLocalRepo(repodir,repos)
	for url,urldata in repos.items():
		for data in urldata:
			dist=data.get("dist","")
			if len(dist)<=0:
				continue
			repo=os.path.join(repodir,dist)
			for component in data.get("components",[]):
				packagesf=downloadFile("{0}/dists/{2}/{3}/binary-amd64/Packages".format(url,dist.split("-")[0],dist,component))
				if os.path.isfile(packagesf)==False:
					packagesgz=downloadFile("{0}/dists/{2}/{3}/binary-amd64/Packages.gz".format(url,dist.split("-")[0],dist,component))
					packagesf=packagesgz.replace(".gz","")
					with gzip.open(packagesgz, 'rb') as f:
						fcontent = f.read().decode()
					with open(packagesf, 'a') as f:
						f.write(fcontent)
					
				if os.path.isfile(packagesf)==False:
					continue
				with open(packagesf,"r") as f:
					fcontent=f.read()
				path="./"
				if repo!=repodir:
					path="../"
				line=[]
				_debug("Generating {0} PACKAGES in {1} for {2} ({3})".format(component,repo,dist,url))
				with open(os.path.join(repo,"Packages"),"a") as f:
					for fline in fcontent.split("\n"):
						if fline.startswith("Filename:"):
							line=fline.split(" ")
							fline=" ".join([line[0],"{0}{1}".format(path,os.path.basename(line[1]))])
						f.write("{}\n".format(fline))
	_modifyAptConf(repodir)
	return()
#def generateLocalRepo

def _cleanLocalRepo(repodir="",repos={}):
	if repodir=="" or os.path.exists(repodir)==False:
		repodir=REPODIR

	for url,urldata in repos.items():
		for data in urldata:
			dist=data.get("dist","")
			repo=os.path.join(repodir,dist)
			_debug("Clean {}".format(repo))
			if os.path.isdir(repo)==False:
				os.makedirs(repo)
			f=open(os.path.join(repo,"Packages"),"w")
			f.close()
	return()
#def _cleanLocalRepo

def _readLocalRepo(repodir=""):
	if repodir=="" or os.path.exists(repodir)==False:
		repodir=REPODIR

	repos={}
	print("BEGIN")
	with open(SOURCESF,"r") as f:
		fcontent=f.readlines()
	for l in fcontent:
		line=l.strip().split()
		url=""
		components=[]
		array_idx=[index for (index, item) in enumerate(line) if ":/" in item]
		if len(array_idx)>0:
			idx=array_idx[0]
			url=line[idx]
			dist=line[idx+1]
			components=line[idx+2:]
		if repos.get(url,"")=="":
			repos[url]=[{"dist":dist,"components":components}]
		else:
			repos[url].append({"dist":dist,"components":components})
	return(repos)
#def _readLocalRepo

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
	_debug("LLXUP URL: {}".format(data.get("url")))
	llxup.defaultUrltoCheck=data.get("url")
	_debug("LLXUP RELEASE: {}".format(data.get("version")))
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
	
#def CHkUpgradeResult

def fixAptSources(repodir="",release="jammy"):
	if repodir=="" or os.path.exists(repodir)==False:
		repodir=REPODIR
	_debug("Setting dir for repo: {}".format(repodir))
	llxup_sources=os.path.join(os.path.dirname(SOURCESF),"lliurexup_sources.list")
	tmpllxup_sources=os.path.join(TMPDIR,"lliurexup_sources.list")
	if os.path.isfile(llxup_sources):
		os.unlink(llxup_sources)
	fcontent=[]
	fcontent.append("deb [trusted=yes] file:{}/ ./\n".format(os.path.join(repodir,release)))
	fcontent.append("deb [trusted=yes] file:{}-updates/ ./\n".format(os.path.join(repodir,release)))
	fcontent.append("deb [trusted=yes] file:{}-security/ ./\n".format(os.path.join(repodir,release)))
	fcontent.append("")
	tmpsources=os.path.join(TMPDIR,os.path.basename(SOURCESF))
	with open (tmpsources,"w") as f:
		f.writelines(fcontent)
		_debug("FixRepo {}".format(fcontent))
	shutil.copy(tmpsources,SOURCESF)
	shutil.copy(tmpsources,llxup_sources)
#def fixAptsources


def _enableIpRedirect():
	##DEPRECATED##
	return
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
			_debug("CMD: {}".format(" ".join(cmd)))
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
	llxup_sources="/etc/apt/lliurexup_sources.list"
	f=open(SOURCESF,"w")
	f.close()
	cmd=["repoman-cli","-e","0","-y"]
	subprocess.run(cmd)
	if os.path.isfile(llxup_sources):
		os.unlink(llxup_sources)
	shutil.copy(SOURCESF,llxup_sources)
	return()
#def unfixAptsources

def removeAptConf():
	aptconf="/etc/apt/apt.conf"
	tmpaptconf=os.path.join(TMPDIR,os.path.basename(aptconf))
	sw=False
	if os.path.isfile(tmpaptconf)==True and os.path.isfile(aptconf)==True:
		if filecmp.cmp(aptconf,tmpaptconf,shallow=True)==False:
			sw=True
	if os.path.isfile(aptconf):
		os.unlink(aptconf)
	if sw==True:
		shutil.copy(tmpaptconf,aptconf)
	if os.path.isfile(tmpaptconf):
		os.unlink(tmpaptconf)
	return()
#def removeAptConf

def enableSystemdServices():
	for i in ["network-manager","systemd-networkd"]:
		cmd=["service",i,"start"]
		subprocess.run(cmd)
	return()
#def enableSystemdServices
