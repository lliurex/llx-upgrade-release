# Actualitzador de versions de Lliurex

Esta eina proveix un mecanisme per a actualitzar versions majors de Lliurex.

## Configuració

La informació requerida deuría estar a un servidor.

* Fitxer llxXX.tar (XX=versió major) -> Es un fitxer tar que inclou tota la informació necesaria per a la actualització. Pot continder el que es considere però obligatoriament cal incloure el fitxer sources.list de la nova versió i un fitxer demoted.cfg amb la llista de paquets a eliminar per incompatibilidat.
* Fitxer meta-release -> Es una especie de changelog entre versions. Es estructurat i conté tota la informació de la nova versió.

## Execució

L'actualitzador compara la versió local amb la que té el fitxer meta-release al servidor. Si troba una nova versió s'aemet un avís a l'usuari.
Al encentar es descarrega el fitxer llxXX.tar (de la url indicada en meta-release) i el processa. Els repos originals es copien a lloc segur i es desactiven, després es copia el sources.list a /etc/apt
Una vegada copiat el actualitzador extrau d'una banda la llista de paquets actualitzables i d'altra banda la llista de paquets instaŀlats localment. Després procedeix a emular la instaŀlació, descarregant aquells paquets que pel motiu que siga no son instanŀlables.
Quan tots els paquets s'han processat es dona pas al procés d'actualització propiament dit.

## Pasos previs a l'actualització

El programa genera un target per a systemd (equivalent a un runlevel de init) i dos scripts per a lliurex-up. El primer es una preaction que elimina els paquets incompatibles segons el fitxer demote.cfg, el segón es una postacion actualment sense ús. Una vegada tot preparat es bota al target de systemd.

## Actualització

El target de systemd es una réplica del target "rescue" que executa l'actualitzador al entrar. L'actualitzador s'encarrega de configurar l'entorn per a que lliurex-up es puga executar correctament. Quan s'executa Lliurex-up el primer que fa es autoactualitzar-se i posteriorment pasar a la instaŀlacio de paquets desde el repositori local configurat al pas anterior.
Al terminar el procès compara la versió local amb la indicada per meta-releases, si coincideixen es suposa que l'actualització ha terminat correctament. De no ser així es suposa que quelcom ha fallat i s'executa una aplicació de rescat per a poder concluir satisfactoriament el procés. 

#############
# Actualizador de versiones de Lliurex

Esta herramienta provee un mecanismo para actualizar versiones mayores de Lliurex

## Configuración

La información necesaria deberia estar en un servidor.

* Fichero llxXX.tar (XX=versión mayor) -> Es un fichero tar que incluye toda la información necesaria para la actualización. Puede contener lo que se considere pero obligatoriamente debe incluir el fichero sources.list de la nueva versión y un fichero demoted.cfg con la lista de paquetes a eliminar por incompatibilidad.
* Fichero meta-release -> Es una especie de changelog entre versiones. Está estructurado y contiene toda la información relevante de la nueva versión.

## Ejecución

El actualizador compara la versión local con la que tiene el fichero meta-release en el servidor. Si encuentra una nueva versión se avisa al usuario.
Al comenzar se descarga el fichero llxXX.tar (de la url indicada en meta-release) y lo procesa. Los repos originales se copian a sitio seguro y se desactivan, luego se copia el sources.list a /etc/apt
Una vez copiado el actualizador extrae pr un lado la lista de paquetes actualizables y por otro lado la lista de paquetes ya instalados. Después se procede a emular la instalación de todos ellos, descargando aquellos que por el motivo que sea no son instalables.
Cuando todos los paquetes se han procesado se pasa al proceso de actualización propiamente dicho.

## Pasos previos a la actualización

El programa genera un target para systemd (equivalente a un runlevel de Init) y dos scripts para lliurex-up. El primero es una preaction que elimina los paquetes incompatibles según el fichero demote.cfg. El segundo es una postacion actualmente sin uso. Una vez todo está preparado se lanza el target de systemd.

## Actualización

El target de systemd es una réplica del target "rescue" que ejecuta el actualizador al entrar. Éste se encarga de configurar el entorno para que Lliurex-Up pueda ejecutarse correctamente. Al ejecutarse Lliurex-Up se autoactualiza y pasa a la instalación de paquetes desde el repositorio local configurado en el paso anterior.
Al terminar el procese compara la versión local con la indicada en el fichero "meta-releases" y la lista de paquetes procesados: si todo parece correcto se supone que la actualización ha terminado correctamente. De no ser así se supone que algo ha ido mal y se ejecuta una aplicación de rescate para poder concluir satisfactoriamente el proceso.

#############

# Upgrader for Lliurex

This tool provides a way for upgrade major releases in Lliurex. 

## Configuration

The information needed must be ideally provided from a server.

* File llxXX.tar (XX=major version of the release) -> This is a tar file that includes the info needed for the upgrade. It can store any info needed but it needs to include the sources.list of the new release and a comited.cfg files with packages that must be removed before upgrade
* File meta-release -> This file it's a sort of changelog for the releases. It's a structured file with relevant info of the release. 

## Execution

The upgrader compares the local release with the meta-release file. If it finds a new release then an advice is showed.
Then the file llxXX.tar (as defined on the meta-release file) is downloaded and processed. The original repos are backed up and disabled, after that the included sources.list is copied to /etc/apt.
Once apt is configured the updater gets de upgradable packages and the installed packages in order to get a whole list of packages to be upgraded. Then the process simulates an install of all of them, downloading the packages that fails to install for some reason.
When all packages are processed the upgrade process begins.

## Previous steps for the upgrade

The app popilares a systemd target (equal to a init runlevel) and two scripts for lliurex-up. The first of them is a preaction that removes offending packahes according to the file demote.cfg. The second one is a postacion actualliy in disuse. When all is ready the process instruc systemd to go to the upgrade target.

## Upgrade
The systemd target is a copy of the "rescue" target that executes the upgrader when launched. The upgrader configures the environment for a correct execution of Lliure-Up. Lliurex-up executes the preaction and upgrades itself. Then  lliurex-up runs as usual upgrading the packages from the local reposity configured in previous step.
At the end the upgrader checks the local version againts the version present at file "meta-release" and the processed packages list. If all seems ok then it's supossed that the upgrade has ended succesfully. If it's not the case then a rescue application is launched in order to fix the system.

