from flask import Flask, request, jsonify
from google.cloud import aiplatform, storage
import base64
import os
import datetime

app = Flask(__name__)

# Set project-specific variables
PROJECT_ID = "cc-gen-image-project"
ENDPOINT_ID = "5450632082118148096"
REGION = "us-central1"
BUCKET_NAME = "cc-gen-images-bucket"  # Replace with your bucket name

def upload_to_gcs(image_data, file_name):
    """Uploads the image to a GCS bucket."""
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)
    blob.upload_from_string(base64.b64decode(image_data), content_type="image/png")
    return f"gs://{BUCKET_NAME}/{file_name}"

def generate_image(prompt):
    """Generates an image from a text prompt using Vertex AI."""
    aiplatform.init(project=PROJECT_ID, location=REGION)
    endpoint = aiplatform.Endpoint(endpoint_name=f"projects/{PROJECT_ID}/locations/{REGION}/endpoints/{ENDPOINT_ID}")

    # Define input prompt and parameters
    instances = [{"text": prompt}]
    parameters = {
        "height": 768,
        "width": 768,
        "num_inference_steps": 25,
        "guidance_scale": 7.5
    }

    # Make the prediction
    response = endpoint.predict(instances=instances, parameters=parameters)

    # Process the response
    if response.predictions:
        image_data = response.predictions[0]["output"]  # Access the correct field, "output" for image bytes
        
        # Use the current time to make the filename unique
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"generated_image_{timestamp}_{prompt.replace(' ', '_')}.png"
        
        gcs_path = upload_to_gcs(image_data, file_name)
        return gcs_path
    else:
        raise ValueError("No predictions received from the endpoint.")

@app.route("/generate-image", methods=["POST"])
def generate_image_endpoint():
    """REST endpoint to generate an image."""
    data = request.get_json()
    if not data or "prompt" not in data:
        return jsonify({"error": "Missing 'prompt' in request payload"}), 400

    prompt = data["prompt"]
    try:
        gcs_path = generate_image(prompt)
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{gcs_path.split('/')[-1]}"
        return jsonify({"message": "Image generated successfully", "gcs_path": gcs_path, "public_url": public_url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
