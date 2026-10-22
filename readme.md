👻 ROOTGHOST — Discord Bot

«Security • Moderation • Automation • Community»

ROOTGHOST es un bot de Discord desarrollado con Python y "discord.py 2.x", diseñado para ayudar a administrar servidores mediante comandos slash, automatizaciones y herramientas de moderación.

Su objetivo es ofrecer una administración más organizada, segura y sencilla, con una estructura modular que permite agregar nuevas funciones sin tener que reescribir todo el bot.

---

📌 Características

- Comandos slash: interacción mediante comandos "/" directamente desde Discord.
- Moderación: herramientas para ayudar al equipo administrativo a mantener el orden.
- Autoroles múltiples: permite configurar varios roles para los nuevos miembros.
- Sistema modular: las extensiones se organizan en la carpeta "commands/".
- Configuración persistente: algunas funciones guardan sus ajustes en archivos JSON.
- Ejecución en Termux: permite alojar el bot desde un dispositivo Android.
- Desarrollo ampliable: facilita incorporar nuevos comandos y sistemas.

Las funciones disponibles dependen de los módulos que estén instalados y correctamente configurados.

---

🧠 ¿Cómo funciona?

ROOTGHOST utiliza Python y la biblioteca "discord.py".

1. Archivo principal

"bot.py"

Es el punto de entrada del bot. Se encarga de iniciar el cliente de Discord, cargar las extensiones configuradas y sincronizar los comandos de aplicación.

2. Carpeta de comandos

"commands/"

Aquí se encuentran los módulos del bot. Cada archivo puede contener comandos, eventos o funciones relacionadas con una característica específica.

Por ejemplo:

- "autorole_setup.py": configuración del autorol.
- "hola.py": comando de saludo.
- Otros módulos: moderación, administración y herramientas adicionales, según la versión instalada.

3. Carpeta de datos

"data/"

Guarda configuraciones persistentes utilizadas por algunos módulos. Por ejemplo, el sistema de autoroles puede almacenar sus ajustes en "data/autorole.json".

Consejo: no elimines los archivos JSON sin saber qué configuración contienen. Podrías perder ajustes de tu servidor.

4. Inicio del bot

"start.sh"

Es el script utilizado para iniciar ROOTGHOST desde Termux.

---

⚙️ Instalación y ejecución

Requisitos

- Python compatible con la versión instalada de "discord.py".
- Una aplicación de Discord Bot creada en el "Discord Developer Portal" (https://discord.com/developers/applications).
- El token configurado de forma privada.
- Las dependencias necesarias del proyecto.

Iniciar en Termux

cd ~/ROOTGHOST
bash start.sh

Para detener el proceso que está ejecutándose en la terminal, normalmente puedes usar "CTRL + C".

Comprobar la sintaxis de un módulo

python -m py_compile commands/autorole_setup.py

Si no aparece ningún mensaje, el archivo superó la comprobación de sintaxis. Esto no garantiza que todas sus funciones trabajen correctamente en Discord.

Actualizar desde GitHub

cd ~/ROOTGHOST
git pull origin master

Antes de actualizar, guarda tus cambios locales. Si Git informa conflictos, revísalos antes de continuar.

---

🎭 Sistema de autoroles

El sistema de autoroles permite configurar varios roles que se asignarán automáticamente cuando entre un nuevo miembro.

Comandos disponibles

Comando| Función
"/autorol-configurar"| Agrega un rol automático.
"/autorol-ver"| Muestra los roles configurados.
"/autorol-quitar-rol"| Quita un rol específico.
"/autorol-quitar"| Desactiva todos los autoroles.

Para configurar varios roles, ejecuta "/autorol-configurar" varias veces y selecciona un rol diferente en cada uso.

Requisitos del autorol

- El bot debe tener el permiso Gestionar roles.
- El rol más alto del bot debe estar por encima de cada rol que deba asignar.
- El intent de miembros ("members") debe estar habilitado en el código y en el Developer Portal.
- El módulo debe cargarse correctamente.

Los roles que no cumplan los requisitos de permisos o jerarquía no podrán asignarse.

---

🛡️ Seguridad y buenas prácticas

Protege el token

El token permite controlar el bot. Nunca lo publiques en GitHub, capturas de pantalla, mensajes o archivos públicos.

Utiliza una variable de entorno como "DISCORD_TOKEN" y evita guardar credenciales directamente en el código.

Si el token se expone, restablécelo desde el Discord Developer Portal.

Protege el repositorio

- Mantén ".env" fuera de Git mediante ".gitignore".
- No publiques contraseñas, tokens ni otros secretos.
- Revisa los cambios antes de hacer "git push".
- Conserva copias de seguridad de los archivos importantes.
- Evita sobrescribir módulos que ya funcionan sin guardar una copia.

Aplica permisos mínimos

No todos los comandos necesitan permisos de administrador. Asigna únicamente los permisos que cada función requiera y restringe las herramientas sensibles al personal autorizado.

Revisa los registros

Los mensajes de la consola pueden ayudar a detectar módulos que no se cargaron, problemas de permisos, errores de Discord y fallos durante la asignación de roles.

No compartas registros sin revisar que no contengan información privada.

---

🧰 Solución de problemas

El bot está online, pero no aparecen los comandos.

- Comprueba que la extensión se haya cargado.
- Revisa que los comandos se hayan sincronizado correctamente.
- Busca errores como "CommandAlreadyRegistered".
- Verifica que el bot esté instalado en el servidor con los permisos necesarios.

El autorol no funciona.

- Comprueba la configuración con "/autorol-ver".
- Verifica los permisos del bot y la jerarquía de roles.
- Revisa que "members" esté habilitado.
- Consulta la consola cuando entre un miembro nuevo.

Un módulo no compila.

Ejecuta "python -m py_compile" sobre el archivo afectado y revisa la línea indicada en el error.

Git no permite actualizar.

Puede haber modificaciones locales que entren en conflicto con GitHub. Guarda los cambios y resuelve el conflicto antes de continuar. No uses comandos destructivos sin entender qué archivos se perderían.

---

💡 Consejos para desarrollar ROOTGHOST

1. Un módulo por función: mantiene el código organizado y facilita encontrar errores.
2. Evita duplicados: antes de crear un comando, comprueba que no exista en otro módulo.
3. Prueba antes de publicar: compila los archivos modificados y verifica las funciones dentro de un servidor de pruebas.
4. Guarda las configuraciones: usa archivos JSON u otro almacenamiento adecuado cuando una función deba recordar sus ajustes.
5. Maneja los errores: los comandos deben responder de forma clara cuando faltan permisos o parámetros.
6. Documenta los cambios: explica las funciones nuevas y sus requisitos.
7. Actualiza con cuidado: conserva los cambios locales antes de descargar modificaciones desde GitHub.
8. Protege los datos: evita almacenar información innecesaria de los miembros.

---

🚀 Ideas para futuras versiones

- Sistema de registros de moderación.
- Protección contra spam y enlaces no autorizados.
- Sistema de verificación de miembros.
- Panel de configuración para administradores.
- Estadísticas de actividad.
- Sistema de tickets de soporte.
- Copias de seguridad de configuraciones.
- Pruebas automatizadas para los módulos.

Estas son ideas de desarrollo, no una garantía de que ya estén implementadas.

---

📂 Estructura del proyecto

ROOTGHOST/
├── bot.py
├── start.sh
├── commands/
│   ├── autorole_setup.py
│   ├── hola.py
│   └── ...
├── data/
│   └── autorole.json
├── .env
├── .gitignore
└── README.md

La estructura puede variar según los módulos instalados. El archivo ".env" debe permanecer privado y no debe publicarse en el repositorio.

---

📜 Tecnologías

- Python: lenguaje de programación principal.
- discord.py 2.x: biblioteca para interactuar con Discord.
- Discord Application Commands: comandos slash.
- JSON: almacenamiento sencillo de configuraciones.
- Git y GitHub: control de versiones y alojamiento del código.
- Termux: entorno de ejecución en Android.

---

👻 ROOTGHOST SECURITY SYSTEM

ROOTGHOST es un proyecto en desarrollo. La seguridad depende tanto del código como de los permisos configurados, el cuidado de las credenciales y las actualizaciones del proyecto.

Desarrolla con cuidado. Prueba cada cambio. Protege tu comunidad.