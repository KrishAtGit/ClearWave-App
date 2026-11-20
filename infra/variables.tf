variable "subscription_id" {
  description = "Azure subscription to deploy into (az account show --query id -o tsv)."
  type        = string
}

variable "name" {
  description = "Prefix for every resource name."
  type        = string
  default     = "clearwave"
}

variable "location" {
  description = "Azure region. Must be one the student subscription allows."
  type        = string
  default     = "australiaeast"
}

variable "image" {
  description = "Image for the first deploy. After that, GitHub Actions rolls out each new image."
  type        = string
  default     = "ghcr.io/krishatgit/clearwave:latest"
}

variable "github_repo" {
  description = "The repo allowed to deploy from main, as GitHub's OIDC tokens name it: owner@id/repo@id."
  type        = string
  default     = "KrishAtGit@193048311/ClearWave-App@1444333248"
}

# ---- The shared Postgres server (created by LockedIn's Terraform) ----

variable "db_server_name" {
  description = "Name of LockedIn's Postgres Flexible Server, e.g. lockedin-db-ab12c."
  type        = string
}

variable "db_server_resource_group" {
  description = "Resource group that holds that server."
  type        = string
  default     = "lockedin-rg"
}

# ---- Secrets: set in terraform.tfvars, never in git ----

variable "acr_host" {
  description = "ACRCloud project host, e.g. identify-ap-southeast-1.acrcloud.com."
  type        = string
}

variable "acr_access_key" {
  type      = string
  sensitive = true
}

variable "acr_access_secret" {
  type      = string
  sensitive = true
}

variable "resend_api_key" {
  description = "Leave empty to log sign-in links instead of emailing them."
  type        = string
  default     = ""
  sensitive   = true
}

variable "mail_from" {
  type    = string
  default = "ClearWave <onboarding@resend.dev>"
}

variable "ghcr_token" {
  description = "GitHub token with read:packages, if the image is private. Leave empty for a public image."
  type        = string
  default     = ""
  sensitive   = true
}
