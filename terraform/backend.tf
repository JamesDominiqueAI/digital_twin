terraform {
  backend "s3" {
    bucket = "twin-terraform-state-285407029618"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}