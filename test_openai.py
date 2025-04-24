import os

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize the client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def test_openai_client():
    try:
        # Make a simple completion request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'Hello, OpenAI client is working!'"}
            ],
            max_tokens=50,
        )

        # Print the response
        print("✅ OpenAI client test successful!")
        print("Response:", response.choices[0].message.content)
        return True

    except Exception as e:
        print("❌ OpenAI client test failed!")
        print("Error:", str(e))
        return False


if __name__ == "__main__":
    test_openai_client()
