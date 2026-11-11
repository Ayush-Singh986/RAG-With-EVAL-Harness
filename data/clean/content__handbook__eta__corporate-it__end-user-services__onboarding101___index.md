## Welcome To GitLab

Congratulations on joining GitLab! This page is dedicated to the IT onboarding experience, here at GitLab we use many applications and the latest hardware to enable you to complete your work to the best of your ability! While it may seem a little bit overwhelming at the start, we are here to make the process as easy as possible!

> **IMPORTANT**: You will not have access to your work Mac until your start date. On your start date, please follow this guide.

## Table of Contents

1. [Activate Your Okta Account](#activate-your-okta-account)
1. Set up your computer:
   - [Mac Setup](#mac-setup)
   - [Linux Setup](#linux-setup)
1. [Set Up Okta Verify on Mac](#set-up-okta-verify-on-mac)
1. [Google Account Setup](#google-account-setup)
1. [Access GitLab Email and GitLab.com](#access-gitlab-email-and-gitlabcom)

## Activate Your Okta Account

You will receive an Okta activation email in your personal email. This is the first step to gaining access to GitLab's systems.

1. On a mobile device, check your personal email for an Okta activation email.
1. Click the link in the email to set your password and configure Okta Verify on your mobile device.
1. After setting up your account, your browser will redirect to the Okta dashboard.

> **IMPORTANT**: Either Okta Verify or an enrolled FIDO2 key (like a YubiKey) is required to set up your GitLab-managed Mac. Make sure either is set up during your Okta account onboarding.

## Mac Setup

> **IMPORTANT**: If the **Device Management** screen does not show up during setup, please follow the [manual enrollment](#manual-mac-setup) steps to enroll your device in MDM.

Keep your Mac plugged in and connected to a stable internet connection until setup is complete.

1. Power on your GitLab-managed Mac.
1. Select your country or region.\
   ![Select Your Country or Region screen with United States selected and a Continue button](/images/eta/corporate-it/end-user-services/onboarding101/mac-setup-country.png)
1. On the **Transfer Your Data to This Mac** screen, select **Set up as new**.\
   ![Transfer Your Data to This Mac screen with Set up as new selected](/images/eta/corporate-it/end-user-services/onboarding101/mac-setup-transfer-data.png)
1. Choose accessibility options, or click **Not Now**.\
   ![Accessibility screen with Vision, Motor, Hearing, and Cognitive options and a Not Now button](/images/eta/corporate-it/end-user-services/onboarding101/mac-setup-accessibility.png)
1. Select your Wi-Fi network.\
   ![Select Your Wi-Fi Network screen with a list of networks and a Continue button](/images/eta/corporate-it/end-user-services/onboarding101/mac-setup-wifi.png)
1. On the **Device Management** screen, wait for the enrollment profile to load, then click **Enroll**.\
   ![Device Management screen showing the Mac is owned by GitLab Inc. with an Enroll button](/images/eta/corporate-it/end-user-services/onboarding101/mac-setup-device-management.png)
1. Sign in to Okta when prompted. Use the password you created during Okta account activation.\
   ![Okta sign-in window titled Connecting to Fleet with a Username field and a Next button](/images/eta/corporate-it/end-user-services/onboarding101/mac-setup-okta-sign-in.png)
1. On the **Verify it's you with a security method** screen, select either **Get a push notification** (Okta Verify) or **Security Key or Biometric Authenticator** (for example, a YubiKey), then complete the verification.\
   ![Okta Verify it's you with a security method screen with Get a push notification and Security Key or Biometric Authenticator options](/images/eta/corporate-it/end-user-services/onboarding101/mac-setup-okta-verify.png)
1. The Mac enrolls in MDM and installs required settings. When that finishes, setup moves on to account creation.
1. Set up your computer account. Your full name and username are automatically prefilled. Create a password for your local Mac account that meets the [GitLab Password Standards](/handbook/security/policies_and_standards/password-standard/#password-requirements). You can use the same password as your Okta password.\
   ![Create a Mac Account screen with prefilled name and username and the password requirements, including at least 12 characters](/images/eta/corporate-it/end-user-services/onboarding101/mac-setup-account.png)
1. Choose your look: **Light**, **Dark**, or **Auto**.
1. Enable Location Services.\
   ![Enable Location Services screen with Enable Location Services on this Mac checked](/images/eta/corporate-it/end-user-services/onboarding101/mac-setup-location.png)
1. Set up Touch ID when prompted.\
   ![Touch ID screen with Set Up Touch ID Later and Continue buttons](/images/eta/corporate-it/end-user-services/onboarding101/mac-setup-touch-id.png)
1. Once you land at the desktop, GitLab's onboarding app (Exit0) opens the **Set up your Mac** window. Click **Start setup**, or wait 10 seconds for it to start on its own. It installs your core apps (Google Chrome, Slack, etc.), applies required settings, and verifies security compliance before use.
1. When the **You're all set!** screen appears, setup is finished. If FileVault full disk encryption is already enabled, your Mac is ready to use. If FileVault is not enabled, you will be prompted to restart the Mac in order to enable it. Click **Restart** or wait for the 60-second countdown, then log back in with your local Mac account password.

If setup stops or shows an error, email it-help@gitlab.com from your personal email address.

### Manual Mac Setup

Manual enrollment is only for Macs that cannot use automated enrollment, such as a Mac that was not purchased through GitLab's authorized vendors. Manually enrolling Macs should be a last resort and is not considered a standard process. If you live in a country where GitLab is not able to ship a Mac to you, email it-help@gitlab.com to confirm it's the right option.

Before you begin, make sure your Mac is running macOS 15 or later and you can sign in to it with an administrator account.

1. Email it-help@gitlab.com and ask for access to manual Mac enrollment. IT adds you to the Okta group for manual enrollment and lets you know when it's done.
1. On your Mac, open Safari. Google Chrome isn't installed yet.
1. Sign in to the [Okta dashboard](https://gitlab.okta.com).
1. Click the **Fleet macOS Manual Enrollment** tile. It opens the Fleet enrollment page.

1. Sign in to Okta again when prompted.
1. On the **How to turn on MDM on your Mac** page, make sure **Company-owned** is selected, then click **Download**. If Safari asks to allow downloads, click **Allow**. When you see **Profile Downloaded**, click **OK**.
1. Choose **Apple menu** > **System Settings**, then select **General** > **Device Management**. Double-click the **GitLab enrollment** profile.\
   ![Device Management settings showing the downloaded GitLab enrollment profile with Profile not installed. Double-click to review.](/images/eta/corporate-it/end-user-services/onboarding101/mac-manual-device-management.png)
1. Click **Install...**, then click **Install** to confirm.\
   ![Confirmation asking Are you sure you want to install profile GitLab enrollment, with Install, Show Details, and Cancel buttons](/images/eta/corporate-it/end-user-services/onboarding101/mac-manual-install-profile.png)
1. Wait a few minutes for GitLab's onboarding app to open the **Set up your Mac** window. Keep your Mac plugged in and connected to the internet.

From there, setup is the same as automated enrollment. Continue with the **Set up your Mac** and **You're all set!** steps in [Mac Setup](#mac-setup), then [set up Okta Verify](#set-up-okta-verify-on-mac).

If enrollment fails, email it-help@gitlab.com.

## Linux Setup

Follow the [Linux Desktop OS Setup Guide](/handbook/security/corporate/systems/linux/setup/) to set up and enroll your Linux laptop.

## Set Up Okta Verify on Mac

Okta Verify is installed automatically during Mac setup and is the primary way to authenticate to apps used at GitLab. The easiest way to set it up is to import the Okta Verify account from your mobile device.

Before you begin:

- Keep your mobile device near your Mac, with Bluetooth turned on for both.
- Open Okta Verify on your mobile device and make sure your GitLab account shows no warnings or errors.

1. Open **Okta Verify** on your Mac.
1. On the **Welcome to Okta Verify** window, click **Import account**.\
   ![Welcome to Okta Verify window with Get started and Import account buttons](/images/eta/corporate-it/end-user-services/onboarding101/mac-okta-verify-welcome.png)
1. On your mobile device, open Okta Verify, tap your GitLab account, tap **Export account**, then tap **Allow**. Your mobile device shows a QR code and an 8-character code.
1. On your Mac, enter the 8-character code and click **Continue**. Okta ends the Bluetooth connection after 5 minutes, so start again if the code expires.\
   ![Okta Verify Enter code screen with eight boxes for the code from the other device and a Continue button](/images/eta/corporate-it/end-user-services/onboarding101/mac-okta-verify-code.png)
1. Your Mac shows a 6-digit PIN. Enter it in Okta Verify on your mobile device. Never enter a PIN that someone else gives you.
1. Enable Touch ID when prompted.

If you don't have Okta Verify on a mobile device, click **Get started** instead of **Import account**. Make sure the sign-in URL is `gitlab.okta.com`, click **Next**, and sign in with your Okta username, password, and security method.

## Google Account Setup

1. Open Google Chrome. On the **Sign in to Chrome** window, click **Sign In**.\
   ![Sign in to Chrome window with Stay Signed Out and Sign In buttons](/images/eta/corporate-it/end-user-services/onboarding101/chrome-sign-in.png)
1. Enter your GitLab email address and click **Next**.\
   ![Sign in to Chrome window with a GitLab email address entered and a Next button](/images/eta/corporate-it/end-user-services/onboarding101/chrome-sign-in-email.png)
1. Chrome opens the GitLab Okta sign-in. On the **Verify it's you with a security method** screen, select **Use Okta FastPass**. On Linux, select **Security Key or Biometric Authenticator** instead.\
   ![Okta Verify it's you with a security method screen with Use Okta FastPass, Password, and Security Key or Biometric Authenticator options](/images/eta/corporate-it/end-user-services/onboarding101/chrome-okta-fastpass.png)
1. The first time you sign in, Google shows the Google Workspace terms. Click **Agree**.
1. On the Google **Verify it's you** screen, check that your GitLab email address is shown and click **Continue**.\
   ![Google Verify it's you screen with a GitLab email address and a Continue button](/images/eta/corporate-it/end-user-services/onboarding101/chrome-google-verify.png)
1. On the **This profile will be managed** screen, click **Continue**.
1. If Chrome asks **What would you like to do with your existing profile data?**, select **Create a new profile for work without my existing data** and click **Confirm**.\
   ![Chrome screen asking what to do with existing profile data, with Create a new profile for work without my existing data selected and a Confirm button](/images/eta/corporate-it/end-user-services/onboarding101/chrome-profile-data.png)

## Access GitLab Email and GitLab.com

1. Access your GitLab email by clicking **Google Workspace Mail** from the Okta dashboard, or go to <https://mail.google.com>.
1. Check your GitLab email for an email titled "**Welcome to GitLab Onboarding, `yourname`!**".
1. Follow the instructions in the email to set up your GitLab.com account and access your Onboarding Issue.

### Congratulations

You have completed the initial setup process for your GitLab accounts and computer. If you encounter any issues, please contact IT via the Compass app in Slack (type "Compass" in the top search bar to find it) or it-help@gitlab.com.

## Need Help?

If you need help setting up your Mac, email it-help@gitlab.com. If you can't access your GitLab email yet, send it from your personal email address.
