# Job listing scrapper and auto-mailer
<a href="https://github.com/sienlonglim/jobs_automailer"><img alt="Static Badge" src="https://img.shields.io/badge/github-black?style=flat-square&logo=github"></a> <img alt="GitHub commit activity (branch)" src="https://img.shields.io/github/commit-activity/t/sienlonglim/jobs_automailer">

This project retrieves job listings from LinkedIn. Areas include:
- Web scrapping
- Pandas Dataframe wranling
- SMTP server and MIMEText mailing

## Upcoming works:
- Automate with github actions

### 20231225 Improved joblist retriever:
- Tried to sort jobids to identify latest, circumvent repeating jobs, but still only getting 1/10 of what is really available
- Need to use Selenium to deal with infinite scrolling to get full number of jobs.

### 20231223 MVP1:
- First viable product for joblist scrapper done
- Added simple logger
- Auto-mailer not intergrated as there are no emails to obtain from linkedin for now