# An rclone bot to upload and transfer to many cloud servers, made by @SpiderSam

    - Upload telegram files to cloud.
    - Transfer from cloud to cloud.
    - Renaming of files before uploading.
    - Menu to list clouds from rclone.conf and selection of folders from cloud to upload.
    - Progress when downloading and uploading.

# Variables

    - API_ID
    - API_HASH
    - OWNER_ID
    - BOT_TOKEN
    - RCLONE_CONFIG

# Commands for bot(set through @BotFather) 
- start - mensaje bienvenida
- subir - subir a la nube 
- copiar - copiar de una nube a la otra
- configuracion - configurar rclone 
- info - info del bot 
- exec - ejecutar comandos linux 
- logs - obtener logs del servidor 
- servidor - obtener info del servidor
- test_velocidad- test velocidad 
- limpiar- limpiar descargas

# Secrets for github

    HEROKU_API_KEY
    HEROKU_APP_NAME
    HEROKU_EMAIL
    
    
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=)    

# Deploy to heroku
- Fork the repo.
- Create app in heroku
- Go to settings of app / config vars / add all variables
- connect to github and deploy
- turn on dynos

# Deploy Manual Run the following commands. 
- sudo apt update 
- sudo apt install -y python3.8 
- sudo apt install -y python3-venv 
- python3 -m venv venv 
- source venv/bin/activate 
- pip install -r requirements.txt 
- curl https://rclone.org/install.sh | bash
- chmod 777 start.sh 
- ./start.sh

