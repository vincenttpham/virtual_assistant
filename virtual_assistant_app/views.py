from django.shortcuts import render, redirect
import openai
from .secret_key import API_KEY
openai.api_key = API_KEY


# Create your views here.
def index(request):
    try:
        # if the session does not have a messages key, create one
        if 'messages' not in request.session:
            request.session['messages'] = [
                {"role": "assistant", "content": "Hi, how can I help you?"},
            ]
        if 'prompts' not in request.session:
            request.session['prompts'] = [
                {"role": "system", "content": ""},
            ]
        if request.method == 'POST':
            # get the prompt from the form
            prompt = request.POST.get('prompt')
            message = request.POST.get('prompt')
            if 'upload' in request.FILES:
                upload = request.FILES['upload']
                request.session['messages'].append({"role": "user", "content": upload.name})
                request.session.modified = True
                if prompt == '':
                    request.session['messages'].append({"role": "assistant", "content": "If you send me a file without telling me what to do with it, how am I supposed to help you?"})
                    request.session.modified = True
                    context = {
                        'messages': request.session['messages'],
                        'prompt': '',
                        'temperature': 1,
                    }
                    return render(request, 'index.html', context)
                if not upload.name.endswith('.csv'):
                    request.session['messages'].append({"role": "assistant", "content": "Sorry, I'm only programmed to read CSV files at the moment. Try sending me a CSV file and I'll try my best to assist you."})
                    request.session.modified = True
                    context = {
                        'messages': request.session['messages'],
                        'prompt': '',
                        'temperature': 1,
                    }
                    return render(request, 'index.html', context)
                #if file is too large, return
                if upload.multiple_chunks():
                    request.session['messages'].append({"role": "assistant", "content": "The uploaded file is too big (%.2f MB)."})
                    request.session.modified = True
                    context = {
                        'messages': request.session['messages'],
                        'prompt': '',
                        'temperature': 1,
                    }
                    return render(request, 'index.html', context)
                
                file_data = upload.read().decode("utf-8")

                lines = file_data.split("\n")
                next(iter(lines))

                #loop over the lines and add them in prompt. If error , store as string and then display
                prompt += "\n"
                upload_content = ""
                for line in lines:
                    fields = line.split(",")
                    for field in fields:
                        upload_content += str(f"{field}")
                    upload_content += "\n"
                prompt += f"###\n{upload_content}\n###"

            # get the temperature from the form
            temperature = float(request.POST.get('temperature', 0.1))
            # append the prompt to the messages list
            request.session['messages'].append({"role": "user", "content": message})
            request.session.modified = True
            request.session['prompts'].append({"role": "user", "content": prompt})
            # set the session as modified
            request.session.modified = True
            # call the openai API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=request.session['prompts'],
                temperature=temperature,
                max_tokens=1000,
            )
            # format the response
            formatted_response = response['choices'][0]['message']['content']
            # append the response to the messages list
            request.session['messages'].append({"role": "assistant", "content": formatted_response})
            request.session.modified = True
            request.session['prompts'].append({"role": "assistant", "content": formatted_response})
            request.session.modified = True
            # redirect to the home page
            context = {
                'messages': request.session['messages'],
                'prompt': '',
                'temperature': temperature,
            }
            return render(request, 'index.html', context)
        else:
            # if the request is not a POST request, render the home page
            context = {
                'messages': request.session['messages'],
                'prompt': '',
                'temperature': 1,
            }
            return render(request, 'index.html', context)
    except Exception as e:
        print(e)
        # if there is an error, redirect to the error handler
        return redirect('error_handler')

def new_chat(request):
    # clear the messages list
    request.session.pop('messages', None)
    request.session.pop('prompts', None)
    return redirect('index')

def error_handler(request):
    return render(request, '404.html')