# paper-downloader
paper downloader with accounts.

Thanks to [ESWZY's webvpn-dlut]("https://github.com/ESWZY/webvpn-dlut"). WebVPN encrypt.

Note that `informs-pubs-online` may ban your account.

Science-Hub is now supported! With download checkpoint.[Beta]

# Usage
```python
from paper_downloader.agent.webvpn import WebVPNAgent

# save cookies of WebVPN
agent = WebVPNAgent(school="swufe")
username = ""
password = ""
agent.login(username, password)

# download pdf with doi url
from paper_downloader.downloader.dss import DSSDownloader

url = ""
downloader = DSSDownloader()
pdf_url = downloader.download(url, filename=None)  # filename is None, will extract paper title automatically.

# download pdf with science-hub by doi
from paper_downloader.downloader.science_hub import SciHubDownloader

doi = ""
downloader.download(doi, filename=None)

# TODO: `SciHubDownloader` is not extract paper title correctly. It will be fixed latter.
```
