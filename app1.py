# from flask import Flask, request, jsonify, send_from_directory
# import os, uuid, time, boto3
# from botocore.exceptions import ClientError

# app = Flask(__name__, static_folder="static")

# # --- ADD THIS ROUTE TO SERVE index.html ---
# @app.route("/")
# def home():
#     return send_from_directory(app.static_folder, "index.html")


# S3_BUCKET = os.environ.get("S3_BUCKET")
# DDB_TABLE = os.environ.get("DDB_TABLE")
# SIGNED_URL_EXP = 3600  # 1 hour

# s3 = boto3.client("s3")
# dynamodb = boto3.resource("dynamodb")
# table = dynamodb.Table(DDB_TABLE)

# def generate_file_number():
#     return str(uuid.uuid4())

# @app.route("/upload", methods=["POST"])
# def upload():
#     if "file" not in request.files:
#         return jsonify({"error": "No file provided"}), 400
#     file = request.files["file"]

#     file_number = generate_file_number()
#     filename = file.filename
#     s3_key = f"uploads/{file_number}/{filename}"

#     try:
#         s3.upload_fileobj(file, S3_BUCKET, s3_key, ExtraArgs={"ServerSideEncryption": "AES256"})

#         metadata = {
#             "file_number": file_number,
#             "s3_key": s3_key,
#             "filename": filename,
#             "content_type": file.content_type or "application/octet-stream",
#             "uploaded_at": int(time.time())
#         }
#         table.put_item(Item=metadata)

#         return jsonify({"message": "Upload successful", "file_number": file_number}), 201

#     except ClientError as e:
#         return jsonify({"error": str(e)}), 500

# @app.route("/download/<file_number>", methods=["GET"])
# def download(file_number):
#     try:
#         response = table.get_item(Key={"file_number": file_number})
#         item = response.get("Item")

#         if not item:
#             return jsonify({"error": "File not found"}), 404

#         s3_key = item["s3_key"]
#         url = s3.generate_presigned_url(
#             "get_object",
#             Params={"Bucket": S3_BUCKET, "Key": s3_key},
#             ExpiresIn=SIGNED_URL_EXP
#         )

#         return jsonify({
#             "download_url": url,
#             "filename": item["filename"]
#         })

#     except ClientError as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)
