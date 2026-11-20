# ClearWave on Azure: one Container App (API + built frontend, scales to zero), a private Blob container
# for uploaded samples, and a database on the Postgres server LockedIn already runs.

resource "azurerm_resource_group" "main" {
  name     = "${var.name}-rg"
  location = var.location
}

# Storage account names are global across Azure, so they get a short random suffix.
resource "random_string" "suffix" {
  length  = 5
  special = false
  upper   = false
}

# ---- Database: a separate database and login on LockedIn's server ----

data "azurerm_postgresql_flexible_server" "shared" {
  name                = var.db_server_name
  resource_group_name = var.db_server_resource_group
}

resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = "clearwave"
  server_id = data.azurerm_postgresql_flexible_server.shared.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Password for ClearWave's own login. Letters and digits only, so it fits in a URL and in SQL as-is.
resource "random_password" "db" {
  length  = 32
  special = false
}

locals {
  db_user = "clearwave"
  database_url = format(
    "postgresql+asyncpg://%s:%s@%s:5432/%s?ssl=require",
    local.db_user,
    random_password.db.result,
    data.azurerm_postgresql_flexible_server.shared.fqdn,
    azurerm_postgresql_flexible_server_database.app.name,
  )
}

# ---- Storage: private container for uploaded samples ----

resource "azurerm_storage_account" "audio" {
  name                            = "${var.name}${random_string.suffix.result}"
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false
}

resource "azurerm_storage_container" "samples" {
  name                  = "samples"
  storage_account_id    = azurerm_storage_account.audio.id
  container_access_type = "private"
}

# ---- App ----

resource "azurerm_log_analytics_workspace" "logs" {
  name                = "${var.name}-logs"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "main" {
  name                       = "${var.name}-env"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id

  # Azure now creates every environment with this pay-per-use profile, so declare it rather than fight it.
  workload_profile {
    name                  = "Consumption"
    workload_profile_type = "Consumption"
  }
}

locals {
  app_name = var.name
  # The app's public address is its name plus the environment's domain, known before the app exists.
  app_url = "https://${local.app_name}.${azurerm_container_app_environment.main.default_domain}"
  # Whether a key was given is not secret, even though the key is.
  use_resend    = nonsensitive(var.resend_api_key != "")
  private_image = nonsensitive(var.ghcr_token != "")
}

resource "azurerm_container_app" "app" {
  name                         = local.app_name
  resource_group_name          = azurerm_resource_group.main.name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"
  workload_profile_name        = "Consumption"

  secret {
    name  = "database-url"
    value = local.database_url
  }
  secret {
    name  = "storage-connection-string"
    value = azurerm_storage_account.audio.primary_connection_string
  }
  secret {
    name  = "acr-access-key"
    value = var.acr_access_key
  }
  secret {
    name  = "acr-access-secret"
    value = var.acr_access_secret
  }
  dynamic "secret" {
    for_each = local.use_resend ? [1] : []
    content {
      name  = "resend-api-key"
      value = var.resend_api_key
    }
  }
  dynamic "secret" {
    for_each = local.private_image ? [1] : []
    content {
      name  = "ghcr-token"
      value = var.ghcr_token
    }
  }

  dynamic "registry" {
    for_each = local.private_image ? [1] : []
    content {
      server               = "ghcr.io"
      username             = "krishatgit"
      password_secret_name = "ghcr-token"
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "http"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    # Zero replicas while idle, so it costs nothing when nobody is using it.
    min_replicas = 0
    max_replicas = 1

    container {
      name   = "app"
      image  = var.image
      cpu    = 0.25
      memory = "0.5Gi"

      # Secrets: the value lives in the secret above; the container only sees it as an env var.
      env {
        name        = "CLEARWAVE_DATABASE_URL"
        secret_name = "database-url"
      }
      env {
        name        = "CLEARWAVE_STORAGE_CONNECTION_STRING"
        secret_name = "storage-connection-string"
      }
      env {
        name        = "CLEARWAVE_ACR_ACCESS_KEY"
        secret_name = "acr-access-key"
      }
      env {
        name        = "CLEARWAVE_ACR_ACCESS_SECRET"
        secret_name = "acr-access-secret"
      }
      dynamic "env" {
        for_each = local.use_resend ? [1] : []
        content {
          name        = "CLEARWAVE_RESEND_API_KEY"
          secret_name = "resend-api-key"
        }
      }

      # Plain settings.
      env {
        name  = "CLEARWAVE_FRONTEND_ORIGIN"
        value = local.app_url
      }
      env {
        name  = "CLEARWAVE_COOKIE_SECURE"
        value = "true"
      }
      env {
        name  = "CLEARWAVE_MATCHER"
        value = "acrcloud"
      }
      env {
        name  = "CLEARWAVE_ACR_HOST"
        value = var.acr_host
      }
      env {
        name  = "CLEARWAVE_MAILER"
        value = local.use_resend ? "resend" : "console"
      }
      env {
        name  = "CLEARWAVE_MAIL_FROM"
        value = var.mail_from
      }
    }

    http_scale_rule {
      name                = "http"
      concurrent_requests = "50"
    }
  }

  lifecycle {
    # GitHub Actions deploys each new image; Terraform owns everything else.
    ignore_changes = [template[0].container[0].image]
  }
}
