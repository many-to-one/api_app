import json
from openai import OpenAI
from django.http import JsonResponse
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Make sure to set your OpenAI API key in your environment or directly in the code (though not recommended for security reasons)
  # Or replace with your key like: openai.api_key = "your-api-key"

def chatbot_response(request):
    # Extract the user's message from the request (assuming it's a POST request)
    data = json.loads(request.body.decode('utf-8'))
    user_message = data.get('content')

    try:
        # Make a request to the OpenAI API to generate a response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # You can use "gpt-4" if available
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=100,  # Set the max tokens for the response (adjust as needed)
            n=1,  # Number of response completions to return
            stop=None,  # You can define stopping criteria here
            temperature=0.7  # Temperature controls randomness (0.7 is a balanced value)
        )

        # Extract the chatbot's reply
        chatbot_reply = response['choices'][0]['message']['content'].strip()

        print(' &&&&&&&&&&&&&& chatbot_response &&&&&&&&&&&&& ', chatbot_reply)

        # Return the chatbot's answer as JSON
        return JsonResponse(
            {
                'message': 'Chatbot answer generated successfully',
                'context': chatbot_reply,  # Return the generated answer
            }, 
            status=200,
        )

    except Exception as e:
        # In case of an error, return an error message
        print(f"Error generating response: {e}")
        return JsonResponse({'error': 'Something went wrong with the chatbot response'}, status=500)
