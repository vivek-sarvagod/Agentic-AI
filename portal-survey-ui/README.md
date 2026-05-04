# Web Application Deployment - Homework Assignment
## Vivek Sarvagod
## George Mason University - MS in Information Systems
## Course: COMP 645
## Date: February 2025

---

## Deployed URLs

### S3 Static Website URL:
**http://comp645-assignment-1-portfolio.s3-website-us-east-1.amazonaws.com/**

### EC2 Web Server URL:
**http://ec2-44-211-236-165.compute-1.amazonaws.com/**

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [File Structure](#file-structure)
3. [Part 1: AWS S3 Static Website Hosting](#part-1-aws-s3-static-website-hosting)
4. [Part 2: AWS EC2 Web Server Deployment](#part-2-aws-ec2-web-server-deployment)
5. [Troubleshooting](#troubleshooting)

---

## Project Overview

This project consists of a personal portfolio website with the following pages:
- **Home Page (index.html)**: Welcome page with navigation to other sections
- **Portfolio Page (portfolio.html)**: Professional resume with skills, experience, and education
- **Student Survey Page (survey.html)**: Survey form for campus feedback with form validation
- **Contact Page (contact.html)**: Contact form and information
- **Error Page (error.html)**: Custom 404 error page

### Technologies Used:
- HTML5
- CSS3 (Bootstrap 5.3.2)
- JavaScript (Vanilla JS)
- Bootstrap Icons
- Font Awesome Icons

---

## File Structure

```
website/
├── index.html              # Home page
├── portfolio.html          # Portfolio/Resume page
├── survey.html             # Student Survey form
├── contact.html            # Contact page
├── error.html              # Custom 404 error page
├── css/
│   └── styles.css          # Shared stylesheet
├── js/
│   └── main.js             # Shared JavaScript functions
└── images/
    └── my-photo.jpeg       # Profile photo
```

---

## Part 1: AWS S3 Static Website Hosting

### S3 Configuration Used

| Setting | Value |
|---------|-------|
| **Bucket Name** | comp645-assignment-1-portfolio |
| **Region** | US East (N. Virginia) us-east-1 |
| **Website URL** | http://comp645-assignment-1-portfolio.s3-website-us-east-1.amazonaws.com/ |

### Step-by-Step Instructions

#### Step 1: Sign in to AWS Console
1. Go to https://aws.amazon.com/console/
2. Sign in with your AWS credentials
3. Ensure you're in the **US East (N. Virginia)** region

#### Step 2: Create an S3 Bucket
1. In the AWS Console, search for "S3" in the search bar
2. Click on "S3" to open the S3 Dashboard
3. Click the **"Create bucket"** button

4. **Configure Bucket Settings:**
   - **Bucket name**: `comp645-assignment-1-portfolio`
   - **AWS Region**: `US East (N. Virginia) us-east-1`

5. **Object Ownership:**
   - Select **"ACLs enabled"**
   - Select **"Bucket owner preferred"**

6. **Block Public Access settings:**
   - **UNCHECK** "Block all public access"
   - Check the acknowledgment box

7. Click **"Create bucket"**

#### Step 3: Upload Website Files
1. Click on the bucket name: `comp645-assignment-1-portfolio`
2. Click the **"Upload"** button
3. Upload the following files and folders:
   - index.html
   - portfolio.html
   - survey.html
   - contact.html
   - error.html
   - css/ folder
   - js/ folder
   - images/ folder
4. Click **"Upload"**

#### Step 4: Enable Static Website Hosting
1. Go to the **"Properties"** tab
2. Scroll down to **"Static website hosting"**
3. Click **"Edit"**
4. Configure:
   - **Static website hosting**: **Enable**
   - **Hosting type**: **Host a static website**
   - **Index document**: `index.html`
   - **Error document**: `error.html`
5. Click **"Save changes"**

#### Step 5: Set Bucket Policy for Public Access
1. Go to the **"Permissions"** tab
2. Scroll to **"Bucket policy"** and click **"Edit"**
3. Paste the following policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::comp645-assignment-1-portfolio/*"
        }
    ]
}
```

4. Click **"Save changes"**

#### Step 6: Verify S3 Deployment
Access the website at: **http://comp645-assignment-1-portfolio.s3-website-us-east-1.amazonaws.com/**

---

## Part 2: AWS EC2 Web Server Deployment

### EC2 Configuration Used

| Setting | Value |
|---------|-------|
| **Instance Name** | vstech-solutions-WebServer |
| **AMI** | Amazon Linux 2023 |
| **Instance Type** | t2.micro (Free tier) |
| **Key Pair** | vstech-solution |
| **Security Group** | vstech-web-server-sg |
| **Public IP** | 44.211.236.165 |
| **Public DNS** | ec2-44-211-236-165.compute-1.amazonaws.com |
| **Website URL** | http://ec2-44-211-236-165.compute-1.amazonaws.com/ |

### Step-by-Step Instructions

#### Step 1: Launch an EC2 Instance

1. In AWS Console, search for "EC2" and open EC2 Dashboard
2. Click **"Launch instance"**

3. **Configure Instance:**

   **Name and tags:**
   - Name: `vstech-solutions-WebServer`

   **Application and OS Images:**
   - Select **"Amazon Linux 2023 AMI"** (Free tier eligible)
   - Architecture: 64-bit (x86)

   **Instance type:**
   - Select **"t2.micro"** (Free tier eligible)

   **Key pair (login):**
   - Click **"Create new key pair"**
   - Key pair name: `vstech-solution`
   - Key pair type: RSA
   - Private key file format: `.pem`
   - Click **"Create key pair"**
   - **Save the downloaded vstech-solution.pem file securely**

   **Network settings:**
   - Click **"Edit"**
   - Auto-assign public IP: **Enable**
   
   **Firewall (Security groups):**
   - Select **"Create security group"**
   - Security group name: `vstech-web-server-sg`
   - Description: `Security group for VSTech web server`
   
   **Inbound Security Group Rules:**
   
   | Type | Protocol | Port | Source | Description |
   |------|----------|------|--------|-------------|
   | SSH | TCP | 22 | My IP | SSH access |
   | HTTP | TCP | 80 | 0.0.0.0/0 | Web traffic |
   | HTTPS | TCP | 443 | 0.0.0.0/0 | Secure web traffic |

4. Click **"Launch instance"**

#### Step 2: Connect to EC2 Instance

```bash
# Set correct permissions for the key file
chmod 400 vstech-solution.pem

# Connect to EC2
ssh -i "vstech-solution.pem" ec2-user@44.211.236.165
```

Or using the full DNS:
```bash
ssh -i "vstech-solution.pem" ec2-user@ec2-44-211-236-165.compute-1.amazonaws.com
```

#### Step 3: Install and Configure Apache Web Server

Once connected to EC2, run these commands:

```bash
# Update the system
sudo yum update -y

# Install Apache HTTP Server
sudo yum install -y httpd

# Start Apache
sudo systemctl start httpd

# Enable Apache to start on boot
sudo systemctl enable httpd

# Verify Apache is running
sudo systemctl status httpd
```

#### Step 4: Upload Website Files to EC2

**From your local machine (not EC2):**

```bash
# Navigate to your website folder
cd /path/to/website

# Copy all files to EC2
scp -i "vstech-solution.pem" -r * ec2-user@ec2-44-211-236-165.compute-1.amazonaws.com:~/website/
```

**Then on EC2, move files to web directory:**

```bash
# SSH into EC2
ssh -i "vstech-solution.pem" ec2-user@44.211.236.165

# Create website directory if needed
mkdir -p ~/website

# Move files to Apache web directory
sudo cp -r ~/website/* /var/www/html/

# Set correct ownership and permissions
sudo chown -R apache:apache /var/www/html
sudo chmod -R 755 /var/www/html

# Restart Apache
sudo systemctl restart httpd
```

#### Step 5: Verify EC2 Deployment
Access the website at: **http://ec2-44-211-236-165.compute-1.amazonaws.com/**

---

## Summary of Deployed URLs

| Deployment | URL |
|------------|-----|
| **S3 Static Website** | http://comp645-assignment-1-portfolio.s3-website-us-east-1.amazonaws.com/ |
| **EC2 Web Server** | http://ec2-44-211-236-165.compute-1.amazonaws.com/ |

---

## Troubleshooting

### S3 Issues

**Problem: 403 Forbidden Error**
- Verify bucket policy is correctly configured
- Ensure "Block all public access" is disabled
- Check that the bucket name in the policy matches exactly

**Problem: 404 Not Found**
- Verify index.html is in the root of the bucket
- Check static website hosting is enabled
- Ensure file names are correct (case-sensitive)

### EC2 Issues

**Problem: Cannot connect via SSH**
```bash
# Check key file permissions
chmod 400 vstech-solution.pem

# Verify correct username (ec2-user, not c2-user)
ssh -i "vstech-solution.pem" ec2-user@44.211.236.165
```

**Problem: Website not loading**
```bash
# Check Apache status
sudo systemctl status httpd

# Restart Apache
sudo systemctl restart httpd

# Check files are in place
ls -la /var/www/html/
```

**Problem: Permission denied when uploading**
```bash
# Upload to home directory first
scp -i "vstech-solution.pem" -r * ec2-user@44.211.236.165:~/website/

# Then SSH in and copy to /var/www/html
sudo cp -r ~/website/* /var/www/html/
```

---

## Important Notes

### Stopping Resources (to avoid charges)

**Stop EC2:**
```
AWS Console → EC2 → Instances → Select instance → Instance State → Stop
```

**Delete S3 Bucket:**
```
AWS Console → S3 → Select bucket → Empty → Delete
```

---

## Submission Checklist

- [x] README.md file included
- [x] All source files included (HTML, CSS, JS)
- [x] Comments at top of each source file
- [x] S3 URL working
- [x] EC2 URL working
- [x] All pages accessible and functional
- [x] Survey form validation works
- [x] Navigation between pages works

---

## Contact Information

**Student:** Vivek Sarvagod  
**Course:** COMP 645  
**University:** George Mason University

---

© 2025 Vivek Sarvagod - George Mason University
