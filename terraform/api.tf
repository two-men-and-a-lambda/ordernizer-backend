data "archive_file" "api_code_archive" {
  type        = "zip"
  source_dir = "${path.root}/../${var.sourceFolder}/"
  output_path = "${path.root}/../${var.zipFile}"
}

resource "aws_s3_bucket" "api_bucket" {
  bucket        = "${var.name_prefix}-api-bucket"
  force_destroy = true

  tags = merge({
    Name = "${var.name_prefix}-api-bucket"
  }, var.tags)
}

resource "aws_s3_bucket_public_access_block" "api_bucket" {
  bucket = aws_s3_bucket.api_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_object" "api_code_archive" {
  bucket = aws_s3_bucket.api_bucket.id
  key    = "${var.zipFile}"
  source = data.archive_file.api_code_archive.output_path
  etag   = filemd5(data.archive_file.api_code_archive.output_path)

  lifecycle {
    ignore_changes = [
      etag,
      version_id
    ]
  }

  tags = merge({
    Name = "${var.name_prefix}-archive"
  }, var.tags)
}

resource "aws_s3_bucket" "database_bucket" {
  bucket        = "${var.name_prefix}-database-bucket"
  force_destroy = true

  tags = merge({
    Name = "${var.name_prefix}-database-bucket"
  }, var.tags)
}

resource "aws_s3_bucket_versioning" "database_bucket" {
  bucket = aws_s3_bucket.database_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "database_bucket" {
  bucket = aws_s3_bucket.database_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_lambda_function" "api_lambda" {
  function_name    = "${var.name_prefix}-api"
  role             = aws_iam_role.api_lambda_role.arn
  s3_bucket        = aws_s3_bucket.api_bucket.id
  s3_key           = aws_s3_bucket_object.api_code_archive.key
  source_code_hash = data.archive_file.api_code_archive.output_base64sha256
  architectures    = ["arm64"]
  runtime          = "${var.runTime}"
  handler          = "${var.sourceFile}.${var.handler}"
  memory_size      = 512
  publish          = true
  timeout = 20
  layers = [
    "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python39-Arm64:4"
    ]

  lifecycle {
    ignore_changes = [
      last_modified,
      source_code_hash,
      version,
      environment
    ]
  }

  tags = merge({
    Name = "${var.name_prefix}-api"
  }, var.tags)
}

resource "aws_lambda_alias" "api_lambda_alias" {
  name             = "production"
  function_name    = aws_lambda_function.api_lambda.arn
  function_version = "$LATEST"

  lifecycle {
    ignore_changes = [
      function_version
    ]
  }
}

resource "aws_cloudwatch_log_group" "api_lambda_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.api_lambda.function_name}"
  retention_in_days = 14
  tags = merge({
    Name = "${var.name_prefix}-logs"
  }, var.tags)
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.name_prefix}-lambda-role-policy"
  role = aws_iam_role.api_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "s3:*"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "api_lambda_role" {
  name = "${var.name_prefix}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Sid    = ""
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
  tags = merge({
    Name = "${var.name_prefix}-lambda-role"
  }, var.tags)
}

resource "aws_apigatewayv2_api" "api_gateway" {
  name          = "${var.name_prefix}-api-gateway"
  protocol_type = "HTTP"
  tags = merge({
    Name = "${var.name_prefix}-gateway"
  }, var.tags)
}

resource "aws_apigatewayv2_stage" "api_gateway_default_stage" {
  api_id      = aws_apigatewayv2_api.api_gateway.id
  name        = "$default"
  auto_deploy = true
  tags = merge({
    Name = "${var.name_prefix}-gateway-stage"
  }, var.tags)

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_log_group.arn

    format = jsonencode({
      requestId               = "$context.requestId"
      sourceIp                = "$context.identity.sourceIp"
      requestTime             = "$context.requestTime"
      protocol                = "$context.protocol"
      httpMethod              = "$context.httpMethod"
      status                  = "$context.status"
      responseLatency         = "$context.responseLatency"
      path                    = "$context.path"
      integrationErrorMessage = "$context.integrationErrorMessage"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_gateway_log_group" {
  name              = "/aws/api_gateway_log_group/${aws_apigatewayv2_api.api_gateway.name}"
  retention_in_days = 14
  tags = merge({
    Name = "${var.name_prefix}-gateway-logs"
  }, var.tags)
}

resource "aws_apigatewayv2_integration" "api_gateway_integration" {
  api_id             = aws_apigatewayv2_api.api_gateway.id
  integration_uri    = "${aws_lambda_function.api_lambda.arn}:${aws_lambda_alias.api_lambda_alias.name}"
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  request_parameters = {}
  request_templates  = {}
}

resource "aws_apigatewayv2_route" "api_gateway_any_route" {
  api_id               = aws_apigatewayv2_api.api_gateway.id
  route_key            = "ANY /{proxy+}"
  target               = "integrations/${aws_apigatewayv2_integration.api_gateway_integration.id}"
  authorization_scopes = []
  request_models       = {}
}

resource "aws_lambda_permission" "api_gateway_lambda_permission" {
  principal     = "apigateway.amazonaws.com"
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_lambda.function_name
  qualifier     = aws_lambda_alias.api_lambda_alias.name
  source_arn    = "${aws_apigatewayv2_api.api_gateway.execution_arn}/*/*"
}



output "api_gateway_invoke_url" {
  description = "API gateway default stage invokation URL"
  value       = aws_apigatewayv2_stage.api_gateway_default_stage.invoke_url
}
