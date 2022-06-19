resource "google_cloud_run_service" "cloud_run_purchase_management_pwa" {
  name     = "purchase-management-pwa-server"
  location = var.region

  template {
    spec {
      containers {
        image = "asia.gcr.io/${var.project}/r24-pwa-server"
      }
    }
  }
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = var.r24_pwa_members
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.cloud_run_purchase_management_pwa.location
  project     = google_cloud_run_service.cloud_run_purchase_management_pwa.project
  service     = google_cloud_run_service.cloud_run_purchase_management_pwa.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
