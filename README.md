#Commands for bott 
- subir - subir a la nube 
- copiar - copiar de una nube a la otra
- configuracion - configurar rclone 
- info - info del bot 
- exec - ejecutar comandos linux 
- logs - obtener logs del servidor 
- servidor - obtener info del servidor
- test_velocidad- test velocidad 
- limpiar- limpiar descargas

#Secrets for github

    HEROKU_API_KEY
    HEROKU_APP_NAME
    HEROKU_EMAIL
    
    
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=)    


#Deploy Manual Run the following commands. (Following commands can be used to setup the vps from scratch) 
- sudo apt update 
- sudo apt install -y python3.8 
- sudo apt install -y python3-venv 
- python3 -m venv venv 
- source venv/bin/activate 
- pip install -r requirements.txt 
- curl https://rclone.org/install.sh | bash

And finally run this in clonned folder. chmod 777 start.sh ./start.sh

