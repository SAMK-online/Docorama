from flask import Flask, request, render_template, jsonify
import openai
import requests
import docx

app = Flask(__name__)

# Your OpenAI API key
OPENAI_API_KEY = ""
openai.api_key = OPENAI_API_KEY

# Your Captions AI API key
CAPTIONS_API_KEY = ""

@app.route("/", methods=["GET"])
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Document Summarization & Video Generation App</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <style>
            body {
                font-family: 'Roboto', sans-serif;
                background-color: #f3f4f6;
                color: #333;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                background-color: #ffffff;
                border-radius: 15px;
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
                padding: 40px;
                margin: 20px;
                transition: all 0.3s ease;
            }
            h1 {
                text-align: center;
                font-size: 1.8rem;
                color: #1f2937;
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-top: 15px;
                font-weight: 500;
                color: #4b5563;
            }
            input[type="file"],
            input[type="text"],
            textarea {
                width: 100%;
                padding: 10px;
                margin-top: 8px;
                border-radius: 8px;
                border: 1px solid #cbd5e1;
                outline: none;
                transition: border-color 0.3s;
            }
            input:focus,
            textarea:focus {
                border-color: #007BFF;
            }
            button {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 12px 18px;
                margin-top: 15px;
                border-radius: 8px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.3s, transform 0.3s;
                width: 100%;
                text-align: center;
            }
            button:hover {
                background-color: #0056b3;
                transform: translateY(-2px);
            }
            #loader {
                display: none;
                text-align: center;
                margin-top: 20px;
                font-weight: bold;
                color: #007BFF;
            }
            #progressBar {
                display: none;
                width: 100%;
                background-color: #e5e7eb;
                border-radius: 8px;
                overflow: hidden;
                margin-top: 20px;
            }
            #progress {
                width: 0;
                height: 10px;
                background-color: #007BFF;
                transition: width 0.5s;
            }
            #progressText {
                text-align: center;
                font-size: 14px;
                color: #1f2937;
                margin-top: 10px;
            }
            #response {
                margin-top: 20px;
                font-weight: bold;
                text-align: center;
                color: #1f2937;
                word-wrap: break-word;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Document Summarization & Video Generation App</h1>
            <form id="uploadForm" enctype="multipart/form-data">
                <label for="file">Upload DOCX file:</label>
                <input type="file" id="file" name="file" accept=".docx" required>
                <button type="submit">Summarize</button>
            </form>
            <h2>Summary:</h2>
            <div id="summary"></div>
            <form id="submitForm">
                <label for="creatorName">Creator Name:</label>
                <input type="text" id="creatorName" name="creatorName" required>
                <label for="script">Script:</label>
                <textarea id="script" name="script" rows="5" required></textarea>
                <button type="submit">Generate Video</button>
            </form>
            <div id="loader">Loading...</div>
            <div id="progressBar">
                <div id="progress"></div>
            </div>
            <div id="progressText">0%</div>
            <h2>Generated Video URL:</h2>
            <div id="response"></div>
        </div>
        <script>
            $(document).ready(function() {
                $('#uploadForm').on('submit', function(event) {
                    event.preventDefault();
                    var formData = new FormData(this);
                    $.ajax({
                        url: '/summarize',
                        type: 'POST',
                        data: formData,
                        contentType: false,
                        processData: false,
                        success: function(response) {
                            $('#summary').text(response.summary);
                            $('#script').val(response.summary);
                        },
                        error: function() {
                            alert('An error occurred while summarizing the document.');
                        }
                    });
                });
                $('#submitForm').on('submit', function(event) {
                    event.preventDefault();
                    var formData = {
                        creatorName: $('#creatorName').val(),
                        script: $('#script').val()
                    };
                    $('#loader').show();
                    $('#progressBar').show();
                    $('#progressText').text('0%');
                    $.ajax({
                        url: '/submit_script',
                        type: 'POST',
                        contentType: 'application/json',
                        data: JSON.stringify(formData),
                        success: function(response) {
                            var operationId = response.operationId;
                            if (!operationId) {
                                $('#loader').hide();
                                $('#progressBar').hide();
                                alert('Failed to get operation ID. Check the response from Captions AI.');
                                return;
                            }
                            setTimeout(function() {
                                pollVideoGeneration(operationId, 5000);
                            }, 30000);
                        },
                        error: function() {
                            $('#loader').hide();
                            $('#progressBar').hide();
                            alert('An error occurred while submitting the script.');
                        }
                    });
                });
                function pollVideoGeneration(operationId, interval) {
                    var currentProgress = 0;
                    var pollInterval = setInterval(function() {
                        $.ajax({
                            url: '/poll_status',
                            type: 'POST',
                            contentType: 'application/json',
                            data: JSON.stringify({ operationId: operationId }),
                            success: function(response) {
                                var progress = response.progress || 0;
                                if (progress > currentProgress) {
                                    currentProgress = progress;
                                    $('#progress').css('width', currentProgress + '%');
                                    $('#progressText').text(currentProgress + '%');
                                }
                                if (response.state === 'COMPLETED') {
                                    clearInterval(pollInterval);
                                    $('#loader').hide();
                                    $('#progressBar').hide();
                                    $('#response').text('Video URL: ' + response.videoUrl);
                                } else if (response.state === 'FAILED') {
                                    clearInterval(pollInterval);
                                    $('#loader').hide();
                                    $('#progressBar').hide();
                                    $('#response').text('Video generation failed.');
                                } else if (currentProgress >= 96) {
                                    clearInterval(pollInterval);
                                    setTimeout(function() {
                                        pollVideoGeneration(operationId, 15000);
                                    }, 15000);
                                }
                            },
                            error: function() {
                                clearInterval(pollInterval);
                                $('#loader').hide();
                                $('#progressBar').hide();
                                alert('An error occurred while polling the video generation status.');
                            }
                        });
                    }, interval);
                }
            });
        </script>
    </body>
    </html>
    """

@app.route("/summarize", methods=["POST"])
def summarize():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    try:
        doc = docx.Document(file)
        full_text = " ".join([paragraph.text for paragraph in doc.paragraphs])
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Ensure this model is supported in your setup
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise summaries."},
                {"role": "user", "content": f"Please provide a concise summary of the following text:\n\n{full_text}"}
            ],
            max_tokens=150,  # Adjust the token limit as needed
            temperature=0.5
        )
        
        # Check if the response contains the expected structure
        if isinstance(response, dict) and 'choices' in response and len(response['choices']) > 0:
            summary = response['choices'][0]['message']['content'].strip()
        else:
            # If the response is not in the expected format, use it as is
            summary = str(response).strip()
        
        return jsonify({"summary": summary})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "An error occurred while summarizing the document."}), 500

@app.route("/submit_script", methods=["POST"])
def submit_script():
    data = request.get_json()
    if not data or 'creatorName' not in data or 'script' not in data:
        return jsonify({"error": "Invalid data provided"}), 400
    creator_name = data['creatorName']
    script = data['script']
    url = "https://api.captions.ai/api/creator/submit"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": CAPTIONS_API_KEY
    }
    payload = {"creatorName": creator_name, "script": script}
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print("Error from Captions AI:", response.text)
            return jsonify({"error": "Failed to submit script to Captions AI"}), response.status_code
        return jsonify(response.json())
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "An error occurred while submitting the script."}), 500

@app.route("/poll_status", methods=["POST"])
def poll_status():
    data = request.get_json()
    if not data or 'operationId' not in data:
        return jsonify({"error": "Invalid data provided"}), 400
    operation_id = data['operationId']
    url = "https://api.captions.ai/api/creator/poll"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": CAPTIONS_API_KEY,
        "x-operation-id": operation_id
    }
    try:
        response = requests.post(url, headers=headers)
        if response.status_code != 200:
            print("Error from Captions AI:", response.text)
            return jsonify({"error": "Failed to poll status from Captions AI"}), response.status_code
        return jsonify(response.json())
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "An internal error occurred while polling status."}), 500

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000, debug=True)
