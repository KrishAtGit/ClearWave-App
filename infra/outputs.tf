output "app_url" {
  description = "The live site."
  value       = local.app_url
}

output "resource_group" {
  value = azurerm_resource_group.main.name
}

output "container_app" {
  value = azurerm_container_app.app.name
}

# Not secrets: they name who may deploy, and only GitHub's signed tokens can use them.
output "github_variables" {
  description = "Repository variables for the deploy workflow."
  value = {
    AZURE_CLIENT_ID       = azuread_application.github.client_id
    AZURE_TENANT_ID       = data.azuread_client_config.current.tenant_id
    AZURE_SUBSCRIPTION_ID = var.subscription_id
  }
}

# Terraform can't create Postgres logins, so this is run once with psql as the server's admin.
# It gives ClearWave its own login that owns only the clearwave database, and stops that login
# from connecting to LockedIn's database.
output "db_setup_sql" {
  sensitive = true
  value     = <<-EOT
    CREATE ROLE ${local.db_user} LOGIN PASSWORD '${random_password.db.result}';
    GRANT ${local.db_user} TO ${data.azurerm_postgresql_flexible_server.shared.administrator_login};
    ALTER DATABASE ${azurerm_postgresql_flexible_server_database.app.name} OWNER TO ${local.db_user};
    REVOKE ALL ON DATABASE ${azurerm_postgresql_flexible_server_database.app.name} FROM PUBLIC;
    GRANT CONNECT ON DATABASE lockedin TO ${data.azurerm_postgresql_flexible_server.shared.administrator_login};
    REVOKE CONNECT ON DATABASE lockedin FROM PUBLIC;
  EOT
}
