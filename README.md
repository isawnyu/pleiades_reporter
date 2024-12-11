# Pleiades Reporter

Create and disseminate reports on Pleiades developments.

## Roadmap:

- [x] Find and report on new records added to Zotero
    - [x] Use Zotero API to get records changed since a particular version and date
    - [x] Cache the last version and date checked, so each time we run we start from there
    - [x] Handle Zotero API backoff and retry after instructions
    - [x] Create formatted reports for each new Zotero record (including citation)

- [x] Create a script to run checks periodically

- [x] Create a textual UI to the check process to control it and review possible reports

- [x] Post reports via the Mastodon API to the Pleiades gazetteer Fediverse account

- [ ] Find and report on new places in Pleiades