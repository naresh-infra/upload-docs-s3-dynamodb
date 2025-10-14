# S3 Bucket for document uploads
resource "aws_s3_bucket" "uploads-s3" {
  bucket = "${var.project}-s3-bucket"   # change name to something unique
  acl    = "private"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = {
    Project = "DocUploader"
    Env     = "Dev"
  }
}

# DynamoDB Table for metadata
resource "aws_dynamodb_table" "dynamodb" {
  name           = "${var.project}-dynamodb"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "file_number"

  attribute {
    name = "file_number"
    type = "S"
  }

  tags = {
    Project = "DocUploader"
    Env     = "Dev"
  }
}

# IAM Policy for S3 + DynamoDB
resource "aws_iam_policy" "doc_policy" {
  name   = "doc-upload-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.uploads-s3.arn}/*"
      },
      {
        Sid    = "DynamoDBAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem"
        ]
        Resource = aws_dynamodb_table.dynamodb.arn
      }
    ]
  })
}
