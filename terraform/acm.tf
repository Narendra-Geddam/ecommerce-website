# ACM Certificate for SSL/HTTPS

resource "aws_acm_certificate" "ecommerce_domain" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  tags = merge(
    var.tags,
    {
      Name = "ecommerce-certificate"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

# Note: For DNS validation in Route 53, you need to create the validation records manually
# or use aws_acm_certificate_validation with Route 53 zone data
# 
# For now, validate manually in AWS Console:
# 1. Go to ACM console
# 2. Click on your certificate
# 3. Follow the DNS validation steps in Route 53
#
# To automate validation (requires Route 53 zone in Terraform):
# resource "aws_route53_record" "acm_validation" {
#   for_each = {
#     for dvo in aws_acm_certificate.ecommerce_domain.domain_validation_options : dvo.domain => {
#       name   = dvo.resource_record_name
#       record = dvo.resource_record_value
#       type   = dvo.resource_record_type
#     }
#   }
#   
#   allow_overwrite = true
#   name            = each.value.name
#   records         = [each.value.record]
#   ttl             = 60
#   type            = each.value.type
#   zone_id         = var.route53_zone_id  # Must be provided as variable
# }
#
# resource "aws_acm_certificate_validation" "ecommerce_domain" {
#   certificate_arn           = aws_acm_certificate.ecommerce_domain.arn
#   timeouts {
#     create = "5m"
#   }
#   depends_on = [aws_route53_record.acm_validation]
# }
