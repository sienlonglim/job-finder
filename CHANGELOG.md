# Change Log

## [2.0.0] 2024-08-17 
### Changes
- Code refactor for cleaner repo.
- Updated config to be py file instead of yaml.
- Temporary removed output emailing, email contains only run info.
- To complete S3 integration to save json files to s3 instead.
- Removed all dead code

### Added
- job_finder package
- mailer.py
- CHANGELOG.md
- AmazonS3 package (WIP)

## [1.2.1] 2023-01-18 
### Changes:
- Modified code so that no sheets are stored in the repo, to protect LinkedIn data
- Sheets will be mailed together with log file as the content
- Owner will need to run a script to manual merge the sheets

## [1.2.0] 2023-12-31
### Changes:
- Completed MIMEText mailing
- An email will be sent after every run, containing the log file and latest main file

## [1.1.0] 2023-12-28
### Changes:
- Renamed repo
- Completed use of Selenium to deal with infinite scrolling and button clicking to get full number of jobs.
- Also incorporated retries when encountering authentication walls

## [1.0.1] 2023-12-25 (Improved joblist retriever):
- Tried to sort jobids to identify latest, circumvent repeating jobs, but still only getting 1/10 of what is really available
### Added
- github workflow on schedule

## [1.0.0] 2023-12-23 
MVP1:
- First viable product for joblist scrapper done
- Added simple logger
- Working SMTP server