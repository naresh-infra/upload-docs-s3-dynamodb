terraform {
    required_providers {
      aws = {
        source = "hashicorp/aws"
        version = "~> 5.0"
      }
    }
}

provider "aws" {
    region = "ap-south-1"
}

terraform {
  backend "s3" {
    encrypt = false
    key = "path/path/terraform.tfstate"
    region = "ap-south-1"
    bucket = "upload-docs-s3-dynamodb-tfstate-bucket"
    
  }
}