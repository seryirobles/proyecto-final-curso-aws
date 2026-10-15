terraform {
  backend "s3" {
    profile      = "commitacademy-srobles"
    bucket       = "lab-terraform-srobles-313095875714-eu-west-1-an"
    key          = "terraform-lab/terraform.tfstate"
    region       = var.aws_region
    encrypt      = true
    use_lockfile = true
  }
}
provider "aws" {
  region  = var.aws_region
  profile = "commitacademy-srobles"
}
provider "aws" {
  alias   = "bedrock"
  region  = "eu-west-1"
  profile = "personal-srobles"
}