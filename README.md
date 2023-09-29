#virtual_assistant

This is a Virtual Assistant app made with a python/django back end and bootstrap/javascript front end. Powered by OpenAI API, the assistant can answer your questions and even read your CSV spreadsheets through the help of python logic.

Setup:

1. To use this app on your local machine, make sure you have python3 installed. Setup a virtual environment in the directory of your choice with "python3 -m venv va_venv" for example.

2. After creating the environment, activate it with "source va_venv/bin/activate".

3. Clone the project to the directory of your choice and then move into the directory through the terminal "cd virtual_assistant". Make sure your virtual environment is activated. Once inside the project directory, install the requirements with "pip install -r requirements.txt".

4. If you don't have an OpenAI API key, head over to https://platform.openai.com/account/api-keys to generate one. Once you have your key, create a new file called "secret_key.py" and add API_KEY='(your OpenAI API key)'.

5. Finally, while in the project directory, run the app with "python manage.py runserver" and the app should be running locally on your machine. Remember to go into the "settings.py" file and remove the contents inside the brackets of ALLOWED_HOSTS = []. You should be able to find the app at "localhost:8000" afterwards.

Deployment:

To deploy this app serverless on AWS Lambda while serving the static files from an S3 bucket, I used zappa and django-s3-storage.

Instructions:

1. While virtual environment is activated and inside the project directory, run "pip install zappa".

2. Once installed, run "zappa init". This will create a "zappa_settings.json" file. Add, "slim_handler": true, to the json file. This allows the sqlite database to be used with your lambda processes by serving it from an Amazon S3 bucket.

3. Once configured, run "zappa deploy" and it should output the link to the project.

4. After deployment, go into the "settings.py" file and add the address to "ALLOWED_HOSTS = []".

5. If you want to server static files from Amazon S3 to the project add these lines to the bottom of your "settings.py" file.



YOUR_S3_BUCKET = 'virtual-assistant-static'

STATICFILES_STORAGE = 'django_s3_storage.storage.StaticS3Storage'
AWS_S3_BUCKET_NAME_STATIC = YOUR_S3_BUCKET

# These next two lines will serve the static files directly 
# from the s3 bucket
AWS_S3_CUSTOM_DOMAIN = f'{YOUR_S3_BUCKET}.s3.amazonaws.com'

STATIC_LOCATION = 'static'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

AWS_DEFAULT_ACL = None



Where it says YOUR_S3_BUCKET = 'virtual-assistant-static', replace "virtual-assistant-static" with the name of your Amazon S3 bucket after you've created it.

6. Run "python manage.py collectstatic" to upload the static files to your S3 bucket to have them served to your Lambda process.



And just like that, the project is deployed and ready for use.