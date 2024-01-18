# Job listing scrapper and auto-mailer
<a href="https://github.com/sienlonglim/jobs_automailer"><img alt="Static Badge" src="https://img.shields.io/badge/github-black?style=flat-square&logo=github"></a> <img alt="GitHub commit activity (branch)" src="https://img.shields.io/github/commit-activity/t/sienlonglim/jobs_automailer"> [![scheduled run main.py](https://github.com/sienlonglim/jobs_retriever_automailer/actions/workflows/actions.yaml/badge.svg)](https://github.com/sienlonglim/jobs_retriever_automailer/actions/workflows/actions.yaml)

This project involves automation in retrieving job listings from LinkedIn and mailing. Areas include:
- Web scrapping with bs4 and Selenium webdriver
- Pandas Dataframe wrangling
- MIME emailing

## Upcoming works:
- TBD

### 20230118 Mail log file and remove excels from repo
- Modified code so that no sheets are stored in the repo, to protect LinkedIn data
- Sheets will be mailed together with log file as the content
- Owner will need to run a script to manual merge the sheets

### 20231231 Added mailer with attachments:
- Completed MIMEText mailing
- An email will be sent after every run, containing the log file and latest main file

### 20231228 Selenium POC:
- Completed use of Selenium to deal with infinite scrolling and button clicking to get full number of jobs.
- Also incorporated retries when encoutering authentication walls.
- Renamed repo

### 20231225 Improved joblist retriever:
- Tried to sort jobids to identify latest, circumvent repeating jobs, but still only getting 1/10 of what is really available
- Added github workflow on schedule

### 20231223 MVP1:
- First viable product for joblist scrapper done
- Added simple logger
- Working SMTP server
- Auto-mailer not intergrated as there are no emails to obtain from linkedin for now
