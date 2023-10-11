from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.conf import settings
import json
import openai
from .secret_key import API_KEY
openai.api_key = API_KEY

# Create your views here.
def index(request):
    # if the session does not have a messages key, create one
    # messages will be used for display on the chatbox
    if 'messages' not in request.session:
        request.session['messages'] = [
            {"role": "assistant", "content": "Hi, how can I help you?"},
        ]
    # prompts will be used for chat completions
    if 'prompts' not in request.session:
        request.session['prompts'] = []
    # by keeping 2 separate logs, I can put custom responses into the message view while keeping the token count low

    # set persistent chatbox for mobile screens
    if 'chatbox' not in request.session:
        request.session['chatbox'] = ''
    context = {
            'messages': request.session['messages'],
            'showbox': request.session['chatbox'],
        }
    return render(request, 'index.html', context)

def send_prompt(request):
    try:
        if request.method == 'POST':
            # get the prompt from the form
            prompt = request.POST.get('prompt')
            message = request.POST.get('prompt')
            # set persistent chatbox for mobile screens
            request.session['chatbox'] = 'showbox'
            if 'upload' in request.FILES:
                upload = request.FILES['upload']
                # user will see file name to confirm successful upload
                request.session['messages'].append({"role": "user", "content": upload.name})
                request.session.modified = True
                # if no prompt
                if prompt == '':
                    request.session['messages'].append({"role": "assistant", "content": "If you send me a file without instructions on what to do with it, how am I supposed to help you?"})
                    request.session.modified = True
                    return redirect('index')
                # if uploaded file isnt csv, return message
                if not upload.name.endswith('.csv'):
                    request.session['messages'].append({"role": "assistant", "content": "Sorry, I'm only programmed to read CSV files at the moment. Try sending me a CSV file and I'll try my best to assist you."})
                    request.session.modified = True
                    return redirect('index')
                #if file is too large, return
                if upload.multiple_chunks():
                    request.session['messages'].append({"role": "assistant", "content": "The uploaded file is too big (%.2f MB)."})
                    request.session.modified = True
                    return redirect('index')

                # add file data to session
                file_data = upload.read().decode("unicode_escape")
                lines = file_data.split("\n")
                next(iter(lines))
                # loop over the lines and add them to prompt
                upload_content = ""
                for line in lines:
                    upload_content += str(f"{line}")
                    fields = line.split(",")
                    for field in fields:
                        upload_content += str(f"{field}")
                prompt += f"###{upload_content}###"

                # testing potential file reading in session for lower token count
                """
                request.session['upload'] = []
                reader = csv.DictReader(upload.read().decode('unicode_escape').splitlines(), delimiter=',')
                for row in reader:
                    request.session['upload'].append(row)
                    request.session.modified = True
                """

            # s_key = request.session.session_key

            functions = [
                {
                    "name": "send_email",
                    "description": "Sends an email to the specified recipients",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recipients": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                                "description": "Email addresses to send the email to",
                            },
                            "subject": {"type": "string"},
                            "body": {"type": "string"},
                        },
                        "required": ["recipients"],
                    },
                },
                {
                    "name": "generate_image",
                    "description": "Generates an image based on the prompt",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            ]

            # Step 1: send the conversation and available functions to GPT
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=request.session['prompts'],
                functions=functions,
                function_call="auto",
            )
            response_message = response['choices'][0]['message']

            # Step 2: check if GPT wanted to call a function
            if response_message.get("function_call"):
                # Step 3: call the function
                # Note: the JSON response may not always be valid; be sure to handle errors
                available_functions = {
                    "send_email": send_email,
                    "generate_image": generate_image,
                }
                function_name = response_message["function_call"]["name"]
                function_to_call = available_functions[function_name]
                function_args = json.loads(response_message["function_call"]["arguments"])
                if function_name == "send_email":
                    function_response = function_to_call(
                        recipients=function_args.get("recipients"),
                        subject=function_args.get("subject"),
                        body=function_args.get("body"),
                    )
                if function_name == "generate_image":
                    function_response = function_to_call(
                        prompt=prompt,
                    )
                request.session['messages'].append(
                    {
                        "role": "function",
                        "name": function_name,
                        "content": function_response,
                    }
                )
                request.session['prompts'].append(
                    {
                        "role": "function",
                        "name": function_name,
                        "content": function_response,
                    }
                )
                request.session.modified = True
                return redirect('index')
            
            # append the prompt to the messages list
            request.session['messages'].append({"role": "user", "content": message})
            request.session['prompts'].append({"role": "user", "content": prompt})
            # append the response to the messages list
            request.session['messages'].append(response_message)
            request.session['prompts'].append(response_message)
            request.session.modified = True
            return redirect('index')
        
        else:
            # if the request is not a POST request, return the home page
            return redirect('index')
        
    except Exception as e:
        # if there is an error, return error message
        request.session['messages'].append({"role": "assistant", "content": str(e)})
        request.session.modified = True
        return redirect('index')

def send_email(recipients, subject, body):
    try:
        email = EmailMessage(
            subject,
            body,
            f'Vincent <{settings.EMAIL_HOST_USER}>',
            recipients,
            reply_to=[settings.EMAIL_HOST_USER],
            headers={'Message-ID': 'foo'},
        )
        email.send(fail_silently=False)
        success = f"Email has been sent successfully.\n\nTo: {recipients}\nSubject: {subject}\nBody:\n\n{body}"
        return success
    except Exception as e:
        return e

def generate_image(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="256x256"
    )
    image_url = response['data'][0]['url']
    return image_url

"""
def personalized_email_outreach(s_key, message):
    s = Session.objects.get(pk=s_key)
    s_data = s.get_decoded()
    upload_data = []
    if 'upload' in s_data:
        upload_data = s_data['upload']
    for record in upload_data:
        prompt = message + "\n"
        prompt += f"###\n{record}\n###"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        response_message = response['choices'][0]['message']
        print(response_message)

    success = {
        "body": "Emails sent successfully",
    }
    return json.dumps(success)
"""

def new_chat(request):
    # clear the messages list
    request.session.pop('messages', None)
    request.session.pop('prompts', None)
    request.session.pop('upload', None)
    request.session.pop('chatbox', None)
    return redirect('index')