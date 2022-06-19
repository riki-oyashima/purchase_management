provider "google" {
  credentials = file("terraform.json")
  project     = var.project
  region      = var.region
  zone        = var.zone
}
