from flask import Flask, request, jsonify, send_from_directory
import os, time, boto3
from botocore.exceptions import ClientError

app = Flask(__name__, static_folder="static")

# --- Serve index.html ---
@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


# --- Environment Variables ---
S3_BUCKET = os.environ.get("S3_BUCKET")
DDB_TABLE = os.environ.get("DDB_TABLE")
SIGNED_URL_EXP = 3600  # 1 hour

# --- AWS Clients ---
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DDB_TABLE)


# --- Generate FIR Number ---
def generate_fir_number():
    """Generate FIR number in format FIR-YYYYMMDD-XXX"""
    today = time.strftime("%Y%m%d")  # e.g., 20251022

    response = table.scan(
        FilterExpression="begins_with(file_number, :prefix)",
        ExpressionAttributeValues={":prefix": f"FIR-{today}-"}
    )
    items = response.get("Items", [])
    if items:
        counters = [int(item["file_number"].split("-")[-1]) for item in items]
        counter = max(counters) + 1
    else:
        counter = 1

    return f"FIR-{today}-{counter:03d}"


# --- Upload Route ---
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    description = request.form.get("description", "")  # optional user description

    file_number = generate_fir_number()
    filename = file.filename
    s3_key = f"uploads/{file_number}/{filename}"

    try:
        # Upload file to S3
        s3.upload_fileobj(file, S3_BUCKET, s3_key, ExtraArgs={"ServerSideEncryption": "AES256"})

        # Store metadata in DynamoDB
        metadata = {
            "file_number": file_number,
            "s3_key": s3_key,
            "filename": filename,
            "description": description,
            "content_type": file.content_type or "application/octet-stream",
            "uploaded_at": int(time.time())
        }
        table.put_item(Item=metadata)

        return jsonify({
            "message": "Upload successful",
            "file_number": file_number,
            "filename": filename,
            "description": description
        }), 201

    except ClientError as e:
        return jsonify({"error": str(e)}), 500


# --- Download by file_number ---
@app.route("/download/<file_number>", methods=["GET"])
def download(file_number):
    try:
        response = table.get_item(Key={"file_number": file_number})
        item = response.get("Item")

        if not item:
            return jsonify({"error": "File not found"}), 404

        s3_key = item["s3_key"]
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_key},
            ExpiresIn=SIGNED_URL_EXP
        )

        return jsonify({
            "download_url": url,
            "filename": item["filename"],
            "description": item.get("description", "")
        })

    except ClientError as e:
        return jsonify({"error": str(e)}), 500


# --- Download by filename ---
@app.route("/download-by-filename/<filename>", methods=["GET"])
def download_by_filename(filename):
    try:
        response = table.scan(
            FilterExpression="filename = :filename",
            ExpressionAttributeValues={":filename": filename}
        )
        items = response.get("Items", [])
        if not items:
            return jsonify({"error": f"No file found with filename '{filename}'"}), 404

        # If multiple found, return the most recent one
        item = sorted(items, key=lambda x: x["uploaded_at"], reverse=True)[0]
        s3_key = item["s3_key"]

        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_key},
            ExpiresIn=SIGNED_URL_EXP
        )

        return jsonify({
            "download_url": url,
            "file_number": item["file_number"],
            "filename": item["filename"],
            "description": item.get("description", "")
        })

    except ClientError as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
