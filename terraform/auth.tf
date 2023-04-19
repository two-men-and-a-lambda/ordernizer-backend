module "aws_cognito_user_pool"{

  source  = "lgallard/cognito-user-pool/aws"
  version = "0.22.0"

  user_pool_name                                     = "ordernizer_auth_pool"
  alias_attributes                                   = ["email", "phone_number"]
  auto_verified_attributes                           = ["email"]
  sms_authentication_message                         = "Your username is {username} and temporary password is {####}."
  sms_verification_message                           = "This is the verification message {####}."
  lambda_config_verify_auth_challenge_response       = "arn:aws:lambda:us-east-1:891210098252:function:hello-world"
  password_policy_require_lowercase                  = false
  password_policy_minimum_length                     = 6
  user_pool_add_ons_advanced_security_mode           = "OFF"
  verification_message_template_default_email_option = "CONFIRM_WITH_CODE"


  # schemas
  schemas = [
    {
      attribute_data_type      = "Boolean"
      developer_only_attribute = false
      mutable                  = true
      name                     = "available"
      required                 = false
    },
  ]

  string_schemas = [
    {
      attribute_data_type      = "String"
      developer_only_attribute = false
      mutable                  = false
      name                     = "email"
      required                 = true

      string_attribute_constraints = {
        min_length = 7
        max_length = 150
      }
    },
  ]

  # user_pool_domain
  domain = "ordernizer-org"

  # client
  client_name                                 = "client0"
  client_allowed_oauth_flows_user_pool_client = false
  client_callback_urls                        = ["https://ordernizer.org/callback"]
  client_default_redirect_uri                 = "https://ordernizer.org/callback"
  client_read_attributes                      = ["email"]
  client_refresh_token_validity               = 30
  client_generate_secret                      = false


  # user_group
  user_group_name        = "ordernizer"
  user_group_description = "Staying Ordernized"
  

  # ressource server
  resource_server_identifier        = "https://ordernizer.org"
  resource_server_name              = "ordernizer"
  resource_server_scope_name        = "scope"
  resource_server_scope_description = "I have never setup auth before"

  # tags
  tags = merge({
    Name = "${var.name_prefix}-cognito-pool"
  }, var.tags)
}
