0.9.2 [2025-05-24]
==================
- Fixed handling 504 http error from server
- Removed support for Python 3.7 and 3.8

0.9.1 [2024-10-27]
==================
- Improved error handling in Jira response

0.9.0 [2024-07-19]
==================
- Added support for marking tests with defects

0.8.11 [2024-03-27]
===================
- Improved errors handling

0.8.10 [2023-09-08]
===================
- Added default text for mandatory `summary` field if not provided by a user

0.8.9 [2023-07-11]
==================
- Fixed formatting issues with pytest captures

0.8.8 [2023-06-06]
==================
- Added option to capture pytest stdout and logs in Xray report

0.8.7 [2023-05-29]
==================
- Fixed sending multiple results while running with xdist

0.8.6 [2023-05-15]
==================
- Changed key ``ContentType`` to ``contentType`` in Xray report

0.8.5 [2023-03-13]
==================
- Added possibility to disable certificate verification in client secret authentication

0.8.4 [2023-02-09]
==================
- Fixed wrong finished date in the Xrey report

0.8.3 [2023-01-02]
==================
- Fixed using plugin with xdist
- Removed redundant Token authentication

0.8.2 [2022-08-25]
==================
- Added possibility to attach test evidence

0.8.1 [2022-08-05]
==================
- Added hook to modify XRAY results before publishing

0.8.0 [2022-05-23]
==================
- Added token authentication
- Changed CLI options
  - Basic authentication is default for both Jira DC and cloud
  - Changed option `--api-key` to `--api-key-auth`

0.7.1 [2022-05-11]
==================
- Improved printing error messages from a Jira server

0.7.0 [2022-03-09]
==================
- Allow optional duplication of ids
- Minor fixes to support the latest changes in Xray Cloud

0.6.0 [2022-02-26]
==================
- Added API Key Authentication
- Added possibility to use multiple jira ids in the marker

0.5.1 [2022-02-17]
==================
- Fixed endpoint for Jira Cloud

0.5.0 [2021-12-10]
==================
- Added support for test execution revision
- Added support for summary and description
- Added support for executions test environments and fix version

0.4.0 [2021-11-28]
==================
- Fixed missing statuses in XRAY report (errors, xfail, xpass)

0.3.0 [2021-10-13]
==================
- Added option to save test execution results to JSON file

0.2.1 [2021-10-11]
==================
- Bug fixes

0.2.0 [2021-09-22]
==================
- Added support for Xray Cloud

0.1.2 [2021-04-24]
==================
- Added SSL Verification

0.1.1 [2021-04-11]
==================
- Fixed handling http errors

0.1.0 [2021-02-12]
==================
- First release
