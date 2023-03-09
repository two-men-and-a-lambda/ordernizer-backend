#------------------------------------------------------------------------------
# Misc
#------------------------------------------------------------------------------
variable "name_prefix" {
  description = "Name prefix for resources on AWS"
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

#------------------------------------------------------------------------------
# Log Bucket
#------------------------------------------------------------------------------
variable "log_bucket_versioning_status" {
  description = "(Optional) The versioning state of the bucket. Valid values: Enabled or Suspended. Defaults to Enabled"
  type        = string
  default     = "Enabled"
}

variable "log_bucket_versioning_mfa_delete" {
  description = "(Optional) Specifies whether MFA delete is enabled in the bucket versioning configuration. Valid values: Enabled or Disabled. Defaults to Disabled"
  type        = string
  default     = "Disabled"
}

variable "log_bucket_force_destroy" {
  description = "(Optional, Default:false) A boolean that indicates all objects (including any locked objects) should be deleted from the log bucket so that the bucket can be destroyed without error. These objects are not recoverable."
  type        = bool
  default     = false
}

variable "aws_accounts_with_read_view_log_bucket" {
  description = "List of AWS accounts with read permissions to log bucket"
  type        = list(string)
  default     = []
}

variable "zipFile" { 
  description = "Local Path for Zipped Lambda Code"
  type = string
  default = "lambda.zip"
  }

variable "bucketName" {
description = "Name for api code bucket"
  type = string
  default = "ordernizer-api-zip"


}

variable "runTime" {
  description = "Lambda Runtime for api function"
  type = string
  default = "python3.9"
}

variable "sourceFolder" {
  description = "Folder containing python source code for the lambda"
  type = string
  default = "src"
}

variable "sourceFile" {
  description = "Main Python File for entry"
  type = string
  default = "router"
}

variable "handler"  {
  description = "Handler function name"
  type = string
  default = "lambda_handler"
}

