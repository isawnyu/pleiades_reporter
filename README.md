# Pleiades Reporter

Create and disseminate social media posts on Pleiades activity. 

Currently designed to post to the Pleiades account on botsinbox.net, which is a GoToSocial instance.

## Roadmap:

- [x] Find and report on new records added to Zotero
    - [x] Use Zotero API to get records changed since a particular version and date
    - [x] Cache the last version and date checked, so each time we run we start from there
    - [x] Handle Zotero API backoff and retry after instructions
    - [x] Create formatted reports for each new Zotero record (including citation)

- [x] Create a script to run checks periodically (see now `scripts/looper.py`)

- [x] Create a textual UI to the check process to control it and review possible reports

- [x] Post reports via the Mastodon API to the Pleiades gazetteer Fediverse account

- [ ] Find and report on new places in Pleiades

- [ ] Find and report new Pleiades blog posts
    - Atom feed: https://pleiades.stoa.org/news/blog/collector/atom

- [ ] Find and report new Pleiades events
    - Atom feed: https://pleiades.stoa.org/events/upcoming-events.atom

- [ ] Find and report on Pleiades data quality

- [ ] Find and report on new and newly closed Pleiades development issues

- [x] Introduce `Channel` classes, one for each dissemination channel
    - [x] GoToSocialChannel (uses the Mastodon API)
    - [ ] Facebook (since we have a legacy presence there)
        - [ ] Support only sending some reports to some channels (e.g., here blog posts is probably all we want)
    
    
