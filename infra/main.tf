/**
 * ATOM Infrastructure as Code
 * Google Cloud Platform Terraform configuration
 * Provisions: Cloud Run, Firestore, Pub/Sub, IAM
 */

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "atom"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ============================================================================
# Service Account
# ============================================================================

resource "google_service_account" "atom_sa" {
  account_id   = "${var.app_name}-sa"
  display_name = "ATOM Service Account"
}

# Grant Firestore permissions
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.atom_sa.email}"
}

# Grant Pub/Sub permissions
resource "google_project_iam_member" "pubsub_editor" {
  project = var.project_id
  role    = "roles/pubsub.editor"
  member  = "serviceAccount:${google_service_account.atom_sa.email}"
}

# Grant Cloud Run permissions
resource "google_project_iam_member" "cloud_run" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.atom_sa.email}"
}

# Grant Logs permissions
resource "google_project_iam_member" "logs_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.atom_sa.email}"
}

# ============================================================================
# Firestore Database
# ============================================================================

resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# ============================================================================
# Pub/Sub Topic and Subscription
# ============================================================================

resource "google_pubsub_topic" "incident_logs" {
  name = "incident-logs"
}

resource "google_pubsub_subscription" "incident_logs_sub" {
  name  = "incident-logs-sub"
  topic = google_pubsub_topic.incident_logs.name

  ack_deadline_seconds = 60

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

# ============================================================================
# Cloud Run Service
# ============================================================================

# Build container image
resource "google_cloud_run_service" "atom_backend" {
  name     = var.app_name
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.atom_sa.email

      containers {
        image = "gcr.io/${var.project_id}/${var.app_name}:latest"

        # Environment variables
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "PUBSUB_TOPIC"
          value = google_pubsub_topic.incident_logs.name
        }

        env {
          name  = "PUBSUB_SUBSCRIPTION"
          value = google_pubsub_subscription.incident_logs_sub.name
        }

        env {
          name  = "FIRESTORE_COLLECTION"
          value = "incidents"
        }

        # Allow microphone access (if running on system with audio)
        ports {
          container_port = 8080
        }

        resources {
          limits = {
            cpu    = "2"
            memory = "4Gi"
          }
        }
      }

      timeout_seconds = 3600
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "autoscaling.knative.dev/minScale" = "1"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_firestore_database.database,
    google_pubsub_topic.incident_logs,
  ]
}

# Allow unauthenticated access (for demo)
resource "google_cloud_run_service_iam_member" "noauth" {
  service  = google_cloud_run_service.atom_backend.name
  location = google_cloud_run_service.atom_backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ============================================================================
# Outputs
# ============================================================================

output "cloud_run_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_service.atom_backend.status[0].url
}

output "service_account_email" {
  description = "Service account email"
  value       = google_service_account.atom_sa.email
}

output "firestore_database" {
  description = "Firestore database name"
  value       = google_firestore_database.database.name
}

output "pubsub_topic" {
  description = "Pub/Sub topic name"
  value       = google_pubsub_topic.incident_logs.name
}
