================================================================================
        WEB APPLICATION DEPLOYMENT - HOMEWORK ASSIGNMENT
================================================================================

Student: Vivek Sarvagod
University: George Mason University - MS in Information Systems
Course: COMP 645
Date: February 2025

================================================================================
                           DEPLOYED URLS
================================================================================

S3 Static Website URL:
http://comp645-assignment-1-portfolio.s3-website-us-east-1.amazonaws.com/

EC2 Web Server URL:
http://ec2-44-211-236-165.compute-1.amazonaws.com/

================================================================================
                         PROJECT OVERVIEW
================================================================================

This project consists of a personal portfolio website with the following pages:
- Home Page (index.html): Welcome page with navigation to other sections
- Portfolio Page (portfolio.html): Professional resume with skills and experience
- Student Survey Page (survey.html): Survey form with validation
- Contact Page (contact.html): Contact form and information
- Error Page (error.html): Custom 404 error page

Technologies Used:
- HTML5
- CSS3 (Bootstrap 5.3.2)
- JavaScript (Vanilla JS)
- Bootstrap Icons
- Font Awesome Icons

================================================================================
                          FILE STRUCTURE
================================================================================

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

================================================================================
              PART 1: AWS S3 STATIC WEBSITE HOSTING
================================================================================

S3 CONFIGURATION USED:
----------------------
Bucket Name:    comp645-assignment-1-portfolio
Region:         US East (N. Virginia) us-east-1
Website URL:    http://comp645-assignment-1-portfolio.s3-website-us-east-1.amazonaws.com/

STEP-BY-STEP INSTRUCTIONS:
--------------------------

Step 1: Sign in to AWS Console
    1. Go to https://aws.amazon.com/console/
    2. Sign in with your AWS credentials
    3. Ensure you're in the US East (N. Virginia) region

Step 2: Create an S3 Bucket
    1. Search for "S3" in the AWS Console
    2. Click "Create bucket"
    3. Bucket name: comp645-assignment-1-portfolio
    4. Region: US East (N. Virginia) us-east-1
    5. Object Ownership: Select "ACLs enabled"
    6. Block Public Access: UNCHECK "Block all public access"
    7. Acknowledge the warning
    8. Click "Create bucket"

Step 3: Upload Website Files
    1. Click on the bucket name
    2. Click "Upload"
    3. Upload all HTML files, css/, js/, and images/ folders
    4. Click "Upload"

Step 4: Enable Static Website Hosting
    1. Go to "Properties" tab
    2. Scroll to "Static website hosting"
    3. Click "Edit"
    4. Enable static website hosting
    5. Index document: index.html
    6. Error document: error.html
    7. Click "Save changes"

Step 5: Set Bucket Policy
    1. Go to "Permissions" tab
    2. Click "Edit" under Bucket policy
    3. Paste the following policy:

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

    4. Click "Save changes"

Step 6: Verify Deployment
    Access: http://comp645-assignment-1-portfolio.s3-website-us-east-1.amazonaws.com/

================================================================================
              PART 2: AWS EC2 WEB SERVER DEPLOYMENT
================================================================================

EC2 CONFIGURATION USED:
-----------------------
Instance Name:    vstech-solutions-WebServer
AMI:              Amazon Linux 2023
Instance Type:    t2.micro (Free tier)
Key Pair:         vstech-solution
Security Group:   vstech-web-server-sg
Public IP:        44.211.236.165
Public DNS:       ec2-44-211-236-165.compute-1.amazonaws.com
Website URL:      http://ec2-44-211-236-165.compute-1.amazonaws.com/

STEP-BY-STEP INSTRUCTIONS:
--------------------------

Step 1: Launch an EC2 Instance
    1. Go to EC2 Dashboard
    2. Click "Launch instance"
    3. Name: vstech-solutions-WebServer
    4. AMI: Amazon Linux 2023 (Free tier)
    5. Instance type: t2.micro
    6. Key pair: Create new - vstech-solution (.pem)
    7. Security group: Create new - vstech-web-server-sg
       - SSH (22) from My IP
       - HTTP (80) from Anywhere
       - HTTPS (443) from Anywhere
    8. Click "Launch instance"

Step 2: Connect to EC2

    # Set key permissions
    chmod 400 vstech-solution.pem

    # Connect via SSH
    ssh -i "vstech-solution.pem" ec2-user@44.211.236.165

    # Or using full DNS
    ssh -i "vstech-solution.pem" ec2-user@ec2-44-211-236-165.compute-1.amazonaws.com

Step 3: Install Apache Web Server

    # Update system
    sudo yum update -y

    # Install Apache
    sudo yum install -y httpd

    # Start Apache
    sudo systemctl start httpd

    # Enable on boot
    sudo systemctl enable httpd

    # Verify status
    sudo systemctl status httpd

Step 4: Upload Website Files

    From local machine:
    -------------------
    scp -i "vstech-solution.pem" -r * ec2-user@ec2-44-211-236-165.compute-1.amazonaws.com:~/website/

    On EC2 instance:
    ----------------
    sudo cp -r ~/website/* /var/www/html/
    sudo chown -R apache:apache /var/www/html
    sudo chmod -R 755 /var/www/html
    sudo systemctl restart httpd

Step 5: Verify Deployment
    Access: http://ec2-44-211-236-165.compute-1.amazonaws.com/

================================================================================
                        SUMMARY OF URLS
================================================================================

+---------------------+----------------------------------------------------------+
| Deployment          | URL                                                      |
+---------------------+----------------------------------------------------------+
| S3 Static Website   | http://comp645-assignment-1-portfolio.s3-website-us-east-1.amazonaws.com/ |
| EC2 Web Server      | http://ec2-44-211-236-165.compute-1.amazonaws.com/       |
+---------------------+----------------------------------------------------------+

================================================================================
                        TROUBLESHOOTING
================================================================================

S3 ISSUES:
----------
403 Forbidden: Check bucket policy and public access settings
404 Not Found: Verify index.html exists and hosting is enabled

EC2 ISSUES:
-----------
SSH Permission Denied:
    - Use "ec2-user" not "c2-user"
    - Run: chmod 400 vstech-solution.pem

Website Not Loading:
    - Check: sudo systemctl status httpd
    - Restart: sudo systemctl restart httpd
    - Verify files: ls -la /var/www/html/

================================================================================
                     STOPPING RESOURCES
================================================================================

To avoid AWS charges when not in use:

STOP EC2:
    AWS Console > EC2 > Instances > Select instance > Instance State > Stop

DELETE S3:
    AWS Console > S3 > Select bucket > Empty > Delete

================================================================================
                     SUBMISSION CHECKLIST
================================================================================

[X] README file included
[X] All source files included (HTML, CSS, JS)
[X] Comments at top of each source file
[X] S3 URL working
[X] EC2 URL working
[X] All pages accessible and functional
[X] Survey form validation works
[X] Navigation between pages works

================================================================================
                     CONTACT INFORMATION
================================================================================

Student: Vivek Sarvagod
Course: COMP 645
University: George Mason University

================================================================================
            (c) 2025 Vivek Sarvagod - George Mason University
================================================================================
