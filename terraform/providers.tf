terraform {
  required_version = ">= 1.10, < 2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.8"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.9"
    }
  }

  backend "s3" {
    profile      = "commitacademy-srobles"
    bucket       = "lab-final-terraform-srobles-313095875714-eu-west-1-an"
    key          = "terraform-lab/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region  = local.region
  profile = var.aws_profile

  default_tags {
    tags = local.tags
  }
}

# The separate AWS account that has Bedrock model access (see bedrock.tf).
provider "aws" {
  alias   = "bedrock"
  region  = local.region
  profile = var.bedrock_aws_profile

  default_tags {
    tags = local.tags
  }
}
