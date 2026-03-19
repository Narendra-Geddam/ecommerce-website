# SSL/HTTPS Setup for morecraze.in

## Step 1: Create ACM Certificate

```bash
cd terraform
terraform apply
```

Get the certificate ARN from output:
```
acm_certificate_arn = "arn:aws:acm:eu-north-1:593067253640:certificate/abc123..."
```

## Step 2: Validate Certificate Via Route 53

1. Go to: https://console.aws.amazon.com/acm/
2. Find certificate for `morecraze.in`
3. Click "Create records in Route 53"
4. AWS automatically creates DNS validation record
5. Wait 5-15 minutes for status to change to **ISSUED**

Check status:
```bash
aws acm describe-certificate --certificate-arn <ARN> --region eu-north-1 | grep Status
```

## Step 3: Update Helm Values

Edit `helm-chart/values.yaml` - update the certificate ARN:

```yaml
domain:
  name: morecraze.in
  certificateArn: "arn:aws:acm:eu-north-1:593067253640:certificate/abc123..."
```

Also update `helm-chart/values-prod.yaml` with same certificate ARN.

## Step 4: Deploy with Helm

```bash
helm upgrade ecommerce ./helm-chart \
  -n prod-ecommerce \
  -f helm-chart/values.yaml \
  -f helm-chart/values-prod.yaml
```

Ingress will automatically update with HTTPS listener.

Wait 5-10 minutes for ALB to update.

## Step 5: Setup Route 53 DNS (Point Domain to ALB)

Get ALB DNS name:
```bash
kubectl get ingress -n prod-ecommerce -o wide
# Look for ADDRESS column
```

In Route 53, create **ALIAS record**:
- **Name:** morecraze.in
- **Type:** A
- **Alias Target:** Your ALB DNS name (from above)

Or via AWS CLI:
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "morecraze.in",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z487MZXP0Z34Z",
          "DNSName": "k8s-xxx.eu-north-1.elb.amazonaws.com",
          "EvaluateTargetHealth": false
        }
      }
    }]
  }' --region eu-north-1
```

## Step 6: Test

Wait 60 seconds for DNS to propagate, then:

```bash
# Test HTTPS (should work)
curl -I https://morecraze.in/

# Test HTTP redirect (should redirect to HTTPS)
curl -I http://morecraze.in/

# Check certificate in browser
# Visit https://morecraze.in - should show 🔒 lock icon
```

## Done! ✅

Your app is now running on **https://morecraze.in** with SSL/HTTPS encryption.

### What Happens Automatically
- Certificate auto-renews before expiration (AWS handles it)
- HTTP requests automatically redirect to HTTPS
- All traffic is encrypted

### If Something Doesn't Work

**HTTPS returns 502?**
- Wait 5-10 more minutes for ALB to update

**Certificate not validating?**
- Check Route 53 has DNS validation record
- Verify domain is in same AWS account

**DNS not resolving?**
- Verify Route 53 ALIAS record created
- Try: `nslookup morecraze.in`
