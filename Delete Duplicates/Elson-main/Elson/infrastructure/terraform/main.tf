# infrastructure/terraform/main.tf

terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }

  # Store state locally for test environment
  backend "local" {
    path = "terraform.tfstate"
  }
}

# Configure the Kubernetes provider to use local cluster
provider "kubernetes" {
  config_path    = "~/.kube/config"  # Default path for kubectl config
  config_context = "minikube"        # Use "kind-kind" if using kind cluster
}

provider "helm" {
  kubernetes {
    config_path    = "~/.kube/config"
    config_context = "minikube"
  }
}

# Create namespace for our application
resource "kubernetes_namespace" "elson" {
  metadata {
    name = "elson-test"
  }
}

# Deploy Redis
resource "kubernetes_deployment" "redis" {
  metadata {
    name      = "redis"
    namespace = kubernetes_namespace.elson.metadata[0].name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "redis"
      }
    }
    template {
      metadata {
        labels = {
          app = "redis"
        }
      }
      spec {
        container {
          name  = "redis"
          image = "redis:alpine"
          port {
            container_port = 6379
          }
        }
      }
    }
  }
}

# Redis Service
resource "kubernetes_service" "redis" {
  metadata {
    name      = "redis"
    namespace = kubernetes_namespace.elson.metadata[0].name
  }
  spec {
    selector = {
      app = "redis"
    }
    port {
      port        = 6379
      target_port = 6379
    }
  }
}

# Local PostgreSQL database
resource "kubernetes_deployment" "postgres" {
  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace.elson.metadata[0].name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "postgres"
      }
    }
    template {
      metadata {
        labels = {
          app = "postgres"
        }
      }
      spec {
        container {
          name  = "postgres"
          image = "postgres:14-alpine"
          env {
            name  = "POSTGRES_DB"
            value = "elson_db"
          }
          env {
            name  = "POSTGRES_USER"
            value = "postgres"
          }
          env {
            name  = "POSTGRES_PASSWORD"
            value = "postgres_local"  # Only for local testing
          }
          port {
            container_port = 5432
          }
          volume_mount {
            name       = "postgres-data"
            mount_path = "/var/lib/postgresql/data"
          }
        }
        volume {
          name = "postgres-data"
          empty_dir {} # Using empty_dir for local testing. Use PVC in production
        }
      }
    }
  }
}

# PostgreSQL Service
resource "kubernetes_service" "postgres" {
  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace.elson.metadata[0].name
  }
  spec {
    selector = {
      app = "postgres"
    }
    port {
      port        = 5432
      target_port = 5432
    }
  }
}

# Variables file reference
variable "local_k8s_config" {
  description = "Path to local Kubernetes config file"
  type        = string
  default     = "~/.kube/config"
}