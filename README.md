# Actualitzador de versions de Lliurex

Esta eina proveix un mecanisme per a actualitzar versions majors de Lliurex.

# Configuració

La informació requerida deuría estar a un servidor.

* Fitxer llxXX.tar (XX=versió major) -> Es un fitxer tar que inclou tota la informació necesaria per a la actualització. Pot continder el que es considere però obligatoriament cal incloure el fitxer sources.list de la nova versió i un fitxer demoted.cfg amb la llista de paquets a eliminar per incompatibilidat.
* Fitxer meta-release -> Es una especie de changelog entre versions. Es estructurat i conté tota la informació de la nova versió.

# Execució

L'actualitzador compara la versió local amb la que té el fitxer meta-release al servidor. Si troba una nova versió s'aemet un avís a l'usuari.
Al encentar es descarrega el fitxer llxXX.tar (de la url indicada en meta-release) i el processa. Els repos originals es copien a lloc seguro i es desactiven, després es copia el sources.list a /etc/apt
Una vegada copiat el actualitzador configura un core de LliurexUp amb els nous repositoris i procedeix a actualitzar desde ell el propi Lliurex-Up i a generar el script de initActions per a eliminar els paquets inclosos a demoted.cfg. En terminar executa lliurex-up.

# Actualització

Lliurex-Up  executa el script per a eliminar els paquets i continua amb el seu comportament habitual. Al terminar el procès compara la versió local amb la indicada per meta-releases, si coincideixen es suposa que l'actualització ha terminat correctament.
De no ser així es suposa que quelcom ha fallat i tracta de deixar el sistema al menys roin dels escenaris, revertint els repositoris a l'estat original i tractant de desactualitzar lliurex-up.

#############
# Actualizador de versiones de Lliurex

Esta herramienta provee un mecanismo para actualizar versiones mayores de Lliurex

# Configuración

La información necesaria deberia estar en un servidor.

* Fichero llxXX.tar (XX=versión mayor) -> Es un fichero tar que incluye toda la información necesaria para la actualización. Puede contener lo que se considere pero obligatoriamente debe incluir el fichero sources.list de la nueva versión y un fichero demoted.cfg con la lista de paquetes a eliminar por incompatibilidad.
* Fichero meta-release -> Es una especie de changelog entre versiones. Está estructurado y contiene toda la información relevante de la nueva versión.

# Ejecución

El actualizador compara la versión local con la que tiene el fichero meta-release en el servidor. Si encuentra una nueva versión se avisa al usuario.
Al comenzar se descarga el fichero llxXX.tar (de la url indicada en meta-release) y lo procesa. Los repos originales se copian a sitio seguro y se desactivan, luego se copia el sources.list a /etc/apt
Una vez copiado el actualizador configura un core de LliurexUp con los nuevos repositorios y procede a actuallizar desde él el propio Lliurex-Up y a generar el script de initActions para eliminar los paquetes incluidos en demoted.cfg. Una vez hecho se ejecuta lliurex-up.

# Actualización

Lliurex-Up  ejecuta el script para eliminar los paquetes y procede según su comportamiento habitual. Cuando el proceso termina el actualizador compara la versión local con la indicada en meta-releases, si coinciden se supone que la actualización ha terminado correctamente.
De no ser así se supone que algo ha fallado y trata de dejar el sistema en el menos malo de los escenarios, revertiendo los repositorios a su estado original y tratando de desactualizar lliurex-up.

#############

# Upgrader for Lliurex

This tool provides a way for upgrade major releases in Lliurex. 

# Configuration

The information needed must be ideally provided from a server.

* File llxXX.tar (XX=major version of the release) -> This is a tar file that includes the info needed for the upgrade. It can store any info needed but it needs to include the sources.list of the new release and a comited.cfg files with packages that must be removed before upgrade
* File meta-release -> This file it's a sort of changelog for the releases. It's a structured file with relevant info of the release. 

# Execution

The upgrader compares the local release with the meta-release file. If it finds a new release then an advice is showed.
Then the file llxXX.tar (as defined on the meta-release file) is downloaded and processed. The original repos are backed up and disabled, then the included sources.list is copied to /etc/apt.
After that the upgrader configures a LliurexUp core with the new repos and proceeds to upgrade lliurexup itself. When this step is accomplished a script with the packages to demote is generated and placed inside initActions folder of lliurex-up and then lliurex-up gets invoked.

# Upgrade
Lliurex-up executes the init script for removing offending packages and begins as usual.
When lliurex-up process ends the upgrader compares the actual local release with the targeted release, if they're both the same then assumes that the upgrade went OK.
If the releases aren't the same then the upgrader tries to revert to the less worst situation:
 - Repositories are restored to original
 - Lliurex-up is downgraded

