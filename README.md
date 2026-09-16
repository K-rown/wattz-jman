# wattz-jman

Private crew page for the Wattz LED Path to Journeyman calendar: an hour or two of Mike Holt every weekday, weekends to catch up. `python3 build.py [start-date]` repacks `curriculum.json` into `index.html`. `player.html?v=VIDEO_ID` plays a Mike Holt course video from the account stream. Not for sharing outside the crew.

## Progress across devices

Done marks and "We're here" follow a first name. Two steps, once:

1. Run `progress.sql` in the Supabase SQL editor (creates `ptj_progress`, anon may read and write only that table).
2. Put the project's anon (public) key in `SYNC.key` at the top of the script in `index.html`. The URL is already there.

Until the key is set, the page saves on the phone only and says so in the footer.
