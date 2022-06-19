terraform {
  required_version = ">= 0.12.24"

  backend "gcs" {
    bucket = "PROJECT-terraform"
    credentials = "terraform.json"
  }
}
